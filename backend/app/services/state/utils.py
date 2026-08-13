from __future__ import annotations

from collections.abc import Iterable


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    normalized = text.lower()
    return any(keyword.lower() in normalized for keyword in keywords)


def contains_affirmed_any(text: str, keywords: Iterable[str]) -> bool:
    """Match keywords while ignoring a nearby explicit negation."""

    normalized = text.lower()
    negators = (
        "不是",
        "并不是",
        "并非",
        "没有",
        "并没有",
        "不用",
        "无需",
        "不必",
        "不算",
        "未",
        "无",
        "not ",
        "no ",
        "never ",
        "isn't ",
        "wasn't ",
        "don't ",
        "didn't ",
    )
    for keyword in keywords:
        token = keyword.lower()
        start = 0
        while True:
            index = normalized.find(token, start)
            if index < 0:
                break
            prefix = normalized[max(0, index - 16):index].rstrip()
            for boundary in ("。", "！", "？", ".", "!", "?", "；", ";", "，", ",", "但是", "但", "不过", "却"):
                if boundary in prefix:
                    prefix = prefix.rsplit(boundary, 1)[-1]
            negated = any(
                negator.rstrip() in prefix[-12:]
                for negator in negators
            )
            if not negated:
                return True
            start = index + max(1, len(token))
    return False


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
