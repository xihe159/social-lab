from __future__ import annotations

import re

from fastapi import HTTPException


ANONYMOUS_ID_PATTERN = re.compile(r"^sl_anon_[0-9a-fA-F-]{32,80}$")


def validate_anonymous_user_id(user_id: str) -> str:
    normalized = (user_id or "").strip()
    if not ANONYMOUS_ID_PATTERN.match(normalized):
        raise HTTPException(
            status_code=400,
            detail="user_id 必须是前端生成的匿名 ID，格式为 sl_anon_<uuid>。",
        )
    return normalized
