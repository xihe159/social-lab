from __future__ import annotations

from dataclasses import dataclass
from statistics import pstdev

from app.schemas.dynamics import ConversationDynamicsSnapshot
from app.schemas.prediction import (
    OutcomeState,
    PredictionContext,
    SemanticPredictionAssessment,
)
from app.services.prediction.utils import clamp_int


@dataclass(frozen=True, slots=True)
class PredictionConfidenceAssessment:
    confidence_score: int
    confidence: str
    evidence_sufficiency: str
    volatility: float
    uncertainty_width: int
    probability_low: int
    probability_high: int


class PredictionConfidenceCalculator:
    """计算证据充分度、置信度、波动率和预测区间。"""

    def assess(
        self,
        *,
        context: PredictionContext,
        semantic: SemanticPredictionAssessment,
        outcome_state: OutcomeState,
        final_score: int,
    ) -> PredictionConfidenceAssessment:
        evidence_sufficiency = self.evidence_sufficiency(context)
        confidence_score = self.confidence_score(
            context=context,
            semantic=semantic,
            outcome_state=outcome_state,
        )
        confidence = self.confidence_label(confidence_score)
        volatility = self.volatility(context.dynamics_history)
        uncertainty_width = self.uncertainty_width(
            confidence_score=confidence_score,
            evidence_sufficiency=evidence_sufficiency,
            volatility=volatility,
        )
        return PredictionConfidenceAssessment(
            confidence_score=confidence_score,
            confidence=confidence,
            evidence_sufficiency=evidence_sufficiency,
            volatility=volatility,
            uncertainty_width=uncertainty_width,
            probability_low=clamp_int(final_score - uncertainty_width, 0, 100),
            probability_high=clamp_int(final_score + uncertainty_width, 0, 100),
        )

    def confidence_score(
        self,
        *,
        context: PredictionContext,
        semantic: SemanticPredictionAssessment,
        outcome_state: OutcomeState,
    ) -> int:
        score = 10.0
        score += min(context.user_turn_count, 3) * 8
        score += min(context.target_turn_count, 3) * 10
        score += 15 if context.current_dynamics is not None else 0
        score += min(len(context.dynamics_history), 4) * 4
        score += semantic.evidence_strength * 15
        score += 5 if context.goal.strip() else 0
        score += 3 if context.outcome.strip() else 0
        if outcome_state == "unknown":
            score -= 8
        if context.target_turn_count == 0:
            score -= 10

        sufficiency = self.evidence_sufficiency(context)
        if sufficiency == "insufficient":
            score = min(score, 40.0)
        elif sufficiency == "partial":
            score = min(score, 70.0)

        return clamp_int(round(score), 0, 95)

    @staticmethod
    def evidence_sufficiency(context: PredictionContext) -> str:
        if (
            context.user_turn_count < 1
            or context.target_turn_count < 1
            or context.current_dynamics is None
        ):
            return "insufficient"
        if (
            context.user_turn_count < 2
            or context.target_turn_count < 2
            or len(context.dynamics_history) < 2
        ):
            return "partial"
        return "sufficient"

    @staticmethod
    def confidence_label(score: int) -> str:
        if score >= 75:
            return "high"
        if score >= 45:
            return "medium"
        return "low"

    @staticmethod
    def uncertainty_width(
        *,
        confidence_score: int,
        evidence_sufficiency: str,
        volatility: float,
    ) -> int:
        width = 26.0 - 0.18 * confidence_score
        width += min(8.0, volatility / 4.0)
        if evidence_sufficiency == "insufficient":
            width += 4.0
        elif evidence_sufficiency == "partial":
            width += 2.0
        return clamp_int(round(width), 8, 30)

    @staticmethod
    def volatility(history: list[ConversationDynamicsSnapshot]) -> float:
        if len(history) < 3:
            return 0.0
        recent = history[-5:]
        series = [
            [item.atmosphere_score for item in recent],
            [item.pressure_level for item in recent],
            [item.progress_score for item in recent],
            [item.pace_score for item in recent],
        ]
        return sum(pstdev(values) for values in series) / len(series)
