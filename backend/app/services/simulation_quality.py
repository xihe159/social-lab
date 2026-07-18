from __future__ import annotations

from collections.abc import Mapping


SIMULATION_QUALITY_PASS_THRESHOLD = 0.75

BASE_DIMENSION_WEIGHTS: dict[str, float] = {
    "persona_fidelity": 0.20,
    "dyadic_consistency": 0.15,
    "state_continuity": 0.15,
    "strategy_adherence": 0.15,
    "reaction_plausibility": 0.15,
    "style_fidelity": 0.10,
    "evidence_grounding": 0.10,
}

# Without uploaded chat evidence, style/evidence claims carry half weight. The
# remaining weight is distributed across the five context-independent checks.
LIMITED_EVIDENCE_DIMENSION_WEIGHTS: dict[str, float] = {
    "persona_fidelity": 0.22,
    "dyadic_consistency": 0.17,
    "state_continuity": 0.17,
    "strategy_adherence": 0.17,
    "reaction_plausibility": 0.17,
    "style_fidelity": 0.05,
    "evidence_grounding": 0.05,
}


def dimension_weights(*, chat_record_available: bool) -> dict[str, float]:
    source = (
        BASE_DIMENSION_WEIGHTS
        if chat_record_available
        else LIMITED_EVIDENCE_DIMENSION_WEIGHTS
    )
    return dict(source)


def weighted_simulation_score(
    scores: Mapping[str, int],
    *,
    chat_record_available: bool,
) -> int:
    weights = dimension_weights(chat_record_available=chat_record_available)
    return round(
        sum(
            max(0, min(100, int(scores[dimension]))) * weight
            for dimension, weight in weights.items()
        )
    )
