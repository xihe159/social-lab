from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.simulation_decision import (
    DecisionAction,
    DecisionMessage,
    ResponsePolicy,
)
from app.schemas.simulation_state import SimulationState


class GenerationSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )


class ResponseGenerationInput(GenerationSchema):
    persona: PersonaModelV2
    current_state: SimulationState
    response_policy: ResponsePolicy
    recent_turns: list[DecisionMessage] = Field(default_factory=list)
    user_message: str = Field(min_length=1)
    relevant_linguistic_evidence: list[str] = Field(default_factory=list)
    consistency_feedback: list[str] = Field(default_factory=list)
    generation_attempt: int = Field(default=1, ge=1, le=2)

    @model_validator(mode="after")
    def validate_persona_consistency(self) -> "ResponseGenerationInput":
        if self.current_state.persona_id != self.persona.persona_id:
            raise ValueError("current_state.persona_id must match persona.persona_id")
        return self


class GeneratedResponse(GenerationSchema):
    response_text: str
    response_action: DecisionAction
