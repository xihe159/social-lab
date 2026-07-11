from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.identity import validate_anonymous_user_id
from app.services.cloudbase import CloudBaseError
from app.services.persistence import get_persistence


router = APIRouter(tags=["anonymous-data"])


def _anonymous_id(user_id: str) -> str:
    return validate_anonymous_user_id(user_id)


@router.get("/api/me")
async def get_me(user_id: str = Query(...)):
    anonymous_id = _anonymous_id(user_id)
    return {
        "user_id": anonymous_id,
        "short_id": anonymous_id[-8:].upper(),
    }


@router.get("/api/personas")
async def list_personas(user_id: str = Query(...)):
    try:
        anonymous_id = _anonymous_id(user_id)
        items = get_persistence().list_personas(anonymous_id)
        return [
            {
                "id": item.get("_id") or item.get("id"),
                "scenario": item.get("scenario"),
                "role": item.get("role") or "",
                "goal": item.get("goal") or "",
                "persona": item.get("persona_json") or {},
                "created_at": item.get("created_at"),
            }
            for item in items
        ]
    except HTTPException:
        raise
    except CloudBaseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.delete("/api/personas/{persona_id}")
async def delete_persona(persona_id: str, user_id: str = Query(...)):
    try:
        anonymous_id = _anonymous_id(user_id)
        get_persistence().delete_persona(anonymous_id, persona_id)
        return {"deleted": True}
    except HTTPException:
        raise
    except CloudBaseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/api/sessions")
async def list_sessions(user_id: str = Query(...)):
    try:
        anonymous_id = _anonymous_id(user_id)
        items = get_persistence().list_sessions(anonymous_id)
        return [
            {
                "id": item.get("_id") or item.get("id"),
                "persona_id": item.get("persona_id"),
                "scenario": item.get("scenario"),
                "goal": item.get("goal") or "",
                "status": item.get("status") or "active",
                "created_at": item.get("created_at"),
                "persona_title": item.get("persona_title"),
                "latest_report_id": item.get("latest_report_id"),
            }
            for item in items
        ]
    except HTTPException:
        raise
    except CloudBaseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/api/sessions/{session_id}")
async def get_session(session_id: str, user_id: str = Query(...)):
    try:
        anonymous_id = _anonymous_id(user_id)
        item = get_persistence().get_session(anonymous_id, session_id)
        if not item:
            raise HTTPException(status_code=404, detail="Session 不存在。")
        return item
    except HTTPException:
        raise
    except CloudBaseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, user_id: str = Query(...)):
    try:
        anonymous_id = _anonymous_id(user_id)
        get_persistence().delete_session(anonymous_id, session_id)
        return {"deleted": True}
    except HTTPException:
        raise
    except CloudBaseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/api/reports/{report_id}")
async def get_report(report_id: str, user_id: str = Query(...)):
    try:
        anonymous_id = _anonymous_id(user_id)
        item = get_persistence().get_report(anonymous_id, report_id)
        if not item:
            raise HTTPException(status_code=404, detail="Report 不存在。")
        return {
            "id": item.get("_id") or item.get("id"),
            "report": item.get("report_json") or {},
        }
    except HTTPException:
        raise
    except CloudBaseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
