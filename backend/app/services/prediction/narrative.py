from __future__ import annotations

from app.schemas.prediction import OutcomeState
from app.services.prediction.utils import clean_text


class PredictionNarrativeBuilder:
    """构造报告里的解释文本和默认结果描述。"""

    @staticmethod
    def build_reasoning(
        *,
        semantic_reasoning: str,
        prior: float,
        dynamics: float,
        relationship: float,
        trend: float,
        semantic_adjustment: float,
        guardrail_adjustment: float,
        confidence: str,
        probability_low: int,
        probability_high: int,
    ) -> str:
        deterministic = (
            f"场景先验 {prior:.0f}；"
            f"对话动态贡献 {dynamics:+.1f}；"
            f"关系状态贡献 {relationship:+.1f}；"
            f"多轮趋势贡献 {trend:+.1f}；"
            f"语义微调 {semantic_adjustment:+.1f}；"
            f"结果护栏修正 {guardrail_adjustment:+.1f}。"
            f"当前置信度为 {confidence}，合理预测区间为 "
            f"{probability_low}–{probability_high}。"
        )
        semantic_text = clean_text(
            semantic_reasoning,
            "",
            max_length=360,
        )
        return (
            f"{deterministic}{semantic_text}"
            if semantic_text
            else deterministic
        )[:900]

    @staticmethod
    def default_likely_outcome(score: int, outcome_state: OutcomeState) -> str:
        if outcome_state == "refuse":
            return "当前模拟更可能出现拒绝或停止推进，需要先处理压力与边界问题。"
        if outcome_state == "conditional_accept":
            return "当前模拟更可能出现附带条件的接受，需要满足对方提出的前置要求。"
        if outcome_state == "accept":
            return "当前模拟更可能继续推进，但仍需保持具体、尊重和低压力的表达。"
        if score >= 70:
            return "对方较可能接受或愿意进入具体协商。"
        if score >= 45:
            return "对方更可能犹豫、要求补充信息或提出附加条件。"
        return "对方较可能拒绝、延后回应或降低互动意愿。"
