from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


UnitScore = float


class SimulationStateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )


class RelationshipStateV2(SimulationStateSchema):
    trust: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    respect: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    warmth: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    patience: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    psychological_safety: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    willingness_to_engage: UnitScore = Field(default=0.5, ge=0.0, le=1.0)


class EmotionalState(SimulationStateSchema):
    irritation: UnitScore = Field(default=0.0, ge=0.0, le=1.0)
    hurt: UnitScore = Field(default=0.0, ge=0.0, le=1.0)
    anxiety: UnitScore = Field(default=0.0, ge=0.0, le=1.0)
    defensiveness: UnitScore = Field(default=0.0, ge=0.0, le=1.0)
    fatigue: UnitScore = Field(default=0.0, ge=0.0, le=1.0)


class ConversationState(SimulationStateSchema):
    turn_count: int = Field(default=0, ge=0)
    conflict_level: UnitScore = Field(default=0.0, ge=0.0, le=1.0)
    topic_resolution: UnitScore = Field(default=0.0, ge=0.0, le=1.0)
    boundary_pressure: UnitScore = Field(default=0.0, ge=0.0, le=1.0)


class SimulationState(SimulationStateSchema):
    session_id: str = Field(min_length=1)
    persona_id: str = Field(min_length=1)
    relationship_state: RelationshipStateV2 = Field(
        default_factory=RelationshipStateV2
    )
    emotional_state: EmotionalState = Field(default_factory=EmotionalState)
    conversation_state: ConversationState = Field(default_factory=ConversationState)
    version: Literal["2.0"] = "2.0"
