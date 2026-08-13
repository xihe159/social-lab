from __future__ import annotations

from app.agents.analysis_agent import AnalysisAgent
from app.agents.prediction_agent import PredictionAgent
from app.agents.rewrite_agent import RewriteAgent
from app.schemas.analysis import ConversationProcessAnalysis
from app.schemas.prediction import (
    PredictionResult,
    SemanticInfluenceFactor,
    SemanticPredictionAssessment,
)
from app.schemas.report import ReportRequest
from app.schemas.rewrite import RewriteResult, RewriteVariants
from app.schemas.strategy import (
    ResponseMode,
    ResponseModeHypothesis,
    TargetInterpretation,
    TargetResponseGuidance,
    TargetResponseStrategyRequest,
    ToneRange,
)


def fallback_prediction(
    agent: PredictionAgent,
    request: ReportRequest,
) -> PredictionResult:
    """Use the existing deterministic calculator with zero semantic adjustment."""
    context = agent.build_context(request)
    semantic = SemanticPredictionAssessment(
        outcome_state="unknown",
        semantic_adjustment=0,
        evidence_strength=0.0,
        likely_outcome="语义模型暂时不可用；当前结果仅基于结构化状态与趋势估计。",
        probability_reasoning=(
            "本次未使用 LLM 语义修正，评分由 PredictionCalculator 的确定性输入计算。"
        ),
        semantic_factors=[
            SemanticInfluenceFactor(
                factor_name="语义评估暂不可用",
                direction="mixed",
                importance=1,
                evidence_turns=[],
                evidence_quote="未使用语义证据。",
                explanation="该因素不参与加减分，仅标记本次报告处于降级模式。",
            )
        ],
    )
    semantic = agent.post_process_semantic(semantic, context)
    return agent.calculator.calculate(context=context, semantic=semantic)


def fallback_analysis(
    agent: AnalysisAgent,
    request: ReportRequest,
) -> ConversationProcessAnalysis:
    """Reuse AnalysisAgent's deterministic neutral semantic builder."""
    manifest, coverage = agent.allocator.build_manifest(request.messages)
    semantic = (
        agent._fallback_semantic(manifest)
        if manifest
        else agent._empty_semantic()
    )
    return agent.allocator.build_analysis(
        request=request,
        semantic=semantic,
        manifest=manifest,
        coverage=coverage,
    )


def fallback_rewrite(
    agent: RewriteAgent,
    request: ReportRequest,
) -> RewriteResult:
    text = agent._default_rewrite(request)
    return RewriteResult(
        suggested_rewrite=text,
        sentence_rewrites=[],
        variants=RewriteVariants(
            minimal_edit=text,
            warmer_version=text,
            firmer_version=text,
        ),
        next_step_advice=(
            "先确认目标人物是否愿意继续讨论，再推进一个具体、可拒绝的小步骤。"
        ),
        do_not_say=[
            "不要使用命令、威胁、道德绑架或要求立即表态的表达。"
        ],
    )


def fallback_strategy_guidance(
    request: TargetResponseStrategyRequest,
) -> TargetResponseGuidance:
    """Neutral guidance that explicitly does not constrain Simulation."""
    return TargetResponseGuidance(
        guidance_id=f"guidance_fallback_{request.turn_id}",
        interpretation=TargetInterpretation(
            perceived_intent="暂时无法稳定识别。",
            perceived_tone="中性或不确定。",
            salient_point="保留 Simulation 自身的人物反应。",
            perceived_concern="Strategy 服务暂时不可用。",
        ),
        possible_response_modes=[
            ResponseModeHypothesis(
                mode=ResponseMode.ENGAGE,
                probability=1.0,
                reason="回退 Guidance 不对人物回复施加额外约束。",
            )
        ],
        recommended_mode=ResponseMode.ENGAGE,
        communication_goal="保留目标人物自主反应。",
        required_content=[],
        forbidden_content=["虚构人物事实"],
        tone_range=ToneRange(
            warmth_min=0,
            warmth_max=100,
            directness_min=0,
            directness_max=100,
            formality=50,
            emotional_intensity_max=100,
            preferred_length="medium",
        ),
        persona_evidence_refs=[],
        memory_evidence_refs=[],
        confidence=0.0,
        uncertainty_notes=["Strategy 失败，本轮未让其干预 Simulation。"],
    )
