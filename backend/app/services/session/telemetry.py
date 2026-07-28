# social-lab/backend/app/services/session/telemetry.py
# 集中处理日志
# 2026/07/28

from __future__ import annotations

import logging
import time
from typing import Any

from app.services.session.context import SessionExecutionContext

logger = logging.getLogger(__name__)


def elapsed_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)


def safe_dump(value: Any) -> Any:
    if value is None:
        return None
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump()
    return value


class SessionTelemetry:
    """集中处理编排日志，避免业务 Stage 被大量日志字段淹没。"""

    def session_started(self, execution_context: SessionExecutionContext) -> None:
        request = execution_context.request
        logger.info(
            "session_message_started",
            extra={
                "trace_id": execution_context.trace_id,
                "scenario": request.scenario,
                "message_count": len(request.messages),
                "has_memory": request.memory is not None,
                "has_current_dynamics": request.current_dynamics is not None,
                "user_message_length": len(request.user_message),
                "goal_length": len(request.goal),
                "outcome_length": len(request.outcome or ""),
                "simulation_agent_version": execution_context.simulation_agent_version,
            },
        )

    def session_finished(
        self,
        execution_context: SessionExecutionContext,
        *,
        status: str,
    ) -> None:
        response = execution_context.require_response()
        logger.info(
            "session_message_finished",
            extra={
                "trace_id": execution_context.trace_id,
                "status": status,
                "duration_ms": elapsed_ms(execution_context.started_at),
                "scenario": execution_context.request.scenario,
                "final_risk_flags": response.simulation.risk_flags,
                "reply_length": len(response.target_message.content),
                "has_updated_memory": response.updated_memory is not None,
                "has_dynamics_update": response.dynamics_update is not None,
                "simulation_agent_version": execution_context.simulation_agent_version,
            },
        )

    def agent_started(
        self,
        execution_context: SessionExecutionContext,
        *,
        agent: str,
        **fields: Any,
    ) -> float:
        started_at = time.perf_counter()
        logger.info(
            "agent_started",
            extra={
                "trace_id": execution_context.trace_id,
                "agent": agent,
                "scenario": execution_context.request.scenario,
                **fields,
            },
        )
        return started_at

    def agent_finished(
        self,
        execution_context: SessionExecutionContext,
        *,
        agent: str,
        started_at: float,
        **fields: Any,
    ) -> None:
        logger.info(
            "agent_finished",
            extra={
                "trace_id": execution_context.trace_id,
                "agent": agent,
                "duration_ms": elapsed_ms(started_at),
                **fields,
            },
        )

    def agent_fallback(
        self,
        execution_context: SessionExecutionContext,
        *,
        agent: str,
        started_at: float,
        fallback: str,
        error_kind: str,
    ) -> None:
        logger.exception(
            "agent_failed_fallback",
            extra={
                "trace_id": execution_context.trace_id,
                "agent": agent,
                "duration_ms": elapsed_ms(started_at),
                "fallback": fallback,
                "error_kind": error_kind,
            },
        )

    def simulation_fields(self, response: Any) -> dict[str, Any]:
        evaluation_meta = getattr(response, "evaluation_meta", None)
        runtime_meta = getattr(response, "runtime_meta", None)
        strategy_meta = getattr(response, "strategy_meta", None)

        final_verdict = getattr(evaluation_meta, "final_verdict", None)
        final_failure = getattr(
            evaluation_meta,
            "final_failure_attribution",
            None,
        )
        feedback_action = getattr(evaluation_meta, "feedback_action", None)

        return {
            "reply_length": len(response.target_message.content),
            "attitude": response.simulation.attitude,
            "emotion": response.simulation.emotion,
            "perceived_user_tone": response.simulation.perceived_user_tone,
            "state_delta": safe_dump(response.simulation.state_delta),
            "risk_flags": list(response.simulation.risk_flags),
            "updated_state": safe_dump(response.updated_state),
            "simulation_evaluated": bool(
                evaluation_meta and getattr(evaluation_meta, "evaluated", False)
            ),
            "initial_evaluation_score": getattr(
                evaluation_meta,
                "initial_score",
                None,
            ),
            "final_evaluation_score": getattr(
                evaluation_meta,
                "final_score",
                None,
            ),
            "evaluation_score_delta": getattr(
                evaluation_meta,
                "score_delta",
                None,
            ),
            "evaluation_verdict": getattr(final_verdict, "value", None),
            "failure_attribution": getattr(final_failure, "value", None),
            "feedback_action": getattr(feedback_action, "value", "none"),
            "feedback_retry_count": getattr(
                evaluation_meta,
                "retry_count",
                0,
            ),
            "evaluation_agent_failed": bool(
                evaluation_meta
                and getattr(evaluation_meta, "evaluator_failed", False)
            ),
            "final_evaluation_failed": bool(
                evaluation_meta
                and getattr(evaluation_meta, "final_evaluator_failed", False)
            ),
            "strategy_policy_id": getattr(strategy_meta, "policy_id", None),
            "strategy_action": getattr(strategy_meta, "strategy_action", None),
            "strategy_confidence": getattr(strategy_meta, "confidence", None),
            "decision_fallback_used": bool(
                runtime_meta
                and getattr(runtime_meta, "decision_fallback_used", False)
            ),
            "strategy_fallback_used": bool(
                runtime_meta
                and getattr(runtime_meta, "strategy_fallback_used", False)
            ),
            "generator_retry_count": getattr(
                runtime_meta,
                "generator_retry_count",
                0,
            ),
            "generator_fallback_used": bool(
                runtime_meta
                and getattr(runtime_meta, "generator_fallback_used", False)
            ),
            "evaluation_call_count": getattr(
                runtime_meta,
                "evaluation_call_count",
                0,
            ),
            "strategy_replan_count": getattr(
                runtime_meta,
                "strategy_replan_count",
                0,
            ),
            "simulation_revision_count": getattr(
                runtime_meta,
                "simulation_revision_count",
                0,
            ),
            "rejected_candidate_discarded": bool(
                runtime_meta
                and getattr(runtime_meta, "rejected_candidate_discarded", False)
            ),
        }
