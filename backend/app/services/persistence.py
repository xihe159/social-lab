from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.schemas.common import ScenarioKey
from app.schemas.persona import Persona, PersonaCreateRequest
from app.schemas.report import ReportRequest, ReportResponse
from app.schemas.session import ChatMessage, SessionMessageRequest
from app.services.cloudbase import CloudBaseClient, get_cloudbase_client


COLLECTIONS = {
    "personas": "personas",
    "sessions": "sessions",
    "messages": "messages",
    "reports": "reports",
    "relationship_states": "relationship_states",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def model_to_dict(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [model_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: model_to_dict(item) for key, item in value.items()}
    return value


class AnonymousPersistence:
    def __init__(self, client: CloudBaseClient | None = None) -> None:
        self.client = client or get_cloudbase_client()

    def save_persona(
        self,
        anonymous_id: str,
        request: PersonaCreateRequest,
        persona: Persona,
    ) -> str | None:
        return self.client.add_document(
            COLLECTIONS["personas"],
            {
                "anonymous_id": anonymous_id,
                "scenario": request.scenario,
                "role": request.role,
                "goal": request.goal,
                "persona_json": model_to_dict(persona),
                "created_at": utc_now(),
            },
        )

    def ensure_session(
        self,
        anonymous_id: str,
        *,
        scenario: ScenarioKey,
        goal: str,
        persona_id: str | None = None,
        session_id: str | None = None,
    ) -> str | None:
        if session_id:
            existing = self.client.get_document(COLLECTIONS["sessions"], session_id)
            if existing and existing.get("anonymous_id") == anonymous_id:
                return session_id

        return self.client.add_document(
            COLLECTIONS["sessions"],
            {
                "anonymous_id": anonymous_id,
                "persona_id": persona_id,
                "scenario": scenario,
                "goal": goal,
                "status": "active",
                "created_at": utc_now(),
            },
        )

    def save_message(
        self,
        anonymous_id: str,
        session_id: str,
        message: ChatMessage,
    ) -> None:
        self.client.add_document(
            COLLECTIONS["messages"],
            {
                "anonymous_id": anonymous_id,
                "session_id": session_id,
                "role": message.role,
                "content": message.content,
                "created_at": utc_now(),
            },
        )

    def save_relationship_state(
        self,
        anonymous_id: str,
        session_id: str,
        state: dict[str, Any],
    ) -> None:
        self.client.update_document(
            COLLECTIONS["relationship_states"],
            {"_id": session_id},
            {
                "anonymous_id": anonymous_id,
                "session_id": session_id,
                **state,
                "updated_at": utc_now(),
            },
            upsert=True,
            replace=True,
        )

    def save_report(
        self,
        anonymous_id: str,
        session_id: str,
        report: ReportResponse,
    ) -> str | None:
        report_id = self.client.add_document(
            COLLECTIONS["reports"],
            {
                "anonymous_id": anonymous_id,
                "session_id": session_id,
                "report_json": model_to_dict(report),
                "created_at": utc_now(),
            },
        )
        self.client.update_document(
            COLLECTIONS["sessions"],
            {"_id": session_id, "anonymous_id": anonymous_id},
            {"status": "completed"},
            multi=False,
        )
        return report_id

    def list_personas(self, anonymous_id: str) -> list[dict[str, Any]]:
        return self.client.query_documents(
            COLLECTIONS["personas"],
            {"anonymous_id": anonymous_id},
            order=[{"field": "created_at", "direction": "desc"}],
            limit=100,
        )

    def list_sessions(self, anonymous_id: str) -> list[dict[str, Any]]:
        sessions = self.client.query_documents(
            COLLECTIONS["sessions"],
            {"anonymous_id": anonymous_id},
            order=[{"field": "created_at", "direction": "desc"}],
            limit=100,
        )
        for session in sessions:
            session_id = session.get("_id") or session.get("id")
            reports = self.client.query_documents(
                COLLECTIONS["reports"],
                {"anonymous_id": anonymous_id, "session_id": session_id},
                order=[{"field": "created_at", "direction": "desc"}],
                limit=1,
            )
            session["latest_report_id"] = (
                reports[0].get("_id") or reports[0].get("id") if reports else None
            )
            persona_id = session.get("persona_id")
            if persona_id:
                persona = self.client.get_document(COLLECTIONS["personas"], persona_id)
                if persona and persona.get("anonymous_id") == anonymous_id:
                    persona_json = persona.get("persona_json") or {}
                    session["persona_title"] = persona_json.get("title")
        return sessions

    def get_session(self, anonymous_id: str, session_id: str) -> dict[str, Any] | None:
        session = self.client.get_document(COLLECTIONS["sessions"], session_id)
        if not session or session.get("anonymous_id") != anonymous_id:
            return None
        messages = self.client.query_documents(
            COLLECTIONS["messages"],
            {"anonymous_id": anonymous_id, "session_id": session_id},
            order=[{"field": "created_at", "direction": "asc"}],
            limit=200,
        )
        session["messages"] = messages
        return session

    def get_report(self, anonymous_id: str, report_id: str) -> dict[str, Any] | None:
        report = self.client.get_document(COLLECTIONS["reports"], report_id)
        if not report or report.get("anonymous_id") != anonymous_id:
            return None
        return report

    def delete_session(self, anonymous_id: str, session_id: str) -> None:
        self.client.remove_documents(
            COLLECTIONS["messages"],
            {"anonymous_id": anonymous_id, "session_id": session_id},
        )
        self.client.remove_documents(
            COLLECTIONS["reports"],
            {"anonymous_id": anonymous_id, "session_id": session_id},
        )
        self.client.remove_documents(
            COLLECTIONS["relationship_states"],
            {"anonymous_id": anonymous_id, "session_id": session_id},
        )
        self.client.remove_documents(
            COLLECTIONS["sessions"],
            {"anonymous_id": anonymous_id, "_id": session_id},
            multi=False,
        )

    def delete_persona(self, anonymous_id: str, persona_id: str) -> None:
        self.client.remove_documents(
            COLLECTIONS["personas"],
            {"anonymous_id": anonymous_id, "_id": persona_id},
            multi=False,
        )


def get_persistence() -> AnonymousPersistence:
    return AnonymousPersistence()
