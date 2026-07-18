from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import ScenarioKey
from app.schemas.feedback import InternalCorrection
from app.schemas.memory import SessionMemory
from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.simulation_state import RelationshipStateV2
from app.schemas.simulation_adjustment import SimulationAdjustmentProfile


class StrategySchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )


class ResponseAction(str, Enum):
    ANSWER = "answer"
    ACKNOWLEDGE = "acknowledge"
    ASK_CLARIFICATION = "ask_clarification"
    ACCEPT = "accept"
    ACCEPT_WITH_CONDITION = "accept_with_condition"
    PARTIAL_ACCEPT = "partial_accept"
    REFUSE = "refuse"
    CHALLENGE = "challenge"
    SET_BOUNDARY = "set_boundary"
    DEFER = "defer"
    NO_REPLY = "no_reply"
    END_CONVERSATION = "end_conversation"


class StrategyMessage(StrategySchema):
    role: Literal["user", "target", "system"]
    content: str


class TargetInterpretation(StrategySchema):
    perceived_intent: str = Field(min_length=1, max_length=160)
    perceived_tone: str = Field(min_length=1, max_length=120)
    salient_point: str = Field(min_length=1, max_length=200)
    perceived_concern: str = Field(min_length=1, max_length=200)


class ToneProfile(StrategySchema):
    warmth: int = Field(ge=0, le=100)
    directness: int = Field(ge=0, le=100)
    formality: int = Field(ge=0, le=100)
    emotional_intensity: int = Field(ge=0, le=100)
    length: Literal["very_short", "short", "medium"]


class TargetResponsePolicy(StrategySchema):
    """Internal target-person policy. It never contains user-facing advice."""

    policy_id: str = Field(min_length=1, max_length=120)
    interpretation: TargetInterpretation
    action: ResponseAction
    response_goal: str = Field(min_length=1, max_length=240)
    stance: str = Field(min_length=1, max_length=160)
    required_content: list[str]
    forbidden_content: list[str]
    tone_profile: ToneProfile
    persona_evidence_refs: list[str]
    memory_evidence_refs: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty_notes: list[str]

    @field_validator(
        "required_content",
        "forbidden_content",
        "persona_evidence_refs",
        "memory_evidence_refs",
        "uncertainty_notes",
    )
    @classmethod
    def keep_lists_bounded(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = str(value).strip()
            if item and item not in cleaned:
                cleaned.append(item[:200])
        return cleaned[:8]


class TargetResponseStrategyRequest(StrategySchema):
    trace_id: str = Field(min_length=1, max_length=120)
    session_id: str = Field(min_length=1, max_length=120)
    turn_id: str = Field(min_length=1, max_length=120)

    scenario: ScenarioKey
    user_goal: str | None = Field(default=None, max_length=500)

    persona_snapshot: PersonaModelV2
    relationship_state: RelationshipStateV2
    session_memory: SessionMemory | None = None

    recent_messages: list[StrategyMessage] = Field(default_factory=list, max_length=6)
    user_message: str = Field(min_length=1, max_length=4000)

    evaluation_correction: InternalCorrection | None = Field(
        default=None,
        description="阶段 4 单次 Strategy 重规划的内部修正约束。",
    )

    simulation_adjustments: SimulationAdjustmentProfile | None = Field(
        default=None,
        description="Evaluation 连续识别后生成的会话内短期修正；不属于 Persona。",
    )

    @field_validator("user_message")
    @classmethod
    def clean_user_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("user_message must not be blank")
        return cleaned
