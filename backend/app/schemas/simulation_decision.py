from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import ScenarioKey
from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.simulation_state import SimulationState


ResponseAction = Literal[
    "REPLY_NORMAL",
    "REPLY_BRIEF",
    "REPLY_COLD",
    "ASK_CLARIFICATION",
    "SET_BOUNDARY",
    "CONFRONT",
    "DEFER_REPLY",
    "READ_NO_REPLY",
    "END_CONVERSATION",
]
DecisionAction = ResponseAction
ReplyLength = Literal["short", "medium", "long"]


class DecisionSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )


class DecisionMessage(DecisionSchema):
    role: Literal["user", "target", "system"]
    content: str


class TurnDecisionInput(DecisionSchema):
    persona: PersonaModelV2
    current_state: SimulationState
    scenario: ScenarioKey
    goal: str
    outcome: str = ""
    recent_turns: list[DecisionMessage] = Field(default_factory=list)
    relevant_evidence: list[str] = Field(default_factory=list)
    user_message: str = Field(min_length=1)

    @field_validator("user_message")
    @classmethod
    def validate_user_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("user_message must not be blank")
        return cleaned

    @model_validator(mode="after")
    def validate_persona_consistency(self) -> "TurnDecisionInput":
        if self.current_state.persona_id != self.persona.persona_id:
            raise ValueError("current_state.persona_id must match persona.persona_id")
        return self


class BehaviorSignals(DecisionSchema):
    politeness: float = Field(ge=0.0, le=1.0)
    clarity: float = Field(ge=0.0, le=1.0)
    accountability: float = Field(ge=0.0, le=1.0)
    pressure: float = Field(ge=0.0, le=1.0)
    blame: float = Field(ge=0.0, le=1.0)
    vulnerability: float = Field(ge=0.0, le=1.0)
    boundary_violation: float = Field(ge=0.0, le=1.0)
    honesty_signal: float = Field(ge=0.0, le=1.0)


class TurnAnalysis(DecisionSchema):
    intent: str
    behavior_signals: BehaviorSignals
    detected_events: list[str]


class SimulationStateDelta(DecisionSchema):
    """Raw LLM delta; backend post-processing applies the tighter turn limit."""

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


class ResponsePolicy(DecisionSchema):
    action: ResponseAction
    content_goals: list[str]
    tone: str
    reply_length: ReplyLength
    must_avoid: list[str]


class TurnDecisionOutput(DecisionSchema):
    turn_analysis: TurnAnalysis
    state_delta: SimulationStateDelta
    response_policy: ResponsePolicy
    confidence: float = Field(ge=0.0, le=1.0)


class TurnDecisionResult(DecisionSchema):
    decision: TurnDecisionOutput
    updated_state: SimulationState
