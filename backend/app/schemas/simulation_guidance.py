from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import ScenarioKey
from app.schemas.memory import SessionMemory
from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.simulation_decision import DecisionMessage, ResponsePolicy
from app.schemas.simulation_state import SimulationState
from app.schemas.strategy import TargetResponseGuidance
from app.schemas.turn_state import TurnStateAnalysis


class SimulationGuidanceSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )


class SimulationDecisionRequest(SimulationGuidanceSchema):
    persona: PersonaModelV2
    current_state: SimulationState
    scenario: ScenarioKey
    goal: str
    outcome: str = ""
    recent_turns: list[DecisionMessage] = Field(default_factory=list, max_length=8)
    relevant_evidence: list[str] = Field(default_factory=list, max_length=8)
    session_memory: SessionMemory | None = None
    user_message: str = Field(min_length=1, max_length=4000)
    turn_state_analysis: TurnStateAnalysis
    strategy_guidance: TargetResponseGuidance

    @model_validator(mode="after")
    def validate_persona_consistency(self) -> "SimulationDecisionRequest":
        if self.current_state.persona_id != self.persona.persona_id:
            raise ValueError("current_state.persona_id must match persona.persona_id")
        return self


class SimulationDecisionOutput(SimulationGuidanceSchema):
    response_policy: ResponsePolicy
    confidence: float = Field(ge=0.0, le=1.0)
    guidance_followed: bool
    guidance_deviation_reason: str = Field(default="", max_length=300)

    @field_validator("guidance_deviation_reason")
    @classmethod
    def clean_reason(cls, value: str) -> str:
        return str(value or "").strip()[:300]

    @model_validator(mode="after")
    def deviation_requires_reason(self) -> "SimulationDecisionOutput":
        if not self.guidance_followed and not self.guidance_deviation_reason:
            self.guidance_deviation_reason = (
                "基于 Persona、关系状态或当前语义证据选择了更真实的反应。"
            )
        return self
