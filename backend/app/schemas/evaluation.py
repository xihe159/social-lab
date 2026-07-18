from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.memory import SessionMemory
from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.simulation_state import RelationshipStateV2
from app.schemas.strategy import StrategyMessage, TargetResponsePolicy
from app.schemas.feedback import InternalCorrection
from app.schemas.runtime_metrics import EvaluationRunMode


class EvaluationSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )


class EvaluationVerdict(str, Enum):
    ACCEPT = "accept"
    ACCEPT_WITH_FEEDBACK = "accept_with_feedback"
    REVISE_SIMULATION = "revise_simulation"
    REPLAN_AND_REGENERATE = "replan_and_regenerate"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class FailureAttribution(str, Enum):
    NONE = "none"
    STRATEGY_ERROR = "strategy_error"
    SIMULATION_EXECUTION_ERROR = "simulation_execution_error"
    CONTEXT_GAP = "context_gap"
    MIXED = "mixed"


class FeedbackAction(str, Enum):
    NONE = "none"
    REVISE_SIMULATION = "revise_simulation"
    REPLAN_AND_REGENERATE = "replan_and_regenerate"


class SimulationEvaluationResult(EvaluationSchema):
    """The generated target-person reaction evaluated by EvaluationAgent V2."""

    reply: str
    attitude: str
    emotion: str
    perceived_user_tone: str
    state_delta: dict[str, float | int]
    risk_flags: list[str]
    policy_id: str
    used_evidence_refs: list[str]

    @field_validator("risk_flags", "used_evidence_refs")
    @classmethod
    def keep_lists_bounded(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = str(value).strip()
            if item and item not in cleaned:
                cleaned.append(item[:240])
        return cleaned[:12]


class SimulationEvaluationRequest(EvaluationSchema):
    """Independent V2 quality evaluation input; not part of the chat hot path."""

    trace_id: str = Field(min_length=1, max_length=120)
    session_id: str = Field(min_length=1, max_length=120)
    turn_id: str = Field(min_length=1, max_length=120)

    persona_snapshot: PersonaModelV2
    relationship_state_before: RelationshipStateV2
    session_memory: SessionMemory

    recent_messages: list[StrategyMessage] = Field(max_length=12)
    user_message: str = Field(min_length=1, max_length=4000)

    response_policy: TargetResponsePolicy
    simulation_result: SimulationEvaluationResult

    strategy_prompt_version: str = Field(min_length=1, max_length=120)
    simulation_prompt_version: str = Field(min_length=1, max_length=120)
    evaluation_prompt_version: str = Field(min_length=1, max_length=120)

    @field_validator("user_message")
    @classmethod
    def user_message_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("user_message must not be blank")
        return cleaned


class EvaluationScoreItem(EvaluationSchema):
    score: int = Field(ge=0, le=100)
    reason: str
    evidence: list[str]


class SimulationEvaluationResponse(EvaluationSchema):
    """Evaluation output for target-person simulation fidelity."""

    evaluation_id: str

    simulation_success_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)
    verdict: EvaluationVerdict
    failure_attribution: FailureAttribution

    persona_fidelity: EvaluationScoreItem
    dyadic_consistency: EvaluationScoreItem
    state_continuity: EvaluationScoreItem
    strategy_adherence: EvaluationScoreItem
    reaction_plausibility: EvaluationScoreItem
    style_fidelity: EvaluationScoreItem
    evidence_grounding: EvaluationScoreItem

    critical_issues: list[str]
    correction_for_strategy: InternalCorrection | None
    correction_for_simulation: InternalCorrection | None
    session_learning_signals: list[str]
    evaluator_notes: list[str]


class SessionEvaluationMeta(EvaluationSchema):
    """Safe feedback-loop metadata returned by the user-facing session API."""

    evaluated: bool = False
    execution_mode: EvaluationRunMode = "not_run"
    background_scheduled: bool = False
    critical_reasons: list[str] = Field(default_factory=list, max_length=8)
    initial_evaluation_id: str | None = None
    final_evaluation_id: str | None = None
    initial_score: int | None = Field(default=None, ge=0, le=100)
    final_score: int | None = Field(default=None, ge=0, le=100)
    score_delta: int | None = Field(default=None, ge=-100, le=100)
    initial_verdict: EvaluationVerdict | None = None
    final_verdict: EvaluationVerdict | None = None
    initial_failure_attribution: FailureAttribution | None = None
    final_failure_attribution: FailureAttribution | None = None
    feedback_action: FeedbackAction = FeedbackAction.NONE
    retry_count: int = Field(default=0, ge=0, le=1)
    correction_applied: bool = False
    evaluator_failed: bool = False
    final_evaluator_failed: bool = False
