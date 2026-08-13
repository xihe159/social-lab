from __future__ import annotations

from app.agents.simulation.prompts import (
    SIMULATION_DECISION_PROMPT_VERSION,
    SIMULATION_DECISION_SYSTEM_PROMPT,
    build_simulation_decision_prompt,
)
from app.llm.client import generate_structured
from app.prompts.simulation import SIMULATION_DECISION_PROMPT
from app.schemas.simulation_guidance import (
    SimulationDecisionOutput,
    SimulationDecisionRequest,
)


_EXTREME_ACTIONS = {"READ_NO_REPLY", "END_CONVERSATION"}


class SimulationDecisionEngine:
    """Own the target person's final behavior after considering Strategy guidance."""

    prompt_version = SIMULATION_DECISION_PROMPT_VERSION

    async def run(
        self,
        request: SimulationDecisionRequest,
    ) -> SimulationDecisionOutput:
        result = await generate_structured(
            system_prompt=SIMULATION_DECISION_SYSTEM_PROMPT,
            user_prompt=build_simulation_decision_prompt(request),
            output_model=SimulationDecisionOutput,
            temperature=SIMULATION_DECISION_PROMPT.temperature,
        )
        return self.post_process(result=result, request=request)

    def post_process(
        self,
        *,
        result: SimulationDecisionOutput,
        request: SimulationDecisionRequest,
    ) -> SimulationDecisionOutput:
        policy = result.response_policy
        policy.tone = policy.tone.strip() or "neutral"
        policy.content_goals = _clean_list(policy.content_goals, limit=5)
        policy.must_avoid = _clean_list(policy.must_avoid, limit=5)
        if not policy.content_goals:
            policy.content_goals = ["回应用户当前表达"]

        if policy.action in _EXTREME_ACTIONS:
            evidence_score = _extreme_action_evidence_score(request)
            threshold = 0.60 if policy.action == "READ_NO_REPLY" else 0.70
            if evidence_score < threshold:
                policy.action = (
                    "DEFER_REPLY"
                    if evidence_score >= 0.35
                    else "SET_BOUNDARY"
                )
                result.guidance_followed = False
                result.guidance_deviation_reason = (
                    "极端动作缺少足够的 Persona 与当前回合组合证据，"
                    "已降级为可解释的延后或边界回应。"
                )
                result.confidence = min(result.confidence, 0.65)
        return result


def _extreme_action_evidence_score(
    request: SimulationDecisionRequest,
) -> float:
    guidance = request.strategy_guidance
    analysis = request.turn_state_analysis
    score = 0.0

    if any(
        not ref.startswith("persona_snapshot:")
        for ref in guidance.persona_evidence_refs
    ):
        score += 0.35
    if (
        analysis.behavior_signals.pressure >= 0.60
        or analysis.behavior_signals.boundary_violation >= 0.55
        or any(
            marker in " ".join(
                [*analysis.detected_events, *analysis.risk_flags]
            ).lower()
            for marker in (
                "pressure",
                "boundary",
                "insult",
                "施压",
                "越界",
                "侮辱",
            )
        )
    ):
        score += 0.35
    if guidance.memory_evidence_refs:
        score += 0.20
    if any(
        marker in " ".join(analysis.detected_events).lower()
        for marker in ("repeated", "连续", "反复")
    ):
        score += 0.10
    return round(min(1.0, score), 3)


def _clean_list(values: list[str], *, limit: int) -> list[str]:
    result: list[str] = []
    for value in values:
        item = str(value).strip()
        if item and item not in result:
            result.append(item[:160])
    return result[:limit]
