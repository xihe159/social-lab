from __future__ import annotations

from app.schemas.common import RelationshipState
from app.schemas.dynamics import ConversationDynamics
from app.schemas.prediction import (
    PredictionContext,
    SemanticInfluenceFactor,
    SemanticPredictionAssessment,
)
from app.services.prediction import (
    OutcomeDistributionCalculator,
    PredictionCalculator,
    PredictionConfidenceCalculator,
    PredictionOutcomeResolver,
)
from app.services.prediction_calculator import (
    PredictionCalculator as CompatibilityPredictionCalculator,
)


def _context(*, target: str, target_turns: int = 2) -> PredictionContext:
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
        current_dynamics=ConversationDynamics(
            atmosphere_score=60,
            pace_score=60,
            pressure_level=30,
            clarity_score=65,
            responsiveness_score=60,
            progress_score=55,
            repairability_score=65,
            boundary_score=70,
            rhythm_label="balanced",
            atmosphere_label="safe",
            recommended_next_move="advance",
            dynamics_reason="测试动态",
        ),
        dynamics_history=[],
        user_turn_count=2,
        target_turn_count=target_turns,
        total_message_count=2 + target_turns,
        last_user_message="我会在周三提交完整版本。",
        last_target_message=target,
        latest_user_turn_index=3,
    )


def _semantic(state: str = "hesitate") -> SemanticPredictionAssessment:
    return SemanticPredictionAssessment(
        outcome_state=state,
        semantic_adjustment=0,
        evidence_strength=0.8,
        likely_outcome="测试结果",
        probability_reasoning="测试判断",
        semantic_factors=[
            SemanticInfluenceFactor(
                factor_name="目标人物最新态度",
                direction="mixed",
                importance=3,
                evidence_turns=[4],
                evidence_quote="我再考虑一下。",
                explanation="最新回应影响当前判断。",
            )
        ],
    )


def test_old_import_path_remains_compatible() -> None:
    assert CompatibilityPredictionCalculator is PredictionCalculator


def test_outcome_resolver_prioritizes_explicit_refusal() -> None:
    result = PredictionOutcomeResolver().resolve(
        _context(target="不行，我不接受这个安排。"),
        _semantic("accept"),
    )
    assert result == "refuse"


def test_distribution_component_always_sums_to_100() -> None:
    result = OutcomeDistributionCalculator().calculate(
        success_probability=55,
        confidence_score=60,
        outcome_state="hesitate",
    )
    assert sum(result.model_dump().values()) == 100


def test_confidence_component_marks_missing_target_as_insufficient() -> None:
    context = _context(target="", target_turns=0)
    context.current_dynamics = None
    semantic = _semantic("unknown")
    assessment = PredictionConfidenceCalculator().assess(
        context=context,
        semantic=semantic,
        outcome_state="unknown",
        final_score=40,
    )
    assert assessment.evidence_sufficiency == "insufficient"
    assert assessment.confidence == "low"
    assert assessment.uncertainty_width >= 20
