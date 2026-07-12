from __future__ import annotations

from typing import Any, Optional

from app.core.auth import AuthUser
from app.core.supabase import get_supabase_client
from app.schemas.common import ScenarioKey
from app.schemas.persona import Persona
from app.schemas.report import ReportResponse
from app.schemas.session import ChatMessage


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value


class PersistenceService:
    def __init__(self) -> None:
        self.client = get_supabase_client()

    def upsert_profile(self, user: AuthUser) -> None:
        self.client.table("profiles").upsert(
            {
                "id": user.id,
                "email": user.email,
            }
        ).execute()

    def save_persona(
        self,
        *,
        user: AuthUser,
        scenario: ScenarioKey,
        role: str,
        goal: str,
        persona: Persona,
    ) -> str:
        self.upsert_profile(user)
        response = (
            self.client.table("personas")
            .insert(
                {
                    "user_id": user.id,
                    "scenario": scenario,
                    "role": role,
                    "goal": goal,
                    "persona_json": persona.model_dump(),
                }
            )
            .execute()
        )
        return response.data[0]["id"]

    def create_session(
        self,
        *,
        user: AuthUser,
        scenario: ScenarioKey,
        goal: str,
        persona_id: Optional[str] = None,
        status: str = "active",
    ) -> str:
        self.upsert_profile(user)
        response = (
            self.client.table("sessions")
            .insert(
                {
                    "user_id": user.id,
                    "persona_id": persona_id,
                    "scenario": scenario,
                    "goal": goal,
                    "status": status,
                }
            )
            .execute()
        )
        return response.data[0]["id"]

    def save_message(self, *, session_id: str, role: str, content: str) -> str:
        response = (
            self.client.table("messages")
            .insert(
                {
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                }
            )
            .execute()
        )
        return response.data[0]["id"]

    def save_relationship_state(self, *, session_id: str, state: Any) -> None:
        payload = _dump(state)
        payload["session_id"] = session_id
        self.client.table("relationship_states").upsert(payload).execute()

    def save_report(self, *, session_id: str, report: Any) -> str:
        response = (
            self.client.table("reports")
            .insert(
                {
                    "session_id": session_id,
                    "report_json": _dump(report),
                }
            )
            .execute()
        )
        self.client.table("sessions").update({"status": "completed"}).eq(
            "id", session_id
        ).execute()
        return response.data[0]["id"]

    def list_personas(self, *, user: AuthUser) -> list[dict[str, Any]]:
        response = (
            self.client.table("personas")
            .select("id, scenario, role, goal, persona_json, created_at")
            .eq("user_id", user.id)
            .order("created_at", desc=True)
            .execute()
        )
        return [
            {
                "id": item["id"],
                "scenario": item["scenario"],
                "role": item.get("role") or "",
                "goal": item.get("goal") or "",
                "persona": item["persona_json"],
                "created_at": item["created_at"],
            }
            for item in response.data
        ]

    def list_sessions(self, *, user: AuthUser) -> list[dict[str, Any]]:
        response = (
            self.client.table("sessions")
            .select("id, persona_id, scenario, goal, status, created_at")
            .eq("user_id", user.id)
            .order("created_at", desc=True)
            .execute()
        )
        records: list[dict[str, Any]] = []
        for item in response.data:
            persona_title = None
            if item.get("persona_id"):
                persona_response = (
                    self.client.table("personas")
                    .select("persona_json")
                    .eq("id", item["persona_id"])
                    .eq("user_id", user.id)
                    .limit(1)
                    .execute()
                )
                if persona_response.data:
                    persona_title = persona_response.data[0]["persona_json"].get("title")

            report_response = (
                self.client.table("reports")
                .select("id")
                .eq("session_id", item["id"])
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            records.append(
                {
                    **item,
                    "persona_title": persona_title,
                    "latest_report_id": report_response.data[0]["id"]
                    if report_response.data
                    else None,
                }
            )
        return records

    def get_session_detail(self, *, user: AuthUser, session_id: str) -> dict[str, Any]:
        session_response = (
            self.client.table("sessions")
            .select("id, persona_id, scenario, goal, status, created_at")
            .eq("id", session_id)
            .eq("user_id", user.id)
            .limit(1)
            .execute()
        )
        if not session_response.data:
            raise KeyError("Session not found.")

        session = session_response.data[0]
        messages_response = (
            self.client.table("messages")
            .select("role, content, created_at")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
        report_response = (
            self.client.table("reports")
            .select("id, report_json, created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        persona = None
        persona_title = None
        if session.get("persona_id"):
            persona_response = (
                self.client.table("personas")
                .select("persona_json")
                .eq("id", session["persona_id"])
                .eq("user_id", user.id)
                .limit(1)
                .execute()
            )
            if persona_response.data:
                persona = persona_response.data[0]["persona_json"]
                persona_title = persona.get("title")

        return {
            **session,
            "persona_title": persona_title,
            "latest_report_id": report_response.data[0]["id"]
            if report_response.data
            else None,
            "messages": [
                {"role": item["role"], "content": item["content"]}
                for item in messages_response.data
            ],
            "report": report_response.data[0]["report_json"]
            if report_response.data
            else None,
            "persona": persona,
        }

    def delete_session(self, *, user: AuthUser, session_id: str) -> None:
        self.client.table("sessions").delete().eq("id", session_id).eq(
            "user_id", user.id
        ).execute()

    def delete_persona(self, *, user: AuthUser, persona_id: str) -> None:
        self.client.table("personas").delete().eq("id", persona_id).eq(
            "user_id", user.id
        ).execute()
