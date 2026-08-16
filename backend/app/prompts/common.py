from __future__ import annotations

import json
from typing import Any


def safe_text(value: Any, default: str = "未提供") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return to_jsonable(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value


def pretty_json(value: Any) -> str:
    return json.dumps(to_jsonable(value), ensure_ascii=False, indent=2, default=str)


def compact_json(value: Any) -> str:
    return json.dumps(to_jsonable(value), ensure_ascii=False, default=str)


def format_messages(messages: Any) -> str:
    if not messages:
        return "暂无历史对话。"

    lines: list[str] = []
    for index, message in enumerate(messages, start=1):
        if isinstance(message, dict):
            role = safe_text(message.get("role"), "unknown")
            content = safe_text(message.get("content"), "")
        else:
            role = safe_text(getattr(message, "role", "unknown"), "unknown")
            content = safe_text(getattr(message, "content", ""), "")
        lines.append(f"{index}. {role}: {content}")
    return "\n".join(lines) if lines else "暂无历史对话。"
