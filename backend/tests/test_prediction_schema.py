from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.prediction import OutcomeDistribution


def test_outcome_distribution_requires_total_100() -> None:
    with pytest.raises(ValidationError):
        OutcomeDistribution(
            accept=40,
            conditional_accept=20,
            hesitate=20,
            refuse=10,
            no_response=5,
        )


def test_outcome_distribution_accepts_total_100() -> None:
    result = OutcomeDistribution(
        accept=40,
        conditional_accept=20,
        hesitate=20,
        refuse=10,
        no_response=10,
    )
    assert result.accept == 40
