from __future__ import annotations

import re

from app.agents.simulation.prompts import (
    CONSISTENCY_EVALUATOR_SYSTEM_PROMPT,
    build_consistency_evaluation_prompt,
)
from app.llm.client import generate_structured
from app.schemas.consistency_evaluation import (
    ConsistencyEvaluationInput,
    ConsistencyEvaluationOutput,
    ConsistencyIssue,
    EvaluatorTriggerResult,
)
from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.simulation_decision import TurnDecisionResult
from app.schemas.simulation_generation import GeneratedResponse
from app.schemas.simulation_state import SimulationState


CONSISTENCY_THRESHOLD = 0.75
LOW_DECISION_CONFIDENCE = 0.55
HIGH_CONFLICT = 0.65
MAJOR_RELATIONSHIP_DELTA = 0.12
_EMOJI_PATTERN = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")


class ConsistencyEvaluator:
    """Conditionally score a generated response without replaying the persona."""

    def should_run(
        self,
        *,
        persona: PersonaModelV2,
        previous_state: SimulationState,
        decision_result: TurnDecisionResult,
        generated: GeneratedResponse,
        relevant_evidence: list[str],
    ) -> EvaluatorTriggerResult:
        reasons: list[str] = []
        decision = decision_result.decision
        updated = decision_result.updated_state

        if decision.confidence < LOW_DECISION_CONFIDENCE:
            reasons.append("low_decision_confidence")

        relationship_fields = (
            "trust", "respect", "warmth", "patience",
            "psychological_safety", "willingness_to_engage",
        )
        if any(
            abs(getattr(decision.state_delta, field)) >= MAJOR_RELATIONSHIP_DELTA
            for field in relationship_fields
        ):
            reasons.append("major_relationship_change")

        if updated.conversation_state.conflict_level >= HIGH_CONFLICT:
            reasons.append("high_conflict")

        action = decision.response_policy.action
        if action in {"CONFRONT", "END_CONVERSATION"} and updated.conversation_state.conflict_level < 0.45:
            reasons.append("potential_overreaction")
        if relevant_evidence and action in {"CONFRONT", "SET_BOUNDARY", "END_CONVERSATION"}:
            reasons.append("evidence_sensitive_action")

        reasons.extend(
            self._style_risks(
                persona=persona,
                generated=generated,
                action=action,
            )
        )
        reasons = list(dict.fromkeys(reasons))
        return EvaluatorTriggerResult(triggered=bool(reasons), reasons=reasons)

    async def evaluate(
        self,
        request: ConsistencyEvaluationInput,
    ) -> ConsistencyEvaluationOutput:
        result = await generate_structured(
            system_prompt=CONSISTENCY_EVALUATOR_SYSTEM_PROMPT,
            user_prompt=build_consistency_evaluation_prompt(request),
            output_model=ConsistencyEvaluationOutput,
            temperature=0.1,
        )
        return self.post_process(result)

    def post_process(
        self,
        result: ConsistencyEvaluationOutput,
    ) -> ConsistencyEvaluationOutput:
        cleaned: list[ConsistencyIssue] = []
        for issue in result.issues:
            message = issue.message.strip()
            if not message:
                continue
            cleaned.append(
                ConsistencyIssue(
                    dimension=issue.dimension,
                    severity=issue.severity,
                    message=message[:240],
                    retry_instruction=issue.retry_instruction.strip()[:240],
                )
            )
        result.issues = cleaned[:8]

        dimension, minimum = result.scores.minimum()
        has_serious_issue = any(
            issue.severity in {"high", "critical"} for issue in result.issues
        )
        if minimum < CONSISTENCY_THRESHOLD or has_serious_issue:
            result.passed = False

        if not result.passed and not result.issues:
            result.issues = [
                ConsistencyIssue(
                    dimension=dimension,  # type: ignore[arg-type]
                    severity="medium",
                    message=f"{dimension} 低于一致性阈值。",
                    retry_instruction="保持 Response Action 不变，修正该维度的语言表达。",
                )
            ]
        return result

    @staticmethod
    def _style_risks(
        *,
        persona: PersonaModelV2,
        generated: GeneratedResponse,
        action: str,
    ) -> list[str]:
        if action in {"DEFER_REPLY", "READ_NO_REPLY"}:
            return []
        text = generated.response_text.strip()
        style = persona.communication_style
        reasons: list[str] = []
        if style.average_reply_length == "short" and len(text) > 90:
            reasons.append("obvious_reply_length_mismatch")
        if style.average_reply_length == "long" and action == "REPLY_NORMAL" and len(text) < 10:
            reasons.append("obvious_reply_length_mismatch")
        emoji_count = len(_EMOJI_PATTERN.findall(text))
        if style.emoji_frequency <= 0.05 and emoji_count >= 2:
            reasons.append("obvious_emoji_mismatch")
        if style.formality >= 0.75 and any(marker in text for marker in ("哈哈", "随便啦", "亲亲", "～", "~")):
            reasons.append("obvious_formality_mismatch")
        return reasons
