from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthUser, require_current_user
from app.core.supabase import SupabaseConfigError, get_supabase_client
from app.schemas.persistence import (
    CurrentUserResponse,
    GuestRunImportRequest,
    GuestRunImportResponse,
    PersonaRecord,
    PersonaSaveRequest,
    SessionDetail,
    SessionRecord,
)
from app.services.persistence import PersistenceService


router = APIRouter(tags=["user-data"])


def get_persistence() -> PersistenceService:
    return PersistenceService()


@router.get("/api/me", response_model=CurrentUserResponse)
async def get_me(user: AuthUser = Depends(require_current_user)):
    return CurrentUserResponse(id=user.id, email=user.email)


@router.get("/api/debug/supabase", response_model=dict)
async def debug_supabase():
    url_configured = bool(os.getenv("SUPABASE_URL"))
    service_key_configured = bool(os.getenv("SUPABASE_SERVICE_KEY"))

    if not url_configured or not service_key_configured:
        return {
            "ok": False,
            "configured": {
                "SUPABASE_URL": url_configured,
                "SUPABASE_SERVICE_KEY": service_key_configured,
            },
            "database": "not_checked",
        }

    try:
        client = get_supabase_client()
        client.table("profiles").select("id").limit(1).execute()
        return {
            "ok": True,
            "configured": {
                "SUPABASE_URL": True,
                "SUPABASE_SERVICE_KEY": True,
            },
            "database": "connected",
        }
    except SupabaseConfigError as exc:
        return {
            "ok": False,
            "configured": {
                "SUPABASE_URL": url_configured,
                "SUPABASE_SERVICE_KEY": service_key_configured,
            },
            "database": "not_checked",
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "ok": False,
            "configured": {
                "SUPABASE_URL": True,
                "SUPABASE_SERVICE_KEY": True,
            },
            "database": "error",
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }


@router.get("/api/personas", response_model=list[PersonaRecord])
async def list_personas(
    user: AuthUser = Depends(require_current_user),
    store: PersistenceService = Depends(get_persistence),
):
    return store.list_personas(user=user)


@router.post("/api/personas/save", response_model=dict)
async def save_persona(
    request: PersonaSaveRequest,
    user: AuthUser = Depends(require_current_user),
    store: PersistenceService = Depends(get_persistence),
):
    persona_id = store.save_persona(
        user=user,
        scenario=request.scenario,
        role=request.role,
        goal=request.goal,
        persona=request.persona,
    )
    return {"saved": True, "persona_id": persona_id}


@router.delete("/api/personas/{persona_id}", response_model=dict)
async def delete_persona(
    persona_id: str,
    user: AuthUser = Depends(require_current_user),
    store: PersistenceService = Depends(get_persistence),
):
    store.delete_persona(user=user, persona_id=persona_id)
    return {"ok": True}


@router.get("/api/sessions", response_model=list[SessionRecord])
async def list_sessions(
    user: AuthUser = Depends(require_current_user),
    store: PersistenceService = Depends(get_persistence),
):
    return store.list_sessions(user=user)


@router.post("/api/sessions", response_model=dict)
async def create_session(
    payload: dict,
    user: AuthUser = Depends(require_current_user),
    store: PersistenceService = Depends(get_persistence),
):
    session_id = store.create_session(
        user=user,
        scenario=payload["scenario"],
        goal=payload.get("goal", ""),
        persona_id=payload.get("persona_id"),
    )
    return {"saved": True, "session_id": session_id}


@router.get("/api/sessions/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: str,
    user: AuthUser = Depends(require_current_user),
    store: PersistenceService = Depends(get_persistence),
):
    try:
        return store.get_session_detail(user=user, session_id=session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found.") from exc


@router.delete("/api/sessions/{session_id}", response_model=dict)
async def delete_session(
    session_id: str,
    user: AuthUser = Depends(require_current_user),
    store: PersistenceService = Depends(get_persistence),
):
    store.delete_session(user=user, session_id=session_id)
    return {"ok": True}


@router.get("/api/reports/{report_id}", response_model=dict)
async def get_report(
    report_id: str,
    user: AuthUser = Depends(require_current_user),
    store: PersistenceService = Depends(get_persistence),
):
    response = (
        store.client.table("reports")
        .select("id, report_json, sessions!inner(user_id)")
        .eq("id", report_id)
        .eq("sessions.user_id", user.id)
        .limit(1)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Report not found.")
    return {"id": response.data[0]["id"], "report": response.data[0]["report_json"]}


@router.post("/api/guest-runs/import", response_model=GuestRunImportResponse)
async def import_guest_run(
    request: GuestRunImportRequest,
    user: AuthUser = Depends(require_current_user),
    store: PersistenceService = Depends(get_persistence),
):
    form = request.form
    persona_id = store.save_persona(
        user=user,
        scenario=request.scenario,
        role=str(form.get("role", "")),
        goal=str(form.get("goal", "")),
        persona=request.persona,
    )
    session_id = store.create_session(
        user=user,
        scenario=request.scenario,
        goal=str(form.get("goal", "")),
        persona_id=persona_id,
        status="completed" if request.report else "active",
    )

    for message in request.messages:
        store.save_message(
            session_id=session_id,
            role=message.role,
            content=message.content,
        )

    store.save_relationship_state(session_id=session_id, state=request.persona.state)

    if request.report:
        store.save_report(session_id=session_id, report=request.report)

    return GuestRunImportResponse(
        saved=True,
        persona_id=persona_id,
        session_id=session_id,
    )
