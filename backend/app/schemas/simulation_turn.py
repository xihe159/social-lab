from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.simulation_decision import (
    BehaviorSignals,
    DecisionAction,
    SimulationStateDelta,
)
from app.schemas.simulation_state import SimulationState


class SimulationTurnSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class SessionRuntimeMeta(SimulationTurnSchema):
    decision_fallback_used: bool = False
    generator_retry_count: int = Field(default=0, ge=0, le=1)
    generator_fallback_used: bool = False


class SafeTurnAnalysis(SimulationTurnSchema):
    intent_digest: str
    behavior_signals: BehaviorSignals
    detected_event_digests: list[str] = Field(default_factory=list)


class SimulationTurnRecord(SimulationTurnSchema):
    turn_id: str
    recorded_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    persona_id: str
    session_id: str
    user_message_digest: str
    user_message_length: int = Field(ge=0)
    state_before: SimulationState
    turn_analysis: SafeTurnAnalysis
    state_delta: SimulationStateDelta
    state_after: SimulationState
    response_action: DecisionAction
    response_text_digest: str
    response_text_length: int = Field(ge=0)
    decision_confidence: float = Field(ge=0.0, le=1.0)
    retrieved_evidence_ids: list[str] = Field(default_factory=list)
    evaluator_triggered: bool = False
    evaluator_passed: bool | None = None
    decision_fallback_used: bool = False
    generator_retry_count: int = Field(default=0, ge=0, le=1)
    generator_fallback_used: bool = False
    version: Literal["2.0"] = "2.0"
