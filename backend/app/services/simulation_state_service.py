from __future__ import annotations

from uuid import uuid4

from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.simulation_state import RelationshipStateV2, SimulationState


def create_initial_simulation_state(
    persona: PersonaModelV2,
    *,
    session_id: str | None = None,
) -> SimulationState:
    """Create an independent, neutral runtime state from the dyadic profile."""

    dyadic = persona.dyadic_profile
    willingness_to_engage = _clamp(
        (dyadic.warmth + dyadic.patience + dyadic.psychological_safety) / 3
    )

    return SimulationState(
        session_id=(session_id or f"session_{uuid4().hex}").strip(),
        persona_id=persona.persona_id,
        relationship_state=RelationshipStateV2(
            trust=dyadic.trust,
            respect=dyadic.respect,
            warmth=dyadic.warmth,
            patience=dyadic.patience,
            psychological_safety=dyadic.psychological_safety,
            willingness_to_engage=willingness_to_engage,
        ),
    )


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)
