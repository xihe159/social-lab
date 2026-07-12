from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.common import ScenarioKey
from app.schemas.persona import Persona
from app.schemas.session import ChatMessage


class CurrentUserResponse(BaseModel):
    id: str
    email: Optional[str] = None


class PersonaRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    scenario: ScenarioKey
    role: str = ""
    goal: str = ""
    persona: Persona
    created_at: str


class SessionRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    persona_id: Optional[str] = None
    scenario: ScenarioKey
    goal: str = ""
    status: str
    created_at: str
    persona_title: Optional[str] = None
    latest_report_id: Optional[str] = None


class SessionDetail(SessionRecord):
    messages: List[ChatMessage] = []
    report: Optional[dict] = None
    persona: Optional[Persona] = None


class PersonaSaveRequest(BaseModel):
    scenario: ScenarioKey
    role: str = ""
    goal: str = ""
    persona: Persona


class GuestRunImportRequest(BaseModel):
    scenario: ScenarioKey
    form: dict
    persona: Persona
    messages: List[ChatMessage] = []
    report: Optional[dict] = None


class GuestRunImportResponse(BaseModel):
    saved: bool
    persona_id: Optional[str] = None
    session_id: Optional[str] = None
