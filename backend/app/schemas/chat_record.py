from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.persona_v2 import BehaviorPattern, CommunicationStyle


class ChatRecordSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class NormalizedChatMessage(ChatRecordSchema):
    message_id: str
    speaker: Literal["user", "target"]
    text: str
    original_text: str
    timestamp: str = ""
    merged_count: int = Field(default=1, ge=1)
    missing_message_before: bool = False


class ConversationEpisode(ChatRecordSchema):
    episode_id: str
    message_ids: list[str] = Field(default_factory=list)
    context: str = "general_conversation"
    user_behavior: list[str] = Field(default_factory=list)
    target_response: list[str] = Field(default_factory=list)
    outcome: str = "unresolved"


class ChatRecordFact(ChatRecordSchema):
    fact_id: str
    category: Literal[
        "identity",
        "relationship",
        "event",
        "commitment",
        "background",
    ]
    content: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ChatEvidence(ChatRecordSchema):
    evidence_id: str
    source_type: Literal["REAL_CHAT"] = "REAL_CHAT"
    content: str
    supports: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    scope: list[str] = Field(default_factory=lambda: ["chat_record"])


class RelationshipCharacteristics(ChatRecordSchema):
    user_initiative: float = Field(default=0.5, ge=0.0, le=1.0)
    target_initiative: float = Field(default=0.5, ge=0.0, le=1.0)
    target_decision_power: float = Field(default=0.5, ge=0.0, le=1.0)
    communication_distance: float = Field(default=0.5, ge=0.0, le=1.0)
    expectation: float = Field(default=0.5, ge=0.0, le=1.0)
    trust: float = Field(default=0.5, ge=0.0, le=1.0)
    warmth: float = Field(default=0.5, ge=0.0, le=1.0)
    summary: list[str] = Field(default_factory=list)


class ChatRecordAnalysis(ChatRecordSchema):
    messages: list[NormalizedChatMessage] = Field(default_factory=list)
    episodes: list[ConversationEpisode] = Field(default_factory=list)
    communication_style: CommunicationStyle
    behavior_patterns: list[BehaviorPattern] = Field(default_factory=list)
    relationship_characteristics: RelationshipCharacteristics
    facts: list[ChatRecordFact] = Field(default_factory=list)
    evidence: list[ChatEvidence] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

