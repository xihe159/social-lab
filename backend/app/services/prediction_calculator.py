from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import pstdev
from typing import Iterable

from app.schemas.dynamics import ConversationDynamics, ConversationDynamicsSnapshot
from app.schemas.prediction import (
    OutcomeDistribution,
    OutcomeState,
    PredictionCalculationTrace,
    PredictionContext,
    PredictionInfluenceFactor,
    PredictionResult,
    SemanticPredictionAssessment,
)


CALIBRATION_VERSION = "social-lab-prediction-v2.0-rules-2026-07"

SCENARIO_PRIORS: dict[str, float] = {
    "advisor": 45.0,
    "work": 48.0,
    "social": 50.0,
}

DYNAMIC_WEIGHTS: dict[str, float] = {
    "atmosphere_score": 0.12,
    "pace_score": 0.08,
    "pressure_level": -0.16,
    "clarity_score": 0.10,
    "responsiveness_score": 0.12,
    "progress_score": 0.22,
    "repairability_score": 0.08,
    "boundary_score": 0.12,
}

RELATIONSHIP_WEIGHTS: dict[str, float] = {
    "trust": 0.05,
    "respect": 0.03,
    "familiarity": 0.02,
    "affinity": 0.03,
    "emotional": 0.04,
}

TREND_WEIGHTS: dict[str, float] = {
    "atmosphere_score": 0.08,
    "pace_score": 0.05,
    "pressure_level": -0.10,
    "clarity_score": 0.05,
    "responsiveness_score": 0.06,
    "progress_score": 0.12,
    "repairability_score": 0.05,
    "boundary_score": 0.06,
}

METRIC_LABELS: dict[str, str] = {
    "atmosphere_score": "对话氛围",
    "pace_score": "节奏健康度",
    "pressure_level": "沟通压力",
    "clarity_score": "表达清晰度",
    "responsiveness_score": "回应对方顾虑",
    "progress_score": "目标推进度",
    "repairability_score": "后续可修复性",
    "boundary_score": "边界健康度",
    "trust": "关系信任",
    "respect": "相互尊重",
    "familiarity": "关系熟悉度",
    "affinity": "关系亲近度",
    "emotional": "情绪稳定度",
}


@dataclass(frozen=True)
class _GuardrailResult:
    score: float
    reason: str | None


class PredictionCalculator:
    """
    可解释、可测试、可校准的成功率计算器。

    最终评分 =
        场景先验
        + Dynamics 当前状态贡献
        + 关系状态贡献
        + Dynamics 趋势贡献
        + LLM 有限语义修正
        + 明确接受/拒绝/高压等确定性护栏

    注意：当前分值是“模拟成功评分”，不是现实统计概率。
    """

    def calculate(
        self,
        *,
        context: PredictionContext,
        semantic: SemanticPredictionAssessment,
    ) -> PredictionResult:
        prior = SCENARIO_PRIORS[context.scenario]

        dynamics_score, dynamics_factors = self._score_dynamics(context)
        relationship_score, relationship_factors = self._score_relationship(context)
        trend_score, trend_factors = self._score_trend(context)

        semantic_adjustment = float(
            self._clamp(semantic.semantic_adjustment, -8, 8)
        )
        semantic_factors = self._semantic_factors(
            context=context,
            semantic=semantic,
            semantic_adjustment=semantic_adjustment,
        )

        pre_guardrail = (
            prior
            + dynamics_score
            + relationship_score
            + trend_score
            + semantic_adjustment
        )
        pre_guardrail = self._clamp_float(pre_guardrail, 0.0, 100.0)

        resolved_outcome = self._resolve_outcome_state(context, semantic)
        guardrail = self._apply_guardrails(
            score=pre_guardrail,
            context=context,
            outcome_state=resolved_outcome,
        )
        final_score = self._clamp(round(guardrail.score), 0, 100)
        guardrail_adjustment = final_score - pre_guardrail

        confidence_score = self._confidence_score(
            context=context,
            semantic=semantic,
            outcome_state=resolved_outcome,
        )
        evidence_sufficiency = self._evidence_sufficiency(context)
        confidence = self._confidence_label(confidence_score)

        volatility = self._volatility(context.dynamics_history)
        uncertainty_width = self._uncertainty_width(
            confidence_score=confidence_score,
            evidence_sufficiency=evidence_sufficiency,
            volatility=volatility,
        )
        probability_low = self._clamp(final_score - uncertainty_width, 0, 100)
        probability_high = self._clamp(final_score + uncertainty_width, 0, 100)

        factors = [
            *self._scenario_prior_factors(context, prior),
            *dynamics_factors,
            *relationship_factors,
            *trend_factors,
            *semantic_factors,
        ]
        if abs(guardrail_adjustment) >= 0.5:
            factors.append(
                self._guardrail_factor(
                    context=context,
                    adjustment=guardrail_adjustment,
                    reason=guardrail.reason or "确定性结果护栏修正",
                )
            )

        factors.sort(
            key=lambda item: (abs(item.contribution), item.importance),
            reverse=True,
        )
        factors = factors[:5]

        outcome_distribution = self._outcome_distribution(
            success_probability=final_score,
            confidence_score=confidence_score,
            outcome_state=resolved_outcome,
        )

        reasoning = self._build_reasoning(
            semantic_reasoning=semantic.probability_reasoning,
            prior=prior,
            dynamics=dynamics_score,
            relationship=relationship_score,
            trend=trend_score,
            semantic_adjustment=semantic_adjustment,
            guardrail_adjustment=guardrail_adjustment,
            confidence=confidence,
            probability_low=probability_low,
            probability_high=probability_high,
        )

        likely_outcome = self._clean_text(
            semantic.likely_outcome,
            self._default_likely_outcome(final_score, resolved_outcome),
            max_length=500,
        )

        return PredictionResult(
            success_probability=final_score,
            probability_low=probability_low,
            probability_high=probability_high,
            confidence_score=confidence_score,
            confidence=confidence,
            evidence_sufficiency=evidence_sufficiency,
            likely_outcome=likely_outcome,
            probability_reasoning=reasoning,
            outcome_state=resolved_outcome,
            outcome_distribution=outcome_distribution,
            main_influence_factors=factors,
            calculation_trace=PredictionCalculationTrace(
                scenario_prior=round(prior, 2),
                dynamics_contribution=round(dynamics_score, 2),
                relationship_contribution=round(relationship_score, 2),
                trend_contribution=round(trend_score, 2),
                semantic_adjustment=round(semantic_adjustment, 2),
                pre_guardrail_score=round(pre_guardrail, 2),
                guardrail_adjustment=round(guardrail_adjustment, 2),
                final_score=final_score,
                uncertainty_width=uncertainty_width,
                volatility_score=round(volatility, 2),
            ),
            calibration_version=CALIBRATION_VERSION,
        )

    def _scenario_prior_factors(
        self,
        context: PredictionContext,
        prior: float,
    ) -> list[PredictionInfluenceFactor]:
        contribution = prior - 50.0
        if abs(contribution) < 0.5:
            return []

        labels = {
            "advisor": "导师场景先验",
            "work": "职场场景先验",
            "social": "社交场景先验",
        }
        return [
            PredictionInfluenceFactor(
                factor_name=labels[context.scenario],
                direction=self._direction(contribution),
                importance=self._importance(contribution),
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

    def _score_dynamics(
        self,
        context: PredictionContext,
    ) -> tuple[float, list[PredictionInfluenceFactor]]:
        dynamics = context.current_dynamics
        if dynamics is None:
            return 0.0, []

        total = 0.0
        factors: list[PredictionInfluenceFactor] = []
        evidence = dynamics.dynamics_reason or "当前对话动态指标"

        for metric_name, weight in DYNAMIC_WEIGHTS.items():
            value = float(getattr(dynamics, metric_name))
            contribution = weight * (value - 50.0)
            total += contribution

            if abs(contribution) >= 1.25:
                factors.append(
                    self._metric_factor(
                        metric_name=metric_name,
                        metric_value=value,
                        contribution=contribution,
                        source="dynamic",
                        evidence_turns=self._latest_turns(context),
                        evidence_quote=evidence,
                    )
                )

        return self._clamp_float(total, -24.0, 24.0), factors

    def _score_relationship(
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
            "emotional": self._clamp_float((state.emotional + 100) / 2, 0, 100),
        }

        for metric_name, weight in RELATIONSHIP_WEIGHTS.items():
            value = values[metric_name]
            contribution = weight * (value - 50.0)
            total += contribution

            if abs(contribution) >= 1.25:
                factors.append(
                    self._metric_factor(
                        metric_name=metric_name,
                        metric_value=value,
                        contribution=contribution,
                        source="relationship",
                        evidence_turns=[],
                        evidence_quote="当前 Persona 关系状态",
                    )
                )

        # 权力距离只作为小幅场景修正，避免与尊重/信任重复计分。
        authority_weight = {
            "advisor": -0.03,
            "work": -0.02,
            "social": -0.01,
        }[context.scenario]
        authority_contribution = authority_weight * (state.authority - 50)
        total += authority_contribution

        if abs(authority_contribution) >= 1.25:
            factors.append(
                PredictionInfluenceFactor(
                    factor_name="权力距离",
                    direction=self._direction(authority_contribution),
                    importance=self._importance(authority_contribution),
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

        return self._clamp_float(total, -12.0, 12.0), factors

    def _score_trend(
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

        for metric_name, weight in TREND_WEIGHTS.items():
            change = float(
                getattr(last, metric_name) - getattr(first, metric_name)
            )
            contribution = weight * change
            total += contribution

            if abs(contribution) >= 1.0:
                label = METRIC_LABELS[metric_name]
                factors.append(
                    PredictionInfluenceFactor(
                        factor_name=f"{label}趋势",
                        direction=self._direction(contribution),
                        importance=self._importance(contribution),
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

        return self._clamp_float(total, -8.0, 8.0), factors

    def _semantic_factors(
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

            contribution = semantic_adjustment * share
            contribution = self._clamp_float(contribution, -8.0, 8.0)

            factors.append(
                PredictionInfluenceFactor(
                    factor_name=factor.factor_name,
                    direction=self._direction(contribution)
                    if abs(contribution) >= 0.25
                    else factor.direction,
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

    def _apply_guardrails(
        self,
        *,
        score: float,
        context: PredictionContext,
        outcome_state: OutcomeState,
    ) -> _GuardrailResult:
        original = score
        reasons: list[str] = []

        dynamics = context.current_dynamics

        if context.user_turn_count == 0:
            score = min(score, 45.0)
            reasons.append("没有有效用户表达")
        if context.target_turn_count == 0:
            score = min(score, 58.0)
            reasons.append("没有目标人物回应")

        explicit_stop = self._contains_any(
            context.last_target_message,
            ["不要再", "别再", "不想继续", "到此为止", "停止联系", "end this"],
        )

        if explicit_stop or (
            dynamics is not None and dynamics.atmosphere_label == "blocked"
        ):
            score = min(score, 20.0)
            reasons.append("目标人物已表现出终止沟通或阻断信号")
        elif outcome_state == "refuse":
            score = min(score, 35.0)
            reasons.append("目标人物已明确拒绝")
        elif outcome_state == "no_response":
            score = min(score, 40.0)
            reasons.append("当前结果为不回应或冷处理")
        elif outcome_state == "conditional_accept":
            score = self._clamp_float(score, 52.0, 78.0)
            reasons.append("目标人物只表现出条件性接受")
        elif outcome_state == "accept":
            concrete_action = self._contains_any(
                context.last_target_message,
                ["时间", "明天", "今天", "周", "发我", "提交", "安排", "就这样", "确认"],
            )
            floor = 72.0 if concrete_action else 62.0
            score = max(score, floor)
            reasons.append("目标人物已给出接受信号")

        if dynamics is not None:
            if dynamics.pressure_level >= 80:
                score = min(score, 40.0)
                reasons.append("当前沟通压力过高")
            elif dynamics.pressure_level >= 70:
                score = min(score, 48.0)
                reasons.append("当前沟通压力明显偏高")

            if dynamics.boundary_score <= 25:
                score = min(score, 35.0)
                reasons.append("边界健康度过低")

            if (
                dynamics.progress_score >= 80
                and dynamics.atmosphere_score >= 65
                and outcome_state not in {"refuse", "no_response"}
            ):
                score = max(score, 68.0)
                reasons.append("目标推进与对话氛围均处于高位")

        score = self._clamp_float(score, 0.0, 100.0)
        reason = "；".join(dict.fromkeys(reasons)) if reasons else None

        if abs(score - original) < 0.5:
            reason = None
        return _GuardrailResult(score=score, reason=reason)

    def _resolve_outcome_state(
        self,
        context: PredictionContext,
        semantic: SemanticPredictionAssessment,
    ) -> OutcomeState:
        text = context.last_target_message

        explicit_stop = self._contains_any(
            text,
            ["不要再", "别再", "不想继续", "到此为止", "停止联系"],
        )
        refusal = self._contains_any(
            text,
            ["不行", "不能", "不接受", "不愿意", "拒绝", "算了"],
        )
        acceptance = self._contains_any(
            text,
            ["可以", "好", "行", "没问题", "同意", "愿意", "答应"],
        )
        conditional = self._contains_any(
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

    def _confidence_score(
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

        evidence_sufficiency = self._evidence_sufficiency(context)
        if evidence_sufficiency == "insufficient":
            score = min(score, 40.0)
        elif evidence_sufficiency == "partial":
            score = min(score, 70.0)

        return self._clamp(round(score), 0, 95)

    @staticmethod
    def _evidence_sufficiency(context: PredictionContext) -> str:
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
    def _confidence_label(score: int) -> str:
        if score >= 75:
            return "high"
        if score >= 45:
            return "medium"
        return "low"

    def _uncertainty_width(
        self,
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

        return self._clamp(round(width), 8, 30)

    @staticmethod
    def _volatility(history: list[ConversationDynamicsSnapshot]) -> float:
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

    def _outcome_distribution(
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

        normalized = self._normalize_distribution(weights)
        return OutcomeDistribution(**normalized)

    @staticmethod
    def _normalize_distribution(weights: dict[str, float]) -> dict[str, int]:
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

    def _metric_factor(
        self,
        *,
        metric_name: str,
        metric_value: float,
        contribution: float,
        source: str,
        evidence_turns: list[int],
        evidence_quote: str,
    ) -> PredictionInfluenceFactor:
        label = METRIC_LABELS[metric_name]
        direction = self._direction(contribution)
        if contribution > 0:
            explanation = f"{label}处于有利水平，为目标推进提供正向支持。"
        elif contribution < 0:
            explanation = f"{label}处于不利水平，增加了对方犹豫、附加条件或拒绝的可能性。"
        else:
            explanation = f"{label}目前对结果影响有限。"

        return PredictionInfluenceFactor(
            factor_name=label,
            direction=direction,
            importance=self._importance(contribution),
            contribution=round(contribution, 2),
            source=source,
            metric_name=metric_name,
            metric_value=round(metric_value, 2),
            evidence_turns=evidence_turns,
            evidence_quote=self._clean_text(
                evidence_quote,
                f"{label}当前值 {metric_value:.0f}",
                max_length=180,
            ),
            explanation=explanation,
        )

    def _guardrail_factor(
        self,
        *,
        context: PredictionContext,
        adjustment: float,
        reason: str,
    ) -> PredictionInfluenceFactor:
        return PredictionInfluenceFactor(
            factor_name="明确结果信号",
            direction=self._direction(adjustment),
            importance=5,
            contribution=round(adjustment, 2),
            source="guardrail",
            metric_name=None,
            metric_value=None,
            evidence_turns=self._latest_turns(context),
            evidence_quote=self._clean_text(
                context.last_target_message,
                "目标人物当前没有可引用回复。",
                max_length=180,
            ),
            explanation=reason,
        )

    def _build_reasoning(
        self,
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
        semantic_text = self._clean_text(
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
    def _default_likely_outcome(
        score: int,
        outcome_state: OutcomeState,
    ) -> str:
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

    @staticmethod
    def _latest_turns(context: PredictionContext) -> list[int]:
        if context.latest_user_turn_index <= 0:
            return []
        return [context.latest_user_turn_index]

    @staticmethod
    def _direction(contribution: float) -> str:
        if contribution > 0.25:
            return "positive"
        if contribution < -0.25:
            return "negative"
        return "mixed"

    @staticmethod
    def _importance(contribution: float) -> int:
        magnitude = abs(contribution)
        if magnitude >= 8:
            return 5
        if magnitude >= 5:
            return 4
        if magnitude >= 3:
            return 3
        if magnitude >= 1.5:
            return 2
        return 1

    @staticmethod
    def _contains_any(text: str, keywords: Iterable[str]) -> bool:
        lowered = text.lower()
        return any(keyword.lower() in lowered for keyword in keywords)

    @staticmethod
    def _clean_text(value: str, default: str, *, max_length: int) -> str:
        text = value.strip() if isinstance(value, str) else ""
        text = text or default
        if len(text) <= max_length:
            return text
        return text[: max_length - 1].rstrip() + "…"

    @staticmethod
    def _clamp(value: int, low: int, high: int) -> int:
        return max(low, min(high, int(value)))

    @staticmethod
    def _clamp_float(value: float, low: float, high: float) -> float:
        if not isfinite(value):
            return low
        return max(low, min(high, float(value)))
