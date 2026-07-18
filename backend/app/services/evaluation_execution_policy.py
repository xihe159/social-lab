from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from app.schemas.runtime_metrics import EvaluationExecutionMode
from app.schemas.simulation_decision import TurnDecisionResult
from app.schemas.strategy import ResponseAction, TargetResponsePolicy
from app.services.simulation_adjustment_manager import SimulationAdjustmentManager


logger = logging.getLogger(__name__)

_CRITICAL_ACTIONS = {
    ResponseAction.REFUSE,
    ResponseAction.SET_BOUNDARY,
    ResponseAction.NO_REPLY,
    ResponseAction.END_CONVERSATION,
}
_SUPPORTED_MODES = {"development_sync", "production_hybrid"}


@dataclass(frozen=True)
class EvaluationExecutionDecision:
    synchronous: bool
    reasons: tuple[str, ...]


def resolve_evaluation_execution_mode(
    value: str | None = None,
) -> EvaluationExecutionMode:
    configured = value if value is not None else os.getenv(
        "EVALUATION_EXECUTION_MODE"
    )
    if configured is None:
        app_environment = os.getenv("APP_ENV", "development").strip().lower()
        configured = (
            "production_hybrid"
            if app_environment in {"production", "prod"}
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
        strategy_policy: TargetResponsePolicy,
        decision_result: TurnDecisionResult,
        adjustment_manager: SimulationAdjustmentManager,
        user_message: str = "",
    ) -> EvaluationExecutionDecision:
        if self.mode == "development_sync":
            return EvaluationExecutionDecision(True, ("development_mode",))

        reasons: list[str] = []
        if strategy_policy.confidence < 0.70:
            reasons.append("low_strategy_confidence")
        if strategy_policy.action in _CRITICAL_ACTIONS:
            reasons.append(f"critical_action:{strategy_policy.action.value}")

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
