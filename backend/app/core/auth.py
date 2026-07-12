from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.supabase import SupabaseConfigError, get_supabase_client


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: Optional[str] = None


async def optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthUser | None:
    if credentials is None:
        return None

    try:
        client = get_supabase_client()
    except SupabaseConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        response = client.auth.get_user(credentials.credentials)
        user = response.user
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid auth token.") from exc

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid auth token.")

    return AuthUser(id=user.id, email=user.email)


async def require_current_user(
    user: AuthUser | None = Depends(optional_current_user),
) -> AuthUser:
    if user is None:
        raise HTTPException(status_code=401, detail="Login required.")
    return user
