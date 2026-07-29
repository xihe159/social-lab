from __future__ import annotations

from collections.abc import Iterable


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    normalized = text.lower()
    return any(keyword.lower() in normalized for keyword in keywords)


def append_unique(values: list[str], item: str) -> None:
    if item not in values:
        values.append(item)


def number(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clean_text(value: object, *, default: str) -> str:
    text = value.strip() if isinstance(value, str) else ""
    return text or default


def truncate(value: str, *, max_length: int) -> str:
    value = value.strip()
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "…"


def clean_list(values: Iterable[object], *, max_items: int) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        item = truncate(value.strip(), max_length=120)
        if item and item not in cleaned:
            cleaned.append(item)
    return cleaned[:max_items]
