from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.simulation_decision import DecisionMessage, ResponsePolicy
from app.schemas.simulation_generation import GeneratedResponse
from app.schemas.simulation_state import SimulationState


EvaluationDimension = Literal[
    "persona_consistency",
    "dyadic_consistency",
    "style_consistency",
    "emotional_continuity",
    "evidence_consistency",
    "reaction_proportionality",
]
IssueSeverity = Literal["low", "medium", "high", "critical"]


class ConsistencySchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
        populate_by_name=True,
    )


class ConsistencyScores(ConsistencySchema):
    persona_consistency: float = Field(ge=0.0, le=1.0)
    dyadic_consistency: float = Field(ge=0.0, le=1.0)
    style_consistency: float = Field(ge=0.0, le=1.0)
    emotional_continuity: float = Field(ge=0.0, le=1.0)
    evidence_consistency: float = Field(ge=0.0, le=1.0)
    reaction_proportionality: float = Field(ge=0.0, le=1.0)

    def minimum(self) -> tuple[str, float]:
        values = self.model_dump()
        return min(values.items(), key=lambda item: item[1])


class ConsistencyIssue(ConsistencySchema):
    dimension: EvaluationDimension
    severity: IssueSeverity
    message: str
    retry_instruction: str = ""


class ConsistencyEvaluationInput(ConsistencySchema):
    persona: PersonaModelV2
    previous_state: SimulationState
    updated_state: SimulationState
    response_policy: ResponsePolicy
    generated_response: GeneratedResponse
    recent_turns: list[DecisionMessage] = Field(default_factory=list)
    user_message: str
    relevant_evidence: list[str] = Field(default_factory=list)
    trigger_reasons: list[str] = Field(default_factory=list)


class ConsistencyEvaluationOutput(ConsistencySchema):
    passed: bool = Field(alias="pass")
    scores: ConsistencyScores
    issues: list[ConsistencyIssue] = Field(default_factory=list)

    def retry_feedback(self) -> list[str]:
        feedback: list[str] = []
        for issue in self.issues:
            instruction = issue.retry_instruction.strip() or issue.message.strip()
            if instruction:
                feedback.append(f"{issue.dimension}: {instruction}")
        return feedback[:6]


class EvaluatorTriggerResult(ConsistencySchema):
    triggered: bool
    reasons: list[str] = Field(default_factory=list)


class SessionEvaluationMeta(ConsistencySchema):
    evaluated: bool = False
    trigger_reasons: list[str] = Field(default_factory=list)
    result: ConsistencyEvaluationOutput | None = None
    retry_count: int = Field(default=0, ge=0, le=1)
    evaluator_failed: bool = False

