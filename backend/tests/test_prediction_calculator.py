from __future__ import annotations

from app.schemas.common import RelationshipState
from app.schemas.dynamics import (
    ConversationDynamics,
    ConversationDynamicsSnapshot,
)
from app.schemas.prediction import (
    PredictionContext,
    SemanticInfluenceFactor,
    SemanticPredictionAssessment,
)
from app.services.prediction_calculator import PredictionCalculator


def _dynamics(
    *,
    atmosphere: int = 60,
    pace: int = 60,
    pressure: int = 30,
    clarity: int = 65,
    responsiveness: int = 60,
    progress: int = 55,
    repairability: int = 65,
    boundary: int = 70,
    atmosphere_label: str = "safe",
) -> ConversationDynamics:
    return ConversationDynamics(
        atmosphere_score=atmosphere,
        pace_score=pace,
        pressure_level=pressure,
        clarity_score=clarity,
        responsiveness_score=responsiveness,
        progress_score=progress,
        repairability_score=repairability,
        boundary_score=boundary,
        rhythm_label="balanced",
        atmosphere_label=atmosphere_label,
        recommended_next_move="advance",
        dynamics_reason="测试动态",
    )


def _snapshot(turn: int, dynamics: ConversationDynamics) -> ConversationDynamicsSnapshot:
    return ConversationDynamicsSnapshot(
        turn_index=turn,
        atmosphere_score=dynamics.atmosphere_score,
        pace_score=dynamics.pace_score,
        pressure_level=dynamics.pressure_level,
        clarity_score=dynamics.clarity_score,
        responsiveness_score=dynamics.responsiveness_score,
        progress_score=dynamics.progress_score,
        repairability_score=dynamics.repairability_score,
        boundary_score=dynamics.boundary_score,
        rhythm_label=dynamics.rhythm_label,
        atmosphere_label=dynamics.atmosphere_label,
        recommended_next_move=dynamics.recommended_next_move,
        reason=dynamics.dynamics_reason,
    )


def _context(
    *,
    dynamics: ConversationDynamics | None,
    last_target: str,
    history: list[ConversationDynamicsSnapshot] | None = None,
    user_turns: int = 2,
    target_turns: int = 2,
) -> PredictionContext:
    return PredictionContext(
        scenario="advisor",
        goal="获得延期批准",
        outcome="导师接受周三提交",
        relationship_state=RelationshipState(
            trust=60,
            respect=65,
            familiarity=50,
            affinity=50,
            authority=70,
            emotional=10,
        ),
        current_dynamics=dynamics,
        dynamics_history=history or [],
        user_turn_count=user_turns,
        target_turn_count=target_turns,
        total_message_count=user_turns + target_turns,
        last_user_message="我会在周三提交完整版本。",
        last_target_message=last_target,
        latest_user_turn_index=max(1, user_turns + target_turns - 1),
    )


def _semantic(
    *,
    state: str,
    adjustment: int,
    quote: str,
) -> SemanticPredictionAssessment:
    return SemanticPredictionAssessment(
        outcome_state=state,
        semantic_adjustment=adjustment,
        evidence_strength=0.8,
        likely_outcome="测试结果",
        probability_reasoning="测试语义判断",
        semantic_factors=[
            SemanticInfluenceFactor(
                factor_name="目标人物最新态度",
                direction="positive" if adjustment > 0 else "negative",
                importance=5,
                evidence_turns=[4],
                evidence_quote=quote,
                explanation="最新回应直接影响当前结果判断。",
            )
        ],
    )


def test_explicit_refusal_caps_probability() -> None:
    result = PredictionCalculator().calculate(
        context=_context(
            dynamics=_dynamics(progress=80),
            last_target="不行，我不接受这个安排。",
        ),
        semantic=_semantic(
            state="accept",
            adjustment=8,
            quote="不行，我不接受这个安排。",
        ),
    )

    assert result.success_probability <= 35
    assert result.outcome_state == "refuse"
    assert result.outcome_distribution.refuse > result.outcome_distribution.accept


def test_explicit_acceptance_with_concrete_action_has_floor() -> None:
    result = PredictionCalculator().calculate(
        context=_context(
            dynamics=_dynamics(progress=72),
            last_target="可以，你周三前把完整版本发我。",
        ),
        semantic=_semantic(
            state="accept",
            adjustment=4,
            quote="可以，你周三前把完整版本发我。",
        ),
    )

    assert result.success_probability >= 72
    assert result.outcome_state == "accept"
    assert result.probability_low <= result.success_probability <= result.probability_high


def test_high_pressure_cannot_produce_high_score() -> None:
    result = PredictionCalculator().calculate(
        context=_context(
            dynamics=_dynamics(
                atmosphere=35,
                pressure=85,
                progress=70,
                boundary=20,
                atmosphere_label="defensive",
            ),
            last_target="我会考虑。",
        ),
        semantic=_semantic(
            state="hesitate",
            adjustment=8,
            quote="我会考虑。",
        ),
    )

    assert result.success_probability <= 35
    assert result.calculation_trace.guardrail_adjustment < 0


def test_improving_trend_raises_score() -> None:
    start = _dynamics(
        atmosphere=45,
        pressure=60,
        progress=35,
        boundary=45,
        atmosphere_label="tense",
    )
    end = _dynamics(
        atmosphere=70,
        pressure=30,
        progress=70,
        boundary=75,
        atmosphere_label="safe",
    )

    calculator = PredictionCalculator()
    semantic = _semantic(
        state="conditional_accept",
        adjustment=0,
        quote="你先把方案发我，我再确认。",
    )

    with_trend = calculator.calculate(
        context=_context(
            dynamics=end,
            last_target="可以，你先把方案发我，我再确认。",
            history=[_snapshot(1, start), _snapshot(3, end)],
        ),
        semantic=semantic,
    )
    without_trend = calculator.calculate(
        context=_context(
            dynamics=end,
            last_target="可以，你先把方案发我，我再确认。",
            history=[],
        ),
        semantic=semantic,
    )

    assert with_trend.calculation_trace.trend_contribution > 0
    assert with_trend.calculation_trace.pre_guardrail_score > without_trend.calculation_trace.pre_guardrail_score


def test_distribution_always_sums_to_100() -> None:
    result = PredictionCalculator().calculate(
        context=_context(
            dynamics=_dynamics(),
            last_target="我再考虑一下。",
        ),
        semantic=_semantic(
            state="hesitate",
            adjustment=0,
            quote="我再考虑一下。",
        ),
    )

    distribution = result.outcome_distribution
    assert (
        distribution.accept
        + distribution.conditional_accept
        + distribution.hesitate
        + distribution.refuse
        + distribution.no_response
    ) == 100


def test_missing_evidence_produces_wider_interval() -> None:
    calculator = PredictionCalculator()

    low_evidence = calculator.calculate(
        context=_context(
            dynamics=None,
            last_target="",
            user_turns=1,
            target_turns=0,
        ),
        semantic=SemanticPredictionAssessment(
            outcome_state="unknown",
            semantic_adjustment=0,
            evidence_strength=0.2,
            likely_outcome="信息不足",
            probability_reasoning="没有目标人物回应。",
            semantic_factors=[
                SemanticInfluenceFactor(
                    factor_name="信息不足",
                    direction="mixed",
                    importance=5,
                    evidence_turns=[1],
                    evidence_quote="只有一轮用户表达",
                    explanation="缺少目标人物回应。",
                )
            ],
        ),
    )

    assert low_evidence.evidence_sufficiency == "insufficient"
    assert low_evidence.confidence == "low"
    assert low_evidence.calculation_trace.uncertainty_width >= 20
