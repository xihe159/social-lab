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
from app.schemas.runtime_metrics import EvaluationRunMode


class SimulationTurnSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class SessionRuntimeMeta(SimulationTurnSchema):
    decision_fallback_used: bool = False
    strategy_fallback_used: bool = False
    generator_retry_count: int = Field(default=0, ge=0, le=1)
    generator_fallback_used: bool = False
    evaluation_call_count: int = Field(default=0, ge=0, le=2)
    feedback_retry_count: int = Field(default=0, ge=0, le=1)
    strategy_replan_count: int = Field(default=0, ge=0, le=1)
    simulation_revision_count: int = Field(default=0, ge=0, le=1)
    rejected_candidate_discarded: bool = False


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
    evaluation_execution_mode: EvaluationRunMode = "not_run"
    background_evaluation_scheduled: bool = False
    evaluation_critical_reasons: list[str] = Field(default_factory=list, max_length=8)
    evaluator_passed: bool | None = None
    initial_evaluation_score: int | None = Field(default=None, ge=0, le=100)
    final_evaluation_score: int | None = Field(default=None, ge=0, le=100)
    evaluation_verdict: str | None = None
    failure_attribution: str | None = None
    feedback_action: str = "none"
    feedback_retry_count: int = Field(default=0, ge=0, le=1)
    rejected_candidate_discarded: bool = False
    adjustment_applied: bool = False
    adjustment_activated: bool = False
    adjustment_style_count: int = Field(default=0, ge=0, le=8)
    adjustment_strategy_count: int = Field(default=0, ge=0, le=8)
    adjustment_remaining_turns: int = Field(default=0, ge=0, le=10)
    decision_fallback_used: bool = False
    strategy_fallback_used: bool = False
    generator_retry_count: int = Field(default=0, ge=0, le=1)
    generator_fallback_used: bool = False
    version: Literal["2.0"] = "2.0"
