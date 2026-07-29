from __future__ import annotations

from app.schemas.dynamics import ConversationDynamicsSnapshot
from app.schemas.prediction import (
    OutcomeDistribution,
    OutcomeState,
    PredictionCalculationTrace,
    PredictionContext,
    PredictionInfluenceFactor,
    PredictionResult,
    SemanticPredictionAssessment,
)
from app.services.prediction.calibration import (
    DEFAULT_CALIBRATION,
    PredictionCalibration,
)
from app.services.prediction.confidence import PredictionConfidenceCalculator
from app.services.prediction.factors import PredictionFactorFactory
from app.services.prediction.guardrails import GuardrailResult, PredictionGuardrails
from app.services.prediction.narrative import PredictionNarrativeBuilder
from app.services.prediction.outcomes import (
    OutcomeDistributionCalculator,
    PredictionOutcomeResolver,
)
from app.services.prediction.scoring import PredictionScorer
from app.services.prediction.utils import (
    clean_text,
    clamp_float,
    clamp_int,
    contains_any,
    direction,
    importance,
    latest_turns,
)


class PredictionCalculator:
    """
    可解释、可测试、可校准的模拟成功评分计算器。

    此类现在只负责编排纯计算组件。公开入口 calculate() 与旧版保持一致。
    """

    def __init__(
        self,
        calibration: PredictionCalibration = DEFAULT_CALIBRATION,
        *,
        factor_factory: PredictionFactorFactory | None = None,
        scorer: PredictionScorer | None = None,
        outcome_resolver: PredictionOutcomeResolver | None = None,
        guardrails: PredictionGuardrails | None = None,
        confidence_calculator: PredictionConfidenceCalculator | None = None,
        distribution_calculator: OutcomeDistributionCalculator | None = None,
        narrative_builder: PredictionNarrativeBuilder | None = None,
    ) -> None:
        self.calibration = calibration
        self.factor_factory = factor_factory or PredictionFactorFactory(calibration)
        self.scorer = scorer or PredictionScorer(calibration, self.factor_factory)
        self.outcome_resolver = outcome_resolver or PredictionOutcomeResolver()
        self.guardrails = guardrails or PredictionGuardrails()
        self.confidence_calculator = (
            confidence_calculator or PredictionConfidenceCalculator()
        )
        self.distribution_calculator = (
            distribution_calculator or OutcomeDistributionCalculator()
        )
        self.narrative_builder = narrative_builder or PredictionNarrativeBuilder()

    def calculate(
        self,
        *,
        context: PredictionContext,
        semantic: SemanticPredictionAssessment,
    ) -> PredictionResult:
        breakdown = self.scorer.score(context)
        semantic_adjustment = float(
            clamp_int(
                semantic.semantic_adjustment,
                -self.calibration.semantic_adjustment_limit,
                self.calibration.semantic_adjustment_limit,
            )
        )
        semantic_factors = self.factor_factory.semantic_factors(
            context=context,
            semantic=semantic,
            semantic_adjustment=semantic_adjustment,
        )

        pre_guardrail = clamp_float(
            breakdown.deterministic_score + semantic_adjustment,
            0.0,
            100.0,
        )
        resolved_outcome = self.outcome_resolver.resolve(context, semantic)
        guardrail = self.guardrails.apply(
            score=pre_guardrail,
            context=context,
            outcome_state=resolved_outcome,
        )
        final_score = clamp_int(round(guardrail.score), 0, 100)
        guardrail_adjustment = final_score - pre_guardrail

        confidence = self.confidence_calculator.assess(
            context=context,
            semantic=semantic,
            outcome_state=resolved_outcome,
            final_score=final_score,
        )

        factors = [*breakdown.factors, *semantic_factors]
        if abs(guardrail_adjustment) >= 0.5:
            factors.append(
                self.factor_factory.guardrail_factor(
                    context=context,
                    adjustment=guardrail_adjustment,
                    reason=guardrail.reason or "确定性结果护栏修正",
                )
            )
        factors.sort(
            key=lambda item: (abs(item.contribution), item.importance),
            reverse=True,
        )
        factors = factors[: self.calibration.max_influence_factors]

        outcome_distribution = self.distribution_calculator.calculate(
            success_probability=final_score,
            confidence_score=confidence.confidence_score,
            outcome_state=resolved_outcome,
        )
        reasoning = self.narrative_builder.build_reasoning(
            semantic_reasoning=semantic.probability_reasoning,
            prior=breakdown.scenario_prior,
            dynamics=breakdown.dynamics_contribution,
            relationship=breakdown.relationship_contribution,
            trend=breakdown.trend_contribution,
            semantic_adjustment=semantic_adjustment,
            guardrail_adjustment=guardrail_adjustment,
            confidence=confidence.confidence,
            probability_low=confidence.probability_low,
            probability_high=confidence.probability_high,
        )
        likely_outcome = clean_text(
            semantic.likely_outcome,
            self.narrative_builder.default_likely_outcome(
                final_score,
                resolved_outcome,
            ),
            max_length=500,
        )

        return PredictionResult(
            success_probability=final_score,
            probability_low=confidence.probability_low,
            probability_high=confidence.probability_high,
            confidence_score=confidence.confidence_score,
            confidence=confidence.confidence,
            evidence_sufficiency=confidence.evidence_sufficiency,
            likely_outcome=likely_outcome,
            probability_reasoning=reasoning,
            outcome_state=resolved_outcome,
            outcome_distribution=outcome_distribution,
            main_influence_factors=factors,
            calculation_trace=PredictionCalculationTrace(
                scenario_prior=round(breakdown.scenario_prior, 2),
                dynamics_contribution=round(breakdown.dynamics_contribution, 2),
                relationship_contribution=round(
                    breakdown.relationship_contribution,
                    2,
                ),
                trend_contribution=round(breakdown.trend_contribution, 2),
                semantic_adjustment=round(semantic_adjustment, 2),
                pre_guardrail_score=round(pre_guardrail, 2),
                guardrail_adjustment=round(guardrail_adjustment, 2),
                final_score=final_score,
                uncertainty_width=confidence.uncertainty_width,
                volatility_score=round(confidence.volatility, 2),
            ),
            calibration_version=self.calibration.version,
        )

    # ------------------------------------------------------------------
    # 兼容旧测试或外部代码调用的私有方法。新代码应直接使用对应组件。
    # ------------------------------------------------------------------

    def _scenario_prior_factors(
        self,
        context: PredictionContext,
        prior: float,
    ) -> list[PredictionInfluenceFactor]:
        return self.factor_factory.scenario_prior_factors(context, prior)

    def _score_dynamics(
        self,
        context: PredictionContext,
    ) -> tuple[float, list[PredictionInfluenceFactor]]:
        return self.scorer.score_dynamics(context)

    def _score_relationship(
        self,
        context: PredictionContext,
    ) -> tuple[float, list[PredictionInfluenceFactor]]:
        return self.scorer.score_relationship(context)

    def _score_trend(
        self,
        context: PredictionContext,
    ) -> tuple[float, list[PredictionInfluenceFactor]]:
        return self.scorer.score_trend(context)

    def _semantic_factors(
        self,
        *,
        context: PredictionContext,
        semantic: SemanticPredictionAssessment,
        semantic_adjustment: float,
    ) -> list[PredictionInfluenceFactor]:
        return self.factor_factory.semantic_factors(
            context=context,
            semantic=semantic,
            semantic_adjustment=semantic_adjustment,
        )

    def _apply_guardrails(
        self,
        *,
        score: float,
        context: PredictionContext,
        outcome_state: OutcomeState,
    ) -> GuardrailResult:
        return self.guardrails.apply(
            score=score,
            context=context,
            outcome_state=outcome_state,
        )

    def _resolve_outcome_state(
        self,
        context: PredictionContext,
        semantic: SemanticPredictionAssessment,
    ) -> OutcomeState:
        return self.outcome_resolver.resolve(context, semantic)

    def _confidence_score(
        self,
        *,
        context: PredictionContext,
        semantic: SemanticPredictionAssessment,
        outcome_state: OutcomeState,
    ) -> int:
        return self.confidence_calculator.confidence_score(
            context=context,
            semantic=semantic,
            outcome_state=outcome_state,
        )

    def _evidence_sufficiency(self, context: PredictionContext) -> str:
        return self.confidence_calculator.evidence_sufficiency(context)

    def _confidence_label(self, score: int) -> str:
        return self.confidence_calculator.confidence_label(score)

    def _uncertainty_width(
        self,
        *,
        confidence_score: int,
        evidence_sufficiency: str,
        volatility: float,
    ) -> int:
        return self.confidence_calculator.uncertainty_width(
            confidence_score=confidence_score,
            evidence_sufficiency=evidence_sufficiency,
            volatility=volatility,
        )

    def _volatility(self, history: list[ConversationDynamicsSnapshot]) -> float:
        return self.confidence_calculator.volatility(history)

    def _outcome_distribution(
        self,
        *,
        success_probability: int,
        confidence_score: int,
        outcome_state: OutcomeState,
    ) -> OutcomeDistribution:
        return self.distribution_calculator.calculate(
            success_probability=success_probability,
            confidence_score=confidence_score,
            outcome_state=outcome_state,
        )

    def _normalize_distribution(self, weights: dict[str, float]) -> dict[str, int]:
        return self.distribution_calculator.normalize(weights)

    def _metric_factor(self, **kwargs: object) -> PredictionInfluenceFactor:
        return self.factor_factory.metric_factor(**kwargs)  # type: ignore[arg-type]

    def _guardrail_factor(self, **kwargs: object) -> PredictionInfluenceFactor:
        return self.factor_factory.guardrail_factor(**kwargs)  # type: ignore[arg-type]

    def _build_reasoning(self, **kwargs: object) -> str:
        return self.narrative_builder.build_reasoning(**kwargs)  # type: ignore[arg-type]

    def _default_likely_outcome(
        self,
        score: int,
        outcome_state: OutcomeState,
    ) -> str:
        return self.narrative_builder.default_likely_outcome(score, outcome_state)

    @staticmethod
    def _latest_turns(context: PredictionContext) -> list[int]:
        return latest_turns(context)

    @staticmethod
    def _direction(contribution: float) -> str:
        return direction(contribution)

    @staticmethod
    def _importance(contribution: float) -> int:
        return importance(contribution)

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        return contains_any(text, keywords)

    @staticmethod
    def _clean_text(value: object, default: str, *, max_length: int) -> str:
        return clean_text(value, default, max_length=max_length)

    @staticmethod
    def _clamp(value: int | float, low: int, high: int) -> int:
        return clamp_int(value, low, high)

    @staticmethod
    def _clamp_float(value: float, low: float, high: float) -> float:
        return clamp_float(value, low, high)
