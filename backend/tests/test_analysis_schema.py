from __future__ import annotations

from app.schemas.analysis import (
    DynamicsSignalVector,
    RelationshipSignalVector,
    SentenceSemanticObservation,
)


def test_sentence_analysis_schema_has_no_advice_fields() -> None:
    fields = SentenceSemanticObservation.model_fields

    assert "fix_direction" not in fields
    assert "improvement_action" not in fields
    assert "suggested_rewrite" not in fields
    assert "next_step" not in fields


def test_signal_vectors_are_bounded() -> None:
    relationship = RelationshipSignalVector(
        trust=5,
        respect=-5,
        familiarity=0,
        affinity=1,
        authority=-1,
        emotional=2,
    )
    dynamics = DynamicsSignalVector(
        atmosphere_score=5,
        pace_score=-5,
        pressure_level=4,
        clarity_score=2,
        responsiveness_score=-2,
        progress_score=1,
        repairability_score=0,
        boundary_score=-4,
    )

    assert relationship.trust == 5
    assert dynamics.pressure_level == 4
