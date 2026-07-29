from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.config import get_settings
from app.schemas.runtime_metrics import EvaluationExecutionMode
from app.schemas.simulation_decision import TurnDecisionResult
from app.schemas.strategy import ResponseMode, TargetResponseGuidance
from app.services.simulation_adjustment_manager import SimulationAdjustmentManager


logger = logging.getLogger(__name__)

_CRITICAL_MODES = {
    ResponseMode.DECLINE,
    ResponseMode.SET_BOUNDARY,
    ResponseMode.NO_REPLY,
    ResponseMode.END_CONVERSATION,
}
_CRITICAL_SIMULATION_ACTIONS = {
    "SET_BOUNDARY",
    "CONFRONT",
    "READ_NO_REPLY",
    "END_CONVERSATION",
}
_SUPPORTED_MODES = {"development_sync", "production_hybrid"}


@dataclass(frozen=True)
class EvaluationExecutionDecision:
    synchronous: bool
    reasons: tuple[str, ...]


def resolve_evaluation_execution_mode(
    value: str | None = None,
) -> EvaluationExecutionMode:
    settings = get_settings()
    configured = (
        value
        if value is not None
        else settings.evaluation_execution_mode
    )
    if not configured or configured.strip().lower() == "auto":
        configured = (
            "production_hybrid"
            if settings.app_env == "production"
            else "development_sync"
        )
    normalized = configured.strip().lower()
    aliases = {
        "sync": "development_sync",
        "development": "development_sync",
        "hybrid": "production_hybrid",
        "production": "production_hybrid",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in _SUPPORTED_MODES:
        logger.warning(
            "invalid_evaluation_execution_mode_falling_back_to_sync",
            extra={
                "configured_mode": configured,
                "fallback_mode": "development_sync",
            },
        )
        return "development_sync"
    return normalized  # type: ignore[return-value]


class EvaluationExecutionPolicy:
    def __init__(self, mode: str | None = None) -> None:
        self.mode = resolve_evaluation_execution_mode(mode)

    def decide(
        self,
        *,
        session_id: str,
        strategy_guidance: TargetResponseGuidance,
        decision_result: TurnDecisionResult,
        adjustment_manager: SimulationAdjustmentManager,
        user_message: str = "",
    ) -> EvaluationExecutionDecision:
        if self.mode == "development_sync":
            return EvaluationExecutionDecision(True, ("development_mode",))

        reasons: list[str] = []
        if strategy_guidance.confidence < 0.70:
            reasons.append("low_strategy_confidence")
        if strategy_guidance.recommended_mode in _CRITICAL_MODES:
            reasons.append(
                f"critical_guidance:{strategy_guidance.recommended_mode.value}"
            )
        simulation_action = decision_result.decision.response_policy.action
        if simulation_action in _CRITICAL_SIMULATION_ACTIONS:
            reasons.append(f"critical_simulation_action:{simulation_action}")

        delta_values = list(
            decision_result.decision.state_delta.model_dump().values()
        )
        if max((abs(float(value)) for value in delta_values), default=0.0) >= 0.10:
            reasons.append("large_state_delta")
        elif sum(abs(float(value)) for value in delta_values) >= 0.35:
            reasons.append("large_state_delta")

        signals = decision_result.decision.turn_analysis.behavior_signals
        events = decision_result.decision.turn_analysis.detected_events
        normalized_message = user_message.strip().lower()
        if (
            signals.pressure >= 0.70
            or signals.boundary_violation >= 0.60
            or any(
                marker in normalized_message
                for marker in (
                    "威胁",
                    "不然你就",
                    "你必须马上",
                    "滚开",
                    "废物",
                    "threat",
                    "or else",
                )
            )
            or any(
                marker in event.lower()
                for event in events
                for marker in ("threat", "pressure", "insult", "boundary")
            )
        ):
            reasons.append("user_pressure_or_threat")

        if adjustment_manager.has_repeated_issue(
            session_id,
            minimum_count=2,
        ):
            reasons.append("repeated_evaluation_issue")

        return EvaluationExecutionDecision(bool(reasons), tuple(reasons))
