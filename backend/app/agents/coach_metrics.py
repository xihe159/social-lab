from __future__ import annotations

import math
import re
from statistics import pstdev
from typing import Any, Iterable

from app.schemas.coach import DynamicsFeatureVector, SentenceUnit
from app.schemas.report import ReportRequest


_DEFAULT_METRIC = 50
_METRIC_NAMES = (
    "atmosphere_score",
    "pace_score",
    "pressure_level",
    "clarity_score",
    "responsiveness_score",
    "progress_score",
    "repairability_score",
    "boundary_score",
)


def _clamp(value: float, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, round(value)))


def _metric(snapshot: Any, name: str, default: int = _DEFAULT_METRIC) -> int:
    metrics = getattr(snapshot, "metrics", snapshot)
    value = getattr(metrics, name, default)
    try:
        return _clamp(float(value))
    except (TypeError, ValueError):
        return default


def build_dynamics_features(request: ReportRequest) -> DynamicsFeatureVector:
    timeline = list(request.state_timeline or [])
    user_turn_count = sum(
        1 for message in request.messages if message.role == "user" and message.content.strip()
    )

    if timeline:
        first = timeline[0]
        latest = timeline[-1]
        first_values = {name: _metric(first, name) for name in _METRIC_NAMES}
        latest_values = {name: _metric(latest, name) for name in _METRIC_NAMES}
        series = [
            [_metric(snapshot, name) for snapshot in timeline]
            for name in _METRIC_NAMES
        ]
        volatility = sum(pstdev(values) if len(values) > 1 else 0 for values in series) / len(series)
    else:
        first_values = {name: _DEFAULT_METRIC for name in _METRIC_NAMES}
        latest_values = dict(first_values)
        volatility = 0.0

    coverage = min(1.0, len(timeline) / max(1, user_turn_count))

    weighted_baseline = (
        0.12 * latest_values["atmosphere_score"]
        + 0.10 * latest_values["pace_score"]
        + 0.06 * (100 - latest_values["pressure_level"])
        + 0.16 * latest_values["clarity_score"]
        + 0.14 * latest_values["responsiveness_score"]
        + 0.24 * latest_values["progress_score"]
        + 0.10 * latest_values["repairability_score"]
        + 0.08 * latest_values["boundary_score"]
    )

    deltas = {
        name: latest_values[name] - first_values[name]
        for name in _METRIC_NAMES
    }
    trend_raw = (
        0.22 * deltas["progress_score"]
        + 0.18 * deltas["clarity_score"]
        + 0.16 * deltas["responsiveness_score"]
        + 0.14 * deltas["atmosphere_score"]
        + 0.10 * deltas["pace_score"]
        + 0.10 * deltas["repairability_score"]
        + 0.10 * deltas["boundary_score"]
        - 0.16 * deltas["pressure_level"]
    ) / 10
    trend_adjustment = max(-10, min(10, round(trend_raw)))

    # 没有时间线时保持保守；有较完整时间线时才让量化分充分发挥作用。
    evidence_weight = 0.55 + 0.45 * coverage
    baseline = _clamp(50 + (weighted_baseline - 50) * evidence_weight + trend_adjustment)

    return DynamicsFeatureVector(
        turn_count=user_turn_count,
        timeline_coverage=round(coverage, 3),
        latest_atmosphere=latest_values["atmosphere_score"],
        latest_pace=latest_values["pace_score"],
        latest_pressure=latest_values["pressure_level"],
        latest_clarity=latest_values["clarity_score"],
        latest_responsiveness=latest_values["responsiveness_score"],
        latest_progress=latest_values["progress_score"],
        latest_repairability=latest_values["repairability_score"],
        latest_boundary=latest_values["boundary_score"],
        atmosphere_delta=deltas["atmosphere_score"],
        pace_delta=deltas["pace_score"],
        pressure_delta=deltas["pressure_level"],
        clarity_delta=deltas["clarity_score"],
        responsiveness_delta=deltas["responsiveness_score"],
        progress_delta=deltas["progress_score"],
        repairability_delta=deltas["repairability_score"],
        boundary_delta=deltas["boundary_score"],
        volatility=round(volatility, 2),
        quantitative_baseline=baseline,
        trend_adjustment=trend_adjustment,
    )


def confidence_from_features(features: DynamicsFeatureVector) -> tuple[str, int]:
    turn_component = min(45, features.turn_count * 9)
    coverage_component = round(features.timeline_coverage * 40)
    stability_component = max(0, round(15 - min(15, features.volatility)))
    score = _clamp(turn_component + coverage_component + stability_component)
    if score >= 75:
        return "high", score
    if score >= 45:
        return "medium", score
    return "low", score


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?；;])|\n+")


def split_user_sentences(request: ReportRequest, max_sentences: int = 24) -> list[SentenceUnit]:
    units: list[SentenceUnit] = []
    user_turn = 0
    for message in request.messages:
        if message.role != "user" or not message.content.strip():
            continue
        user_turn += 1
        pieces = [piece.strip() for piece in _SENTENCE_SPLIT_RE.split(message.content) if piece.strip()]
        if not pieces:
            pieces = [message.content.strip()]
        for sentence_index, text in enumerate(pieces, start=1):
            units.append(
                SentenceUnit(
                    sentence_id=f"u{user_turn}s{sentence_index}",
                    turn_index=user_turn,
                    sentence_index=sentence_index,
                    text=text,
                )
            )
            if len(units) >= max_sentences:
                return units
    return units


def exact_or_nearest_quote(quote: str, units: Iterable[SentenceUnit]) -> str:
    quote = (quote or "").strip()
    texts = [unit.text for unit in units]
    if quote and any(quote in text or text in quote for text in texts):
        return quote
    return texts[0] if texts else "未找到可验证的用户原话。"
