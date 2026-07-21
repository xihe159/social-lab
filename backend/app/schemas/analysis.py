from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import RelationshipState
from app.schemas.dynamics import (
    ConversationDynamics,
    ConversationDynamicsDelta,
)
from app.schemas.session import StateDelta


CommunicativeFunction = Literal[
    "context",
    "request",
    "question",
    "explanation",
    "apology",
    "commitment",
    "boundary",
    "emotion",
    "pressure",
    "response",
    "other",
]

SentenceEvaluationLabel = Literal[
    "strong",
    "effective",
    "neutral",
    "risky",
    "damaging",
]

GoalEffect = Literal["supports", "neutral", "obstructs"]

TargetFeeling = Literal[
    "reassured",
    "respected",
    "understood",
    "neutral",
    "uncertain",
    "burdened",
    "pressured",
    "defensive",
    "hurt",
    "withdrawn",
]

StateChangeSource = Literal[
    "turn_delta_attribution",
    "unavailable",
]


class RelationshipSignalVector(BaseModel):
    """
    LLM 对句子影响方向和强度的语义判断。

    它不是最终状态增量。SentenceAnalysisAllocator 会将整轮真实增量
    按该向量归因到各句，并确保句级增量之和等于整轮增量。
    """

    model_config = ConfigDict(extra="forbid")

    trust: int = Field(ge=-5, le=5)
    respect: int = Field(ge=-5, le=5)
    familiarity: int = Field(ge=-5, le=5)
    affinity: int = Field(ge=-5, le=5)
    authority: int = Field(ge=-5, le=5)
    emotional: int = Field(ge=-5, le=5)


class DynamicsSignalVector(BaseModel):
    """
    LLM 对句子影响 Dynamics 的方向和强度判断。

    pressure_level 的正数表示压力上升，其他指标正数通常表示改善。
    """

    model_config = ConfigDict(extra="forbid")

    atmosphere_score: int = Field(ge=-5, le=5)
    pace_score: int = Field(ge=-5, le=5)
    pressure_level: int = Field(ge=-5, le=5)
    clarity_score: int = Field(ge=-5, le=5)
    responsiveness_score: int = Field(ge=-5, le=5)
    progress_score: int = Field(ge=-5, le=5)
    repairability_score: int = Field(ge=-5, le=5)
    boundary_score: int = Field(ge=-5, le=5)


class ConversationEvaluationScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clarity: int = Field(ge=0, le=100)
    responsiveness: int = Field(ge=0, le=100)
    respect_and_boundary: int = Field(ge=0, le=100)
    responsibility: int = Field(ge=0, le=100)
    emotional_safety: int = Field(ge=0, le=100)
    goal_alignment: int = Field(ge=0, le=100)
    overall: int = Field(ge=0, le=100)


class SentenceSemanticObservation(BaseModel):
    """
    AnalysisAgent 的句级语义观察。

    本模型刻意不包含：
    - fix_direction
    - improvement_action
    - suggested_rewrite
    - next_step

    所有改进和下一步均由 RewriteAgent 负责。
    """

    model_config = ConfigDict(extra="forbid")

    turn_index: int = Field(ge=1)
    sentence_index: int = Field(ge=1)
    sentence_text: str

    communicative_function: CommunicativeFunction
    intent_summary: str
    target_likely_interpretation: str
    target_likely_feeling: TargetFeeling

    evaluation_label: SentenceEvaluationLabel
    evaluation_score: int = Field(ge=0, le=100)
    goal_effect: GoalEffect
    evaluation_reason: str

    relationship_signal: RelationshipSignalVector
    dynamics_signal: DynamicsSignalVector


class TurnSemanticObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_index: int = Field(ge=1)
    turn_summary: str
    target_reply_interpretation: str
    turn_evaluation_score: int = Field(ge=0, le=100)
    sentences: list[SentenceSemanticObservation]


class AnalysisSemanticResult(BaseModel):
    """
    LLM 的中间输出，只表达观察与评价，不表达改进方案。
    """

    model_config = ConfigDict(extra="forbid")

    overall_assessment: str
    strengths: list[str]
    problems: list[str]
    key_risks: list[str]
    primary_bottleneck: str
    evaluation_scores: ConversationEvaluationScores
    state_trajectory_summary: str
    turns: list[TurnSemanticObservation]


class ConversationTurnTrace(BaseModel):
    """
    前端在每轮 SessionMessageResponse 后保存的可审计状态轨迹。

    relationship_delta 来自本轮最终采用的关系增量；
    dynamics_delta 来自 StateAgent；
    before/after 是整轮级真实状态，不是句级估计。
    """

    model_config = ConfigDict(extra="forbid")

    turn_index: int = Field(ge=1)
    user_message: str
    target_reply: str

    relationship_before: RelationshipState
    relationship_delta: StateDelta
    relationship_after: RelationshipState

    dynamics_before: ConversationDynamics | None = None
    dynamics_delta: ConversationDynamicsDelta | None = None
    dynamics_after: ConversationDynamics | None = None

    risk_flags: list[str] = Field(default_factory=list)


class DynamicsMetricState(BaseModel):
    """不带标签和策略字段的 Dynamics 数值状态。"""

    model_config = ConfigDict(extra="forbid")

    atmosphere_score: int = Field(ge=0, le=100)
    pace_score: int = Field(ge=0, le=100)
    pressure_level: int = Field(ge=0, le=100)
    clarity_score: int = Field(ge=0, le=100)
    responsiveness_score: int = Field(ge=0, le=100)
    progress_score: int = Field(ge=0, le=100)
    repairability_score: int = Field(ge=0, le=100)
    boundary_score: int = Field(ge=0, le=100)


class AnalysisCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_user_turns: int = Field(ge=0)
    analyzed_user_turns: int = Field(ge=0)
    total_user_sentences: int = Field(ge=0)
    analyzed_user_sentences: int = Field(ge=0)
    turn_trace_count: int = Field(ge=0)
    complete: bool


class SentenceProcessAnalysis(BaseModel):
    """
    报告展示的逐句分析项。

    这里只展示观察、影响和评价，不提供任何改进建议。
    """

    model_config = ConfigDict(extra="forbid")

    turn_index: int = Field(ge=1)
    sentence_index: int = Field(ge=1)
    sentence_text: str

    communicative_function: CommunicativeFunction
    intent_summary: str
    target_likely_interpretation: str
    target_likely_feeling: TargetFeeling

    evaluation_label: SentenceEvaluationLabel
    evaluation_score: int = Field(ge=0, le=100)
    goal_effect: GoalEffect
    evaluation_reason: str

    state_change_source: StateChangeSource
    state_change_note: str

    relationship_before: RelationshipState | None
    relationship_delta: StateDelta | None
    relationship_after: RelationshipState | None

    dynamics_before: DynamicsMetricState | None
    dynamics_delta: ConversationDynamicsDelta | None
    dynamics_after: DynamicsMetricState | None


class TurnProcessAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_index: int = Field(ge=1)
    user_message: str
    target_reply: str
    turn_summary: str
    target_reply_interpretation: str
    turn_evaluation_score: int = Field(ge=0, le=100)

    relationship_before: RelationshipState | None
    relationship_delta: StateDelta | None
    relationship_after: RelationshipState | None

    dynamics_before: DynamicsMetricState | None
    dynamics_delta: ConversationDynamicsDelta | None
    dynamics_after: DynamicsMetricState | None

    risk_flags: list[str]
    sentences: list[SentenceProcessAnalysis]


class ConversationProcessAnalysis(BaseModel):
    """
    AnalysisAgent 在报告中的完整输出。
    """

    model_config = ConfigDict(extra="forbid")

    methodology_notice: str
    coverage: AnalysisCoverage

    overall_assessment: str
    strengths: list[str]
    problems: list[str]
    key_risks: list[str]
    primary_bottleneck: str

    evaluation_scores: ConversationEvaluationScores
    state_trajectory_summary: str
    turns: list[TurnProcessAnalysis]

    @model_validator(mode="after")
    def validate_sentence_identity(self) -> "ConversationProcessAnalysis":
        seen: set[tuple[int, int]] = set()
        for turn in self.turns:
            for sentence in turn.sentences:
                key = (sentence.turn_index, sentence.sentence_index)
                if key in seen:
                    raise ValueError(
                        f"duplicate sentence analysis identity: {key}"
                    )
                seen.add(key)
        return self
