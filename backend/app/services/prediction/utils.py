from __future__ import annotations

from math import isfinite
from typing import Iterable

from app.schemas.prediction import PredictionContext


def clamp_int(value: int | float, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


def clamp_float(value: float, low: float, high: float) -> float:
    if not isfinite(value):
        return low
    return max(low, min(high, float(value)))


def clean_text(value: object, default: str, *, max_length: int) -> str:
    text = value.strip() if isinstance(value, str) else ""
    text = text or default
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "…"


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def direction(contribution: float) -> str:
    if contribution > 0.25:
        return "positive"
    if contribution < -0.25:
        return "negative"
    return "mixed"


def importance(contribution: float) -> int:
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


def latest_turns(context: PredictionContext) -> list[int]:
    if context.latest_user_turn_index <= 0:
        return []
    return [context.latest_user_turn_index]
