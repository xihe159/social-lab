from __future__ import annotations

from app.schemas.state import StateEvaluateRequest, StateEvaluationResponse
from app.services.state.signals import ConversationSignals
from app.services.state.utils import append_unique, clamp


class RelationshipGuardrails:
    """修正关系状态增量，防止模型忽略明显的礼貌、责任或施压信号。"""

    def apply(
        self,
        *,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
        signals: ConversationSignals,
    ) -> None:
        delta = result.state_delta

        if signals.relationship_polite:
            delta.respect = max(delta.respect, 0)
            append_unique(
                result.positive_signals,
                "表达中包含礼貌或尊重性措辞",
            )

        if signals.concrete:
            delta.trust = max(delta.trust, 1)
            if request.scenario in {"advisor", "work"}:
                delta.respect = max(delta.respect, 1)
            append_unique(
                result.positive_signals,
                "提供了较具体的计划、时间或处理方案",
            )

        if signals.responsibility and request.scenario in {"advisor", "work"}:
            delta.trust = max(delta.trust, 1)
            delta.respect = max(delta.respect, 1)
            append_unique(
                result.positive_signals,
                "表达中体现了责任承担或主动推进",
            )

        if signals.pressure:
            delta.trust = min(delta.trust, -1)
            delta.respect = min(delta.respect, -1)
            delta.affinity = min(delta.affinity, -1)
            delta.emotional = min(delta.emotional, -1)
            append_unique(
                result.negative_signals,
                "表达可能让对方感到被催促或被迫表态",
            )
            append_unique(
                result.risk_flags,
                "表达中存在催促、施压或命令感",
            )

        if signals.vague:
            delta.trust = min(delta.trust, 0)
            delta.emotional = min(delta.emotional, 0)
            append_unique(
                result.negative_signals,
                "关键信息不足，可能增加对方判断成本",
            )
            append_unique(
                result.risk_flags,
                "表达信息不足或请求不够具体",
            )

        delta.authority = clamp(delta.authority, -2, 2)
