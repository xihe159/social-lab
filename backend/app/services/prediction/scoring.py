from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.prediction import PredictionContext, PredictionInfluenceFactor
from app.services.prediction.calibration import (
    DEFAULT_CALIBRATION,
    PredictionCalibration,
)
from app.services.prediction.factors import PredictionFactorFactory
from app.services.prediction.utils import clamp_float, direction, importance, latest_turns


@dataclass(slots=True)
class PredictionScoreBreakdown:
    scenario_prior: float
    dynamics_contribution: float
    relationship_contribution: float
    trend_contribution: float
    factors: list[PredictionInfluenceFactor] = field(default_factory=list)

    @property
    def deterministic_score(self) -> float:
        return (
            self.scenario_prior
            + self.dynamics_contribution
            + self.relationship_contribution
            + self.trend_contribution
        )


class PredictionScorer:
    """计算场景、Dynamics、关系状态与趋势的确定性贡献。"""

    def __init__(
        self,
        calibration: PredictionCalibration = DEFAULT_CALIBRATION,
        factor_factory: PredictionFactorFactory | None = None,
    ) -> None:
        self.calibration = calibration
        self.factor_factory = factor_factory or PredictionFactorFactory(calibration)

    def score(self, context: PredictionContext) -> PredictionScoreBreakdown:
        prior = float(self.calibration.scenario_priors[context.scenario])
        dynamics_score, dynamics_factors = self.score_dynamics(context)
        relationship_score, relationship_factors = self.score_relationship(context)
        trend_score, trend_factors = self.score_trend(context)

        return PredictionScoreBreakdown(
            scenario_prior=prior,
            dynamics_contribution=dynamics_score,
            relationship_contribution=relationship_score,
            trend_contribution=trend_score,
            factors=[
                *self.factor_factory.scenario_prior_factors(context, prior),
                *dynamics_factors,
                *relationship_factors,
                *trend_factors,
            ],
        )

    def score_dynamics(
        self,
        context: PredictionContext,
    ) -> tuple[float, list[PredictionInfluenceFactor]]:
        dynamics = context.current_dynamics
        if dynamics is None:
            return 0.0, []

        total = 0.0
        factors: list[PredictionInfluenceFactor] = []
        evidence = dynamics.dynamics_reason or "当前对话动态指标"

        for metric_name, weight in self.calibration.dynamic_weights.items():
            value = float(getattr(dynamics, metric_name))
            contribution = weight * (value - 50.0)
            total += contribution
            if abs(contribution) >= 1.25:
                factors.append(
                    self.factor_factory.metric_factor(
                        metric_name=metric_name,
                        metric_value=value,
                        contribution=contribution,
                        source="dynamic",
                        evidence_turns=latest_turns(context),
                        evidence_quote=evidence,
                    )
                )

        limit = self.calibration.dynamics_score_limit
        return clamp_float(total, -limit, limit), factors

    def score_relationship(
        self,
        context: PredictionContext,
    ) -> tuple[float, list[PredictionInfluenceFactor]]:
        state = context.relationship_state
        total = 0.0
        factors: list[PredictionInfluenceFactor] = []
        values: dict[str, float] = {
            "trust": float(state.trust),
            "respect": float(state.respect),
            "familiarity": float(state.familiarity),
            "affinity": float(state.affinity),
            "emotional": clamp_float((state.emotional + 100) / 2, 0, 100),
        }

        for metric_name, weight in self.calibration.relationship_weights.items():
            value = values[metric_name]
            contribution = weight * (value - 50.0)
            total += contribution
            if abs(contribution) >= 1.25:
                factors.append(
                    self.factor_factory.metric_factor(
                        metric_name=metric_name,
                        metric_value=value,
                        contribution=contribution,
                        source="relationship",
                        evidence_turns=[],
                        evidence_quote="当前 Persona 关系状态",
                    )
                )

        authority_weight = self.calibration.authority_weights[context.scenario]
        authority_contribution = authority_weight * (state.authority - 50)
        total += authority_contribution
        if abs(authority_contribution) >= 1.25:
            factors.append(
                PredictionInfluenceFactor(
                    factor_name="权力距离",
                    direction=direction(authority_contribution),
                    importance=importance(authority_contribution),
                    contribution=round(authority_contribution, 2),
                    source="relationship",
                    metric_name="authority",
                    metric_value=float(state.authority),
                    evidence_turns=[],
                    evidence_quote="当前 Persona 权力距离",
                    explanation=(
                        "较高的权力距离会提高请求被审视、延后或附加条件的可能性。"
                        if authority_contribution < 0
                        else "较低的权力距离使双方更容易直接协商。"
                    ),
                )
            )

        limit = self.calibration.relationship_score_limit
        return clamp_float(total, -limit, limit), factors

    def score_trend(
        self,
        context: PredictionContext,
    ) -> tuple[float, list[PredictionInfluenceFactor]]:
        history = context.dynamics_history
        if len(history) < 2:
            return 0.0, []

        first = history[0]
        last = history[-1]
        total = 0.0
        factors: list[PredictionInfluenceFactor] = []

        for metric_name, weight in self.calibration.trend_weights.items():
            change = float(getattr(last, metric_name) - getattr(first, metric_name))
            contribution = weight * change
            total += contribution
            if abs(contribution) >= 1.0:
                label = self.calibration.metric_labels[metric_name]
                factors.append(
                    PredictionInfluenceFactor(
                        factor_name=f"{label}趋势",
                        direction=direction(contribution),
                        importance=importance(contribution),
                        contribution=round(contribution, 2),
                        source="trend",
                        metric_name=metric_name,
                        metric_value=change,
                        evidence_turns=[first.turn_index, last.turn_index],
                        evidence_quote=(
                            f"第 {first.turn_index} 轮到第 {last.turn_index} 轮，"
                            f"{label}变化 {change:+.0f}"
                        ),
                        explanation=(
                            f"{label}持续改善，提高了目标继续推进的可能性。"
                            if contribution > 0
                            else f"{label}持续恶化，增加了对方犹豫或拒绝的可能性。"
                        ),
                    )
                )

        limit = self.calibration.trend_score_limit
        return clamp_float(total, -limit, limit), factors
