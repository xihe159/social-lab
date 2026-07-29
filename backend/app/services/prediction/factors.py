from __future__ import annotations

from app.schemas.prediction import (
    PredictionContext,
    PredictionInfluenceFactor,
    SemanticPredictionAssessment,
)
from app.services.prediction.calibration import (
    DEFAULT_CALIBRATION,
    PredictionCalibration,
)
from app.services.prediction.utils import (
    clean_text,
    clamp_float,
    direction,
    importance,
    latest_turns,
)


class PredictionFactorFactory:
    """只负责构造报告中的影响因素，不负责计算最终分数。"""

    def __init__(
        self,
        calibration: PredictionCalibration = DEFAULT_CALIBRATION,
    ) -> None:
        self.calibration = calibration

    def scenario_prior_factors(
        self,
        context: PredictionContext,
        prior: float,
    ) -> list[PredictionInfluenceFactor]:
        contribution = prior - 50.0
        if abs(contribution) < 0.5:
            return []

        return [
            PredictionInfluenceFactor(
                factor_name=self.calibration.scenario_labels[context.scenario],
                direction=direction(contribution),
                importance=importance(contribution),
                contribution=round(contribution, 2),
                source="scenario_prior",
                metric_name="scenario_prior",
                metric_value=prior,
                evidence_turns=[],
                evidence_quote=f"当前场景：{context.scenario}",
                explanation=(
                    "该场景通常需要更明确的责任、证据或前置条件，因此采用保守起点。"
                    if contribution < 0
                    else "该场景使用中性起点，主要由当前对话证据决定后续评分。"
                ),
            )
        ]

    def metric_factor(
        self,
        *,
        metric_name: str,
        metric_value: float,
        contribution: float,
        source: str,
        evidence_turns: list[int],
        evidence_quote: str,
    ) -> PredictionInfluenceFactor:
        label = self.calibration.metric_labels[metric_name]
        if contribution > 0:
            explanation = f"{label}处于有利水平，为目标推进提供正向支持。"
        elif contribution < 0:
            explanation = (
                f"{label}处于不利水平，增加了对方犹豫、附加条件或拒绝的可能性。"
            )
        else:
            explanation = f"{label}目前对结果影响有限。"

        return PredictionInfluenceFactor(
            factor_name=label,
            direction=direction(contribution),
            importance=importance(contribution),
            contribution=round(contribution, 2),
            source=source,
            metric_name=metric_name,
            metric_value=round(metric_value, 2),
            evidence_turns=evidence_turns,
            evidence_quote=clean_text(
                evidence_quote,
                f"{label}当前值 {metric_value:.0f}",
                max_length=180,
            ),
            explanation=explanation,
        )

    def semantic_factors(
        self,
        *,
        context: PredictionContext,
        semantic: SemanticPredictionAssessment,
        semantic_adjustment: float,
    ) -> list[PredictionInfluenceFactor]:
        raw_weights: list[float] = []
        for factor in semantic.semantic_factors:
            sign = {
                "positive": 1.0,
                "negative": -1.0,
                "mixed": 0.0,
            }[factor.direction]
            raw_weights.append(sign * factor.importance)

        denominator = sum(abs(value) for value in raw_weights)
        factors: list[PredictionInfluenceFactor] = []

        if denominator <= 0 or abs(semantic_adjustment) < 0.5:
            for factor in semantic.semantic_factors:
                factors.append(
                    PredictionInfluenceFactor(
                        factor_name=factor.factor_name,
                        direction=factor.direction,
                        importance=factor.importance,
                        contribution=0.0,
                        source="semantic",
                        metric_name=None,
                        metric_value=None,
                        evidence_turns=factor.evidence_turns,
                        evidence_quote=factor.evidence_quote,
                        explanation=factor.explanation,
                    )
                )
            return factors

        signed_sum = sum(raw_weights)
        for index, factor in enumerate(semantic.semantic_factors):
            if abs(signed_sum) >= 1:
                share = raw_weights[index] / signed_sum
            else:
                share = abs(raw_weights[index]) / denominator

            contribution = clamp_float(
                semantic_adjustment * share,
                -float(self.calibration.semantic_adjustment_limit),
                float(self.calibration.semantic_adjustment_limit),
            )
            factors.append(
                PredictionInfluenceFactor(
                    factor_name=factor.factor_name,
                    direction=(
                        direction(contribution)
                        if abs(contribution) >= 0.25
                        else factor.direction
                    ),
                    importance=factor.importance,
                    contribution=round(contribution, 2),
                    source="semantic",
                    metric_name=None,
                    metric_value=None,
                    evidence_turns=factor.evidence_turns,
                    evidence_quote=factor.evidence_quote,
                    explanation=factor.explanation,
                )
            )
        return factors

    def guardrail_factor(
        self,
        *,
        context: PredictionContext,
        adjustment: float,
        reason: str,
    ) -> PredictionInfluenceFactor:
        return PredictionInfluenceFactor(
            factor_name="明确结果信号",
            direction=direction(adjustment),
            importance=5,
            contribution=round(adjustment, 2),
            source="guardrail",
            metric_name=None,
            metric_value=None,
            evidence_turns=latest_turns(context),
            evidence_quote=clean_text(
                context.last_target_message,
                "目标人物当前没有可引用回复。",
                max_length=180,
            ),
            explanation=reason,
        )
