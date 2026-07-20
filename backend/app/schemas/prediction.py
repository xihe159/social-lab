from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import RelationshipState, ScenarioKey
from app.schemas.dynamics import ConversationDynamics, ConversationDynamicsSnapshot


PredictionDirection = Literal["positive", "negative", "mixed"]
PredictionSource = Literal[
    "scenario_prior",
    "dynamic",
    "relationship",
    "trend",
    "semantic",
    "guardrail",
]
OutcomeState = Literal[
    "accept",
    "conditional_accept",
    "hesitate",
    "refuse",
    "no_response",
    "unknown",
]
PredictionConfidence = Literal["low", "medium", "high"]
EvidenceSufficiency = Literal["insufficient", "partial", "sufficient"]


class SemanticInfluenceFactor(BaseModel):
    """
    LLM 只负责识别语义因素和证据，不直接决定最终成功率。
    """

    model_config = ConfigDict(extra="forbid")

    factor_name: str = Field(description="语义影响因素名称")
    direction: PredictionDirection
    importance: int = Field(ge=1, le=5)
    evidence_turns: list[int]
    evidence_quote: str
    explanation: str


class SemanticPredictionAssessment(BaseModel):
    """
    PredictionAgent 的 LLM 结构化输出。

    semantic_adjustment 被限制在 -8 到 +8，只能修正确定性计算无法覆盖的语义信息。
    """

    model_config = ConfigDict(extra="forbid")

    outcome_state: OutcomeState
    semantic_adjustment: int = Field(ge=-8, le=8)
    evidence_strength: float = Field(ge=0.0, le=1.0)
    likely_outcome: str
    probability_reasoning: str
    semantic_factors: list[SemanticInfluenceFactor] = Field(min_length=1, max_length=4)


class PredictionContext(BaseModel):
    """
    交给 PredictionCalculator 的稳定输入。
    与 ReportRequest 解耦，便于单元测试与离线校准。
    """

    model_config = ConfigDict(extra="forbid")

    scenario: ScenarioKey
    goal: str
    outcome: str
    relationship_state: RelationshipState
    current_dynamics: ConversationDynamics | None
    dynamics_history: list[ConversationDynamicsSnapshot]

    user_turn_count: int = Field(ge=0)
    target_turn_count: int = Field(ge=0)
    total_message_count: int = Field(ge=0)

    last_user_message: str
    last_target_message: str
    latest_user_turn_index: int = Field(ge=0)


class PredictionInfluenceFactor(BaseModel):
    """
    最终报告中的主要影响因素。

    不包含 improvement_action。改进建议只由 AnalysisAgent / RewriteAgent 输出。
    """

    model_config = ConfigDict(extra="forbid")

    factor_name: str
    direction: PredictionDirection
    importance: int = Field(ge=1, le=5)
    contribution: float = Field(ge=-100.0, le=100.0)
    source: PredictionSource

    metric_name: str | None
    metric_value: float | None
    evidence_turns: list[int]
    evidence_quote: str
    explanation: str


class OutcomeDistribution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accept: int = Field(ge=0, le=100)
    conditional_accept: int = Field(ge=0, le=100)
    hesitate: int = Field(ge=0, le=100)
    refuse: int = Field(ge=0, le=100)
    no_response: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_total(self) -> "OutcomeDistribution":
        total = (
            self.accept
            + self.conditional_accept
            + self.hesitate
            + self.refuse
            + self.no_response
        )
        if total != 100:
            raise ValueError("OutcomeDistribution values must sum to 100")
        return self


class PredictionCalculationTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_prior: float
    dynamics_contribution: float
    relationship_contribution: float
    trend_contribution: float
    semantic_adjustment: float
    pre_guardrail_score: float
    guardrail_adjustment: float
    final_score: int
    uncertainty_width: int
    volatility_score: float


class PredictionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success_probability: int = Field(ge=0, le=100)
    probability_low: int = Field(ge=0, le=100)
    probability_high: int = Field(ge=0, le=100)

    confidence_score: int = Field(ge=0, le=100)
    confidence: PredictionConfidence
    evidence_sufficiency: EvidenceSufficiency

    likely_outcome: str
    probability_reasoning: str
    outcome_state: OutcomeState
    outcome_distribution: OutcomeDistribution

    main_influence_factors: list[PredictionInfluenceFactor]
    calculation_trace: PredictionCalculationTrace
    calibration_version: str

    @model_validator(mode="after")
    def validate_interval(self) -> "PredictionResult":
        if not (
            self.probability_low
            <= self.success_probability
            <= self.probability_high
        ):
            raise ValueError(
                "success_probability must be inside probability_low/high"
            )
        return self
