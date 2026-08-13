from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import ScenarioKey
from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.simulation_state import SimulationState


class TurnStateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )


class TurnContextMessage(TurnStateSchema):
    role: Literal["user", "target", "system"]
    content: str


class TurnBehaviorSignals(TurnStateSchema):
    politeness: float = Field(ge=0.0, le=1.0)
    clarity: float = Field(ge=0.0, le=1.0)
    accountability: float = Field(ge=0.0, le=1.0)
    pressure: float = Field(ge=0.0, le=1.0)
    blame: float = Field(ge=0.0, le=1.0)
    vulnerability: float = Field(ge=0.0, le=1.0)
    boundary_violation: float = Field(ge=0.0, le=1.0)
    honesty_signal: float = Field(ge=0.0, le=1.0)


class TurnStateDelta(TurnStateSchema):
    trust: float = Field(ge=-1.0, le=1.0)
    respect: float = Field(ge=-1.0, le=1.0)
    warmth: float = Field(ge=-1.0, le=1.0)
    patience: float = Field(ge=-1.0, le=1.0)
    psychological_safety: float = Field(ge=-1.0, le=1.0)
    willingness_to_engage: float = Field(ge=-1.0, le=1.0)
    irritation: float = Field(ge=-1.0, le=1.0)
    hurt: float = Field(ge=-1.0, le=1.0)
    anxiety: float = Field(ge=-1.0, le=1.0)
    defensiveness: float = Field(ge=-1.0, le=1.0)
    fatigue: float = Field(ge=-1.0, le=1.0)
    conflict_level: float = Field(ge=-1.0, le=1.0)
    topic_resolution: float = Field(ge=-1.0, le=1.0)
    boundary_pressure: float = Field(ge=-1.0, le=1.0)


class TurnStateAnalysis(TurnStateSchema):
    """Pre-response understanding and state impact; never selects a reply action."""

    user_intent: str = Field(min_length=1, max_length=240)
    user_emotion: str = Field(min_length=1, max_length=160)
    behavior_signals: TurnBehaviorSignals
    persona_triggers: list[str] = Field(default_factory=list, max_length=6)
    detected_events: list[str] = Field(default_factory=list, max_length=8)
    risk_flags: list[str] = Field(default_factory=list, max_length=6)
    state_delta: TurnStateDelta
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("persona_triggers", "detected_events", "risk_flags")
    @classmethod
    def clean_lists(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = str(value).strip()
            if item and item not in cleaned:
                cleaned.append(item[:160])
        return cleaned


class TurnStateAnalysisRequest(TurnStateSchema):
    persona: PersonaModelV2
    current_state: SimulationState
    scenario: ScenarioKey
    goal: str
    outcome: str = ""
    recent_turns: list[TurnContextMessage] = Field(default_factory=list, max_length=8)
    relevant_evidence: list[str] = Field(default_factory=list, max_length=8)
    user_message: str = Field(min_length=1, max_length=4000)

    @field_validator("user_message")
    @classmethod
    def clean_user_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("user_message must not be blank")
        return cleaned

    @model_validator(mode="after")
    def validate_persona_consistency(self) -> "TurnStateAnalysisRequest":
        if self.current_state.persona_id != self.persona.persona_id:
            raise ValueError("current_state.persona_id must match persona.persona_id")
        return self


class TurnStateAnalysisResult(TurnStateSchema):
    analysis: TurnStateAnalysis
    updated_state: SimulationState
