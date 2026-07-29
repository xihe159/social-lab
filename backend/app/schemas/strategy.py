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
from app.schemas.turn_state import TurnStateAnalysis


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


class ResponseMode(str, Enum):
    ENGAGE = "engage"
    SEEK_INFORMATION = "seek_information"
    CONDITIONAL_SUPPORT = "conditional_support"
    LIMITED_SUPPORT = "limited_support"
    DECLINE = "decline"
    SET_BOUNDARY = "set_boundary"
    CHALLENGE = "challenge"
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
    length: Literal["very_short", "short", "medium", "long"]


class ResponseModeHypothesis(StrategySchema):
    mode: ResponseMode
    probability: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=240)


class ToneRange(StrategySchema):
    warmth_min: int = Field(ge=0, le=100)
    warmth_max: int = Field(ge=0, le=100)
    directness_min: int = Field(ge=0, le=100)
    directness_max: int = Field(ge=0, le=100)
    formality: int = Field(ge=0, le=100)
    emotional_intensity_max: int = Field(ge=0, le=100)
    preferred_length: Literal["very_short", "short", "medium", "long"]

    @field_validator("warmth_max")
    @classmethod
    def warmth_range_must_be_valid(cls, value: int, info) -> int:
        minimum = info.data.get("warmth_min")
        if minimum is not None and value < minimum:
            raise ValueError("warmth_max must be >= warmth_min")
        return value

    @field_validator("directness_max")
    @classmethod
    def directness_range_must_be_valid(cls, value: int, info) -> int:
        minimum = info.data.get("directness_min")
        if minimum is not None and value < minimum:
            raise ValueError("directness_max must be >= directness_min")
        return value


class TargetResponseGuidance(StrategySchema):
    """Advisory response hypotheses. Simulation retains final decision authority."""

    guidance_id: str = Field(min_length=1, max_length=120)
    interpretation: TargetInterpretation
    possible_response_modes: list[ResponseModeHypothesis] = Field(
        min_length=1,
        max_length=3,
    )
    recommended_mode: ResponseMode
    communication_goal: str = Field(min_length=1, max_length=240)
    required_content: list[str]
    forbidden_content: list[str]
    tone_range: ToneRange
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
    def keep_guidance_lists_bounded(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = str(value).strip()
            if item and item not in cleaned:
                cleaned.append(item[:200])
        return cleaned[:8]

    @field_validator("possible_response_modes")
    @classmethod
    def normalize_probabilities(
        cls,
        values: list[ResponseModeHypothesis],
    ) -> list[ResponseModeHypothesis]:
        total = sum(item.probability for item in values)
        if total <= 0:
            even = round(1 / len(values), 4)
            for item in values:
                item.probability = even
        else:
            normalized = [
                round(item.probability / total, 4)
                for item in values
            ]
            normalized[-1] = round(
                1.0 - sum(normalized[:-1]),
                4,
            )
            for item, probability in zip(values, normalized, strict=True):
                item.probability = probability
        return values

    @field_validator("recommended_mode")
    @classmethod
    def recommended_mode_must_be_listed(cls, value: ResponseMode, info):
        hypotheses = info.data.get("possible_response_modes") or []
        if hypotheses and value not in {item.mode for item in hypotheses}:
            raise ValueError("recommended_mode must appear in possible_response_modes")
        return value


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
    turn_state_analysis: TurnStateAnalysis | None = None

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
