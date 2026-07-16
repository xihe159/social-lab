from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


UnitScore = float
ReplyLength = Literal["short", "medium", "long"]


class PersonaV2Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )


class BasicProfile(PersonaV2Schema):
    name: str = ""
    role: str = ""
    age_range: str = ""
    relationship_type: str = ""
    relationship_duration: str = ""
    power_dynamic: str = ""


class StableTraits(PersonaV2Schema):
    directness: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    emotional_expressiveness: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    conflict_avoidance: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    need_for_control: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    tolerance_for_ambiguity: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    sensitivity_to_disrespect: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    sensitivity_to_rejection: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    patience_for_explanation: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    preference_for_efficiency: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    need_for_reassurance: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    boundary_strictness: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    forgiveness_speed: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    responsibility_orientation: UnitScore = Field(default=0.5, ge=0.0, le=1.0)


class CommunicationStyle(PersonaV2Schema):
    average_reply_length: ReplyLength = "medium"
    formality: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    emoji_frequency: UnitScore = Field(default=0.0, ge=0.0, le=1.0)
    question_frequency: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    uses_periods: bool = True
    uses_multiple_messages: bool = False
    typical_openings: list[str] = Field(default_factory=list)
    typical_closings: list[str] = Field(default_factory=list)
    preferred_sentence_patterns: list[str] = Field(default_factory=list)


class DyadicProfile(PersonaV2Schema):
    """Relatively stable characteristics of this person toward this user."""

    trust: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    respect: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    warmth: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    expectation: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    patience: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    psychological_safety: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    communication_distance: UnitScore = Field(default=0.5, ge=0.0, le=1.0)


class BehaviorTrigger(PersonaV2Schema):
    user_behavior: list[str] = Field(default_factory=list)
    context: list[str] = Field(default_factory=list)


class ObservedResponse(PersonaV2Schema):
    reply_length_change: str = "unchanged"
    warmth_change: str = "unchanged"
    directness_change: str = "unchanged"


class BehaviorPattern(PersonaV2Schema):
    pattern_id: str
    trigger: BehaviorTrigger = Field(default_factory=BehaviorTrigger)
    observed_response: ObservedResponse = Field(default_factory=ObservedResponse)
    inferred_tendency: str = ""
    confidence: UnitScore = Field(default=0.5, ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)
    counter_evidence_ids: list[str] = Field(default_factory=list)


class EvidenceSummary(PersonaV2Schema):
    evidence_count: int = Field(default=0, ge=0)
    chat_record_available: bool = False
    overall_confidence: UnitScore = Field(default=0.4, ge=0.0, le=1.0)


class PersonaModelV2(PersonaV2Schema):
    persona_id: str = Field(min_length=1)
    basic_profile: BasicProfile = Field(default_factory=BasicProfile)
    stable_traits: StableTraits = Field(default_factory=StableTraits)
    communication_style: CommunicationStyle = Field(default_factory=CommunicationStyle)
    dyadic_profile: DyadicProfile = Field(default_factory=DyadicProfile)
    behavior_patterns: list[BehaviorPattern] = Field(default_factory=list)
    evidence_summary: EvidenceSummary = Field(default_factory=EvidenceSummary)
    version: Literal["2.0"] = "2.0"
