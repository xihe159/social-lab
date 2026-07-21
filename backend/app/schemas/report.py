from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.analysis import (
    ConversationProcessAnalysis,
    ConversationTurnTrace,
)
from app.schemas.common import ScenarioKey
from app.schemas.dynamics import (
    ConversationDynamics,
    ConversationDynamicsSnapshot,
)
from app.schemas.persona import Persona
from app.schemas.prediction import (
    EvidenceSufficiency,
    OutcomeDistribution,
    PredictionCalculationTrace,
    PredictionConfidence,
    PredictionInfluenceFactor,
)
from app.schemas.rewrite import (
    RewriteVariants,
    SentenceRewrite,
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
    turn_traces: list[ConversationTurnTrace] = Field(
        default_factory=list,
        description=(
            "每轮 SessionMessageResponse 形成的关系状态和 Dynamics 轨迹。"
            "AnalysisAgent 使用它进行可审计的逐句状态归因。"
        ),
    )

    @property
    def user_goal(self) -> str:
        return self.goal


class ReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Prediction V2
    success_probability: int = Field(
        ge=0,
        le=100,
        description="模拟成功评分，0 到 100；不是现实统计概率",
    )
    probability_low: int = Field(ge=0, le=100)
    probability_high: int = Field(ge=0, le=100)
    confidence_score: int = Field(ge=0, le=100)
    confidence: PredictionConfidence
    evidence_sufficiency: EvidenceSufficiency

    likely_outcome: str
    probability_reasoning: str
    outcome_distribution: OutcomeDistribution
    main_influence_factors: list[PredictionInfluenceFactor]
    prediction_trace: PredictionCalculationTrace
    calibration_version: str

    # AnalysisAgent：观察与评价，不包含任何改进建议。
    conversation_analysis: ConversationProcessAnalysis
    strengths: list[str]
    problems: list[str]
    key_risks: list[str]

    # RewriteAgent：所有逐句改写、整体改写和下一步集中在这里。
    suggested_rewrite: str
    sentence_rewrites: list[SentenceRewrite]
    rewrite_variants: RewriteVariants
    next_step_advice: str
    do_not_say: list[str]
