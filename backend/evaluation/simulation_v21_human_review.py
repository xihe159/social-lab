from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from evaluation.strategy_evaluation_baseline import (
    BaselineCatalog,
    load_baseline_catalog,
)


class ReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VersionScore(ReviewModel):
    naturalness: int = Field(ge=1, le=5)
    persona_consistency: int = Field(ge=1, le=5)
    emotional_continuity: int = Field(ge=1, le=5)
    hard_error: bool = False


class PairedHumanReview(ReviewModel):
    case_id: str
    winner: Literal["v1", "v2.1", "tie"]
    v1: VersionScore
    v21: VersionScore
    ordinary_turn: bool
    v21_evaluation_intervened: bool
    notes: str = Field(default="", max_length=500)


class V21ReleaseSummary(ReviewModel):
    case_count: int
    decisive_case_count: int
    v21_win_rate: float
    v1_persona_consistency: float
    v21_persona_consistency: float
    v21_hard_error_rate: float
    ordinary_evaluation_non_intervention_rate: float
    gates_passed: bool
    failed_gates: list[str]


def summarize_paired_reviews(
    reviews: list[PairedHumanReview],
    *,
    catalog: BaselineCatalog | None = None,
) -> V21ReleaseSummary:
    catalog = catalog or load_baseline_catalog()
    expected = {case.case_id for case in catalog.cases}
    actual = [review.case_id for review in reviews]
    if len(actual) != len(set(actual)):
        raise ValueError("paired reviews contain duplicate case_id values")
    if set(actual) != expected:
        raise ValueError("paired reviews must cover the complete fixed 36-case set")

    decisive = [review for review in reviews if review.winner != "tie"]
    v21_wins = sum(review.winner == "v2.1" for review in decisive)
    win_rate = v21_wins / len(decisive) if decisive else 0.0
    v1_persona = _average(review.v1.persona_consistency for review in reviews)
    v21_persona = _average(review.v21.persona_consistency for review in reviews)
    hard_error_rate = sum(
        review.v21.hard_error for review in reviews
    ) / len(reviews)
    ordinary = [review for review in reviews if review.ordinary_turn]
    non_intervention_rate = (
        sum(not review.v21_evaluation_intervened for review in ordinary)
        / len(ordinary)
        if ordinary
        else 0.0
    )

    failed: list[str] = []
    if win_rate < 0.55:
        failed.append("v21_win_rate_below_55_percent")
    if v21_persona < v1_persona:
        failed.append("persona_consistency_below_v1")
    if hard_error_rate > 0.03:
        failed.append("hard_error_rate_above_3_percent")
    if non_intervention_rate < 0.85:
        failed.append("ordinary_evaluation_non_intervention_below_85_percent")

    return V21ReleaseSummary(
        case_count=len(reviews),
        decisive_case_count=len(decisive),
        v21_win_rate=round(win_rate, 4),
        v1_persona_consistency=v1_persona,
        v21_persona_consistency=v21_persona,
        v21_hard_error_rate=round(hard_error_rate, 4),
        ordinary_evaluation_non_intervention_rate=round(
            non_intervention_rate,
            4,
        ),
        gates_passed=not failed,
        failed_gates=failed,
    )


def load_paired_reviews(path: Path) -> list[PairedHumanReview]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [PairedHumanReview.model_validate(item) for item in payload]


def _average(values) -> float:
    items = list(values)
    return round(sum(items) / len(items), 3) if items else 0.0
