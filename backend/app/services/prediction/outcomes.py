from __future__ import annotations

from app.schemas.prediction import (
    OutcomeDistribution,
    OutcomeState,
    PredictionContext,
    SemanticPredictionAssessment,
)
from app.services.prediction.utils import contains_any


class PredictionOutcomeResolver:
    """根据明确文本信号覆盖 LLM 的结果状态判断。"""

    def resolve(
        self,
        context: PredictionContext,
        semantic: SemanticPredictionAssessment,
    ) -> OutcomeState:
        text = context.last_target_message
        explicit_stop = contains_any(
            text,
            ["不要再", "别再", "不想继续", "到此为止", "停止联系"],
        )
        refusal = contains_any(
            text,
            ["不行", "不能", "不接受", "不愿意", "拒绝", "算了"],
        )
        acceptance = contains_any(
            text,
            ["可以", "好", "行", "没问题", "同意", "愿意", "答应"],
        )
        conditional = contains_any(
            text,
            ["如果", "先把", "先发", "再看", "可以考虑", "看情况", "不保证"],
        )

        if explicit_stop or refusal:
            return "refuse"
        if conditional and acceptance:
            return "conditional_accept"
        if acceptance:
            return "accept"
        if context.target_turn_count == 0:
            return "unknown"
        return semantic.outcome_state


class OutcomeDistributionCalculator:
    """把成功评分和结果状态映射为总和为 100 的结果分布。"""

    def calculate(
        self,
        *,
        success_probability: int,
        confidence_score: int,
        outcome_state: OutcomeState,
    ) -> OutcomeDistribution:
        p = float(success_probability)
        weights = {
            "accept": max(1.0, ((p / 100.0) ** 2) * 55.0),
            "conditional_accept": max(3.0, 30.0 - abs(p - 65.0) * 0.35),
            "hesitate": max(4.0, 32.0 - abs(p - 50.0) * 0.25),
            "refuse": max(1.0, (((100.0 - p) / 100.0) ** 2) * 50.0),
            "no_response": 8.0 + (100.0 - confidence_score) / 12.0,
        }
        multipliers = {
            "accept": {"accept": 2.2, "conditional_accept": 1.2},
            "conditional_accept": {
                "conditional_accept": 2.2,
                "hesitate": 1.1,
            },
            "hesitate": {"hesitate": 2.0},
            "refuse": {"refuse": 2.5},
            "no_response": {"no_response": 2.5},
            "unknown": {},
        }[outcome_state]

        for name, multiplier in multipliers.items():
            weights[name] *= multiplier

        return OutcomeDistribution(**self.normalize(weights))

    @staticmethod
    def normalize(weights: dict[str, float]) -> dict[str, int]:
        total = sum(max(0.0, value) for value in weights.values())
        if total <= 0:
            return {
                "accept": 20,
                "conditional_accept": 20,
                "hesitate": 30,
                "refuse": 20,
                "no_response": 10,
            }

        raw = {name: value / total * 100.0 for name, value in weights.items()}
        rounded = {name: int(value) for name, value in raw.items()}
        remainder = 100 - sum(rounded.values())
        order = sorted(
            raw,
            key=lambda name: raw[name] - rounded[name],
            reverse=True,
        )
        for name in order[:remainder]:
            rounded[name] += 1
        return rounded
