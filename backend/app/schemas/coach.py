from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ConfidenceLabel = Literal["low", "medium", "high"]
FactorDirection = Literal["positive", "negative", "mixed"]
ReasonabilityLabel = Literal[
    "reasonable",
    "conditionally_reasonable",
    "unreasonable",
    "insufficient_information",
]
SentenceFunction = Literal[
    "context",
    "request",
    "reason",
    "emotion",
    "boundary",
    "option",
    "commitment",
    "question",
    "pressure",
    "repair",
    "other",
]
SentenceEffect = Literal["helps", "hurts", "mixed", "neutral"]
RewriteStyle = Literal["balanced", "minimal_edit", "warmer", "firmer"]


class DynamicsFeatureVector(BaseModel):
    """三个 SubAgent 共用的确定性量化特征。"""

    model_config = ConfigDict(extra="forbid")

    turn_count: int = Field(ge=0)
    timeline_coverage: float = Field(ge=0, le=1)

    latest_atmosphere: int = Field(ge=0, le=100)
    latest_pace: int = Field(ge=0, le=100)
    latest_pressure: int = Field(ge=0, le=100)
    latest_clarity: int = Field(ge=0, le=100)
    latest_responsiveness: int = Field(ge=0, le=100)
    latest_progress: int = Field(ge=0, le=100)
    latest_repairability: int = Field(ge=0, le=100)
    latest_boundary: int = Field(ge=0, le=100)

    atmosphere_delta: int = Field(ge=-100, le=100)
    pace_delta: int = Field(ge=-100, le=100)
    pressure_delta: int = Field(ge=-100, le=100)
    clarity_delta: int = Field(ge=-100, le=100)
    responsiveness_delta: int = Field(ge=-100, le=100)
    progress_delta: int = Field(ge=-100, le=100)
    repairability_delta: int = Field(ge=-100, le=100)
    boundary_delta: int = Field(ge=-100, le=100)

    volatility: float = Field(ge=0, le=100)
    quantitative_baseline: int = Field(ge=0, le=100)
    trend_adjustment: int = Field(ge=-10, le=10)


class PredictionLLMResult(BaseModel):
    """
    PredictionAgent 的模型输出。

    PredictionAgent 只负责：
    1. 对量化基线做有限校正；
    2. 预测当前最可能结果；
    3. 说明概率判断依据。

    它不负责影响因素、优劣势、风险或下一步建议。
    """

    model_config = ConfigDict(extra="forbid")

    model_adjustment: int = Field(
        ge=-12,
        le=12,
        description="在确定性量化基线上的有限校正值",
    )
    likely_outcome: str
    probability_reasoning: str


class PredictionResult(BaseModel):
    """PredictionAgent 的完整内部结果。"""

    model_config = ConfigDict(extra="forbid")

    baseline_probability: int = Field(ge=0, le=100)
    model_adjustment: int = Field(ge=-12, le=12)
    success_probability: int = Field(ge=0, le=100)

    confidence: ConfidenceLabel
    confidence_score: int = Field(ge=0, le=100)

    likely_outcome: str
    probability_reasoning: str

    features: DynamicsFeatureVector


class SentenceUnit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sentence_id: str
    turn_index: int = Field(ge=1)
    sentence_index: int = Field(ge=1)
    text: str


class SentenceDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sentence_id: str
    evidence_quote: str

    function: SentenceFunction
    effect: SentenceEffect

    clarity: int = Field(ge=0, le=100)
    pressure: int = Field(ge=0, le=100)
    empathy: int = Field(ge=0, le=100)
    specificity: int = Field(ge=0, le=100)

    target_interpretation: str
    advantage: str
    disadvantage: str
    recommended_change: str


class ReasonabilityDimension(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Literal[
        "goal_legitimacy",
        "feasibility",
        "cost_to_target",
        "reciprocity",
        "consent_and_boundary",
        "timing",
        "information_completeness",
    ]
    score: int = Field(ge=0, le=100)
    evidence: str
    judgment: str


class ReasonabilityAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: ReasonabilityLabel
    overall_score: int = Field(ge=0, le=100)
    summary: str

    assumptions: list[str] = Field(default_factory=list)
    dimensions: list[ReasonabilityDimension] = Field(
        min_length=7,
        max_length=7,
    )


class TradeoffItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    evidence_quote: str
    impact: str


class AnalysisInfluenceFactor(BaseModel):
    """
    报告中的“主要影响因素”。

    这里刻意不包含 improvement_action / next_step 等建议字段，
    避免把事实诊断和行动建议混在同一个项目里。
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    direction: FactorDirection
    importance: int = Field(ge=1, le=5)

    evidence_turns: list[int] = Field(default_factory=list)
    evidence_quote: str
    impact: str


class AnalysisLLMResult(BaseModel):
    """AnalysisAgent 的模型输出。"""

    model_config = ConfigDict(extra="forbid")

    sentence_diagnostics: list[SentenceDiagnostic]
    reasonability: ReasonabilityAssessment

    influence_factors: list[AnalysisInfluenceFactor] = Field(
        default_factory=list,
        max_length=6,
    )

    advantages: list[TradeoffItem] = Field(
        default_factory=list,
        max_length=8,
    )
    disadvantages: list[TradeoffItem] = Field(
        default_factory=list,
        max_length=8,
    )

    primary_bottleneck: str
    key_risks: list[str] = Field(default_factory=list, max_length=6)

    next_step_advice: str
    do_not_say: list[str] = Field(default_factory=list, max_length=6)


class AnalysisResult(AnalysisLLMResult):
    model_config = ConfigDict(extra="forbid")

    strengths: list[str] = Field(default_factory=list, max_length=6)
    problems: list[str] = Field(default_factory=list, max_length=6)
    sentence_units: list[SentenceUnit]


class RewriteCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    style: RewriteStyle
    text: str
    design_rationale: str
    addresses_sentence_ids: list[str] = Field(default_factory=list)


class RewriteCandidatesResult(BaseModel):
    """
    RewriteAgent 只生成候选表达。

    下一步建议和避免表达已经由 AnalysisAgent 负责，
    不再允许 CandidateWriterAgent 重复生成。
    """

    model_config = ConfigDict(extra="forbid")

    candidates: list[RewriteCandidate] = Field(
        min_length=3,
        max_length=4,
    )


class CandidateScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str

    goal_fit: int = Field(ge=0, le=100)
    state_fit: int = Field(ge=0, le=100)
    naturalness: int = Field(ge=0, le=100)
    pressure_safety: int = Field(ge=0, le=100)
    specificity: int = Field(ge=0, le=100)
    fidelity: int = Field(ge=0, le=100)

    critical_issue: str
    recommendation_reason: str


class RewriteCritiqueResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scores: list[CandidateScore] = Field(
        min_length=3,
        max_length=4,
    )


class RankedRewrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate: RewriteCandidate
    score: float = Field(ge=0, le=100)
    recommendation_reason: str


class RewriteResult(BaseModel):
    """RewriteAgent 只返回排序后的对话候选。"""

    model_config = ConfigDict(extra="forbid")

    recommended: RankedRewrite
    alternatives: list[RankedRewrite]
