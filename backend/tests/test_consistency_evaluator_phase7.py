from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import AsyncMock

from pydantic import ValidationError


llm_client_stub = types.ModuleType("app.llm.client")
llm_client_stub.generate_structured = AsyncMock()
sys.modules.setdefault("app.llm.client", llm_client_stub)

from app.agents.simulation.consistency_evaluator import ConsistencyEvaluator
from app.agents.simulation.prompts import CONSISTENCY_EVALUATOR_SYSTEM_PROMPT
from app.schemas.common import RelationshipState
from app.schemas.consistency_evaluation import (
    ConsistencyEvaluationOutput,
    ConsistencyIssue,
    ConsistencyScores,
)
from app.schemas.persona import Persona
from app.schemas.simulation_decision import (
    BehaviorSignals,
    ResponsePolicy,
    SimulationStateDelta,
    TurnAnalysis,
    TurnDecisionOutput,
    TurnDecisionResult,
)
from app.schemas.simulation_generation import GeneratedResponse
from app.schemas.simulation_state import ConversationState, SimulationState
from app.services.persona_v2_adapter import compile_legacy_persona


def persona_v2():
    legacy = Persona(
        title="直接、简洁的导师",
        style="直接、简洁、正式",
        speed="正常",
        focus="材料完整度",
        risk="重复拖延",
        strategy="提供完整材料",
        state=RelationshipState(
            trust=60,
            respect=70,
            familiarity=45,
            affinity=50,
            authority=80,
            emotional=10,
        ),
    )
    result = compile_legacy_persona(
        legacy,
        persona_id="persona_phase7",
        role="导师",
        relation="师生关系",
        scenario="advisor",
    )
    result.communication_style.average_reply_length = "short"
    result.communication_style.formality = 0.85
    result.communication_style.emoji_frequency = 0.0
    return result


def decision_result(
    *,
    confidence: float = 0.85,
    action: str = "REPLY_NORMAL",
    trust_delta: float = 0.02,
    conflict: float = 0.2,
) -> TurnDecisionResult:
    delta = SimulationStateDelta(
        trust=trust_delta,
        respect=0,
        warmth=0,
        patience=0,
        psychological_safety=0,
        willingness_to_engage=0,
        irritation=0,
        hurt=0,
        anxiety=0,
        defensiveness=0,
        fatigue=0,
        conflict_level=0,
        topic_resolution=0,
        boundary_pressure=0,
    )
    policy = ResponsePolicy(
        action=action,
        content_goals=["回应当前请求"],
        tone="直接",
        reply_length="medium",
        must_avoid=[],
    )
    return TurnDecisionResult(
        decision=TurnDecisionOutput(
            turn_analysis=TurnAnalysis(
                intent="request",
                behavior_signals=BehaviorSignals(
                    politeness=0.8,
                    clarity=0.8,
                    accountability=0.7,
                    pressure=0.1,
                    blame=0,
                    vulnerability=0.2,
                    boundary_violation=0,
                    honesty_signal=0.8,
                ),
                detected_events=[],
            ),
            state_delta=delta,
            response_policy=policy,
            confidence=confidence,
        ),
        updated_state=SimulationState(
            session_id="session_phase7",
            persona_id="persona_phase7",
            conversation_state=ConversationState(conflict_level=conflict),
        ),
    )


def passing_evaluation() -> ConsistencyEvaluationOutput:
    return ConsistencyEvaluationOutput(
        **{
            "pass": True,
            "scores": {
                "persona_consistency": 0.9,
                "dyadic_consistency": 0.9,
                "style_consistency": 0.9,
                "emotional_continuity": 0.9,
                "evidence_consistency": 0.9,
                "reaction_proportionality": 0.9,
            },
            "issues": [],
        }
    )


class EvaluatorTriggerPhase7Tests(unittest.TestCase):
    def test_normal_response_does_not_trigger_extra_model_call(self) -> None:
        evaluator = ConsistencyEvaluator()
        state = SimulationState(session_id="session_phase7", persona_id="persona_phase7")

        trigger = evaluator.should_run(
            persona=persona_v2(),
            previous_state=state,
            decision_result=decision_result(),
            generated=GeneratedResponse(
                response_text="可以，把材料发来。",
                response_action="REPLY_NORMAL",
            ),
            relevant_evidence=[],
        )

        self.assertFalse(trigger.triggered)
        self.assertEqual(trigger.reasons, [])

    def test_obvious_style_mismatch_is_detected(self) -> None:
        evaluator = ConsistencyEvaluator()
        state = SimulationState(session_id="session_phase7", persona_id="persona_phase7")
        text = "哈哈～当然没问题呀😂😂" + "我会特别详细地慢慢和你聊这件事情。" * 6

        trigger = evaluator.should_run(
            persona=persona_v2(),
            previous_state=state,
            decision_result=decision_result(),
            generated=GeneratedResponse(
                response_text=text,
                response_action="REPLY_NORMAL",
            ),
            relevant_evidence=[],
        )

        self.assertTrue(trigger.triggered)
        self.assertIn("obvious_reply_length_mismatch", trigger.reasons)
        self.assertIn("obvious_emoji_mismatch", trigger.reasons)
        self.assertIn("obvious_formality_mismatch", trigger.reasons)

    def test_low_confidence_major_change_and_high_conflict_trigger(self) -> None:
        evaluator = ConsistencyEvaluator()
        state = SimulationState(session_id="session_phase7", persona_id="persona_phase7")

        trigger = evaluator.should_run(
            persona=persona_v2(),
            previous_state=state,
            decision_result=decision_result(
                confidence=0.4,
                trust_delta=-0.15,
                conflict=0.8,
            ),
            generated=GeneratedResponse(
                response_text="这件事到此为止。",
                response_action="REPLY_NORMAL",
            ),
            relevant_evidence=[],
        )

        self.assertIn("low_decision_confidence", trigger.reasons)
        self.assertIn("major_relationship_change", trigger.reasons)
        self.assertIn("high_conflict", trigger.reasons)


class EvaluatorScoringPhase7Tests(unittest.TestCase):
    def test_score_outside_unit_range_is_rejected(self) -> None:
        payload = passing_evaluation().model_dump(by_alias=True)
        payload["scores"]["style_consistency"] = 1.1
        with self.assertRaises(ValidationError):
            ConsistencyEvaluationOutput.model_validate(payload)

    def test_score_below_threshold_forces_failure_and_retry_feedback(self) -> None:
        result = passing_evaluation()
        result.scores.style_consistency = 0.4
        result.issues = [
            ConsistencyIssue(
                dimension="style_consistency",
                severity="high",
                message="回复明显比人物历史风格更长、更随意。",
                retry_instruction="缩短回复并保持正式表达。",
            )
        ]

        processed = ConsistencyEvaluator().post_process(result)

        self.assertFalse(processed.passed)
        self.assertEqual(
            processed.retry_feedback(),
            ["style_consistency: 缩短回复并保持正式表达。"],
        )

    def test_prompt_forbids_roleplay_and_unrequested_response_generation(self) -> None:
        self.assertIn("只检查", CONSISTENCY_EVALUATOR_SYSTEM_PROMPT)
        self.assertIn("不重新扮演人物", CONSISTENCY_EVALUATOR_SYSTEM_PROMPT)
        self.assertIn("不生成新的目标人物回复", CONSISTENCY_EVALUATOR_SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
