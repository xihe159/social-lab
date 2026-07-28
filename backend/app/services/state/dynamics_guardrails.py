from __future__ import annotations

from app.schemas.state import StateEvaluateRequest, StateEvaluationResponse
from app.services.state.signals import ConversationSignals
from app.services.state.utils import append_unique


class DynamicsGuardrails:
    """修正对话动态增量，使明确接受、拒绝、施压等信号具有稳定影响。"""

    def apply(
        self,
        *,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
        signals: ConversationSignals,
    ) -> None:
        del request  # 当前规则不直接读取其他请求字段，保留参数便于后续扩展。
        delta = result.dynamics_update.dynamics_delta

        if signals.dynamics_polite:
            delta.atmosphere_score = max(delta.atmosphere_score, 0)
            delta.boundary_score = max(delta.boundary_score, 0)

        if signals.concrete:
            delta.clarity_score = max(delta.clarity_score, 3)
            delta.pace_score = max(delta.pace_score, 1)
            delta.progress_score = max(delta.progress_score, 1)

        if signals.responsibility:
            delta.responsiveness_score = max(
                delta.responsiveness_score,
                2,
            )
            delta.repairability_score = max(
                delta.repairability_score,
                1,
            )
            delta.progress_score = max(delta.progress_score, 1)

        if signals.apology:
            delta.repairability_score = max(
                delta.repairability_score,
                2,
            )
            delta.atmosphere_score = max(delta.atmosphere_score, 1)

        if signals.gives_space:
            delta.boundary_score = max(delta.boundary_score, 3)
            delta.pressure_level = min(delta.pressure_level, -3)
            delta.atmosphere_score = max(delta.atmosphere_score, 2)
            append_unique(
                result.positive_signals,
                "表达为对方保留了考虑、拒绝或延后回应的空间",
            )

        if signals.pressure:
            delta.pressure_level = max(delta.pressure_level, 6)
            delta.atmosphere_score = min(delta.atmosphere_score, -3)
            delta.boundary_score = min(delta.boundary_score, -4)
            delta.pace_score = min(delta.pace_score, -3)
            delta.repairability_score = min(
                delta.repairability_score,
                -1,
            )

        if signals.vague:
            delta.clarity_score = min(delta.clarity_score, -3)
            delta.pace_score = min(delta.pace_score, -2)
            delta.progress_score = min(delta.progress_score, 0)

        if signals.asks_for_detail and not signals.concrete:
            delta.clarity_score = min(delta.clarity_score, -2)
            delta.responsiveness_score = min(
                delta.responsiveness_score,
                0,
            )
            delta.progress_score = min(delta.progress_score, 0)

        if signals.conditional_acceptance:
            delta.progress_score = max(delta.progress_score, 1)
            delta.atmosphere_score = max(delta.atmosphere_score, 0)

        if signals.explicit_acceptance and not signals.explicit_refusal:
            delta.progress_score = max(delta.progress_score, 4)
            delta.atmosphere_score = max(delta.atmosphere_score, 2)
            delta.pressure_level = min(delta.pressure_level, 0)

        if signals.defensive_reply:
            delta.atmosphere_score = min(delta.atmosphere_score, -3)
            delta.pressure_level = max(delta.pressure_level, 4)
            delta.boundary_score = min(delta.boundary_score, -2)
            delta.progress_score = min(delta.progress_score, -1)
            append_unique(
                result.risk_flags,
                "目标人物已表现出压力或防御",
            )

        if signals.explicit_refusal:
            delta.progress_score = min(delta.progress_score, -5)
            delta.atmosphere_score = min(delta.atmosphere_score, -4)
            delta.pressure_level = max(delta.pressure_level, 4)
            delta.repairability_score = min(
                delta.repairability_score,
                -2,
            )
            append_unique(
                result.risk_flags,
                "目标人物已出现明确拒绝或停止推进信号",
            )
