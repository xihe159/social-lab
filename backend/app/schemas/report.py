from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ScenarioKey
from app.schemas.dynamics import ConversationDynamics, ConversationDynamicsSnapshot
from app.schemas.persona import Persona
from app.schemas.prediction import (
    OutcomeDistribution,
    PredictionCalculationTrace,
    PredictionConfidence,
    PredictionInfluenceFactor,
    EvidenceSufficiency,
)
from app.schemas.session import ChatMessage


class ReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: ScenarioKey
    goal: str
    outcome: str = ""
    persona: Persona
    messages: list[ChatMessage]

    current_dynamics: ConversationDynamics | None = Field(
        default=None,
        description="最后一轮 StateAgent 输出的 updated_dynamics",
    )
    dynamics_history: list[ConversationDynamicsSnapshot] = Field(
        default_factory=list,
        description="最近多轮 Dynamics 快照；建议最多传 10 轮",
    )

    @property
    def user_goal(self) -> str:
        return self.goal


class ReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # 兼容当前前端的字段。
    success_probability: int = Field(
        ge=0,
        le=100,
        description="模拟成功评分，0 到 100；不是现实统计概率",
    )
    likely_outcome: str = Field(description="基于模拟的可能结果")
    strengths: list[str]
    problems: list[str]
    key_risks: list[str]
    suggested_rewrite: str
    next_step_advice: str

    # Prediction V2 新增字段。
    probability_low: int = Field(ge=0, le=100)
    probability_high: int = Field(ge=0, le=100)
    confidence_score: int = Field(ge=0, le=100)
    confidence: PredictionConfidence
    evidence_sufficiency: EvidenceSufficiency

    outcome_distribution: OutcomeDistribution
    main_influence_factors: list[PredictionInfluenceFactor]
    probability_reasoning: str
    prediction_trace: PredictionCalculationTrace
    calibration_version: str
