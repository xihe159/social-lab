from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.evaluation_agent import EvaluationAgent
from app.agents.strategy_agent import StrategyAgent
from app.agents.simulation_agent_v2 import SimulationAgentV2
from app.agents.simulation_agent_factory import resolve_simulation_agent_version
from app.agents.simulation.response_generator import ResponseGenerator
from app.agents.simulation.simulation_decision_engine import (
    SimulationDecisionEngine,
)
from app.schemas.common import RelationshipState
from app.schemas.evaluation import (
    EvaluationScoreItem,
    EvaluationVerdict,
    FailureAttribution,
    HardErrorCode,
    SimulationEvaluationRequest,
    SimulationEvaluationResponse,
    SimulationEvaluationResult,
)
from app.schemas.memory import SessionMemory
from app.schemas.persona import Persona
from app.schemas.simulation_decision import ResponsePolicy
from app.schemas.simulation_generation import (
    GeneratedResponse,
    ResponseGenerationInput,
)
from app.schemas.simulation_guidance import (
    SimulationDecisionOutput,
    SimulationDecisionRequest,
)
from app.schemas.simulation_state import SimulationState
from app.schemas.session import SessionMessageRequest
from app.schemas.turn_state import TurnStateAnalysisResult
from app.schemas.state import StateEvaluateRequest
from app.schemas.strategy import (
    ResponseMode,
    ResponseModeHypothesis,
    StrategyMessage,
    TargetInterpretation,
    TargetResponseGuidance,
    TargetResponseStrategyRequest,
    ToneRange,
)
from app.schemas.turn_state import (
    TurnBehaviorSignals,
    TurnStateAnalysis,
    TurnStateDelta,
)
from app.services.evaluation_execution_policy import (
    resolve_evaluation_execution_mode,
)
from app.services.simulation_adjustment_manager import (
    SimulationAdjustmentManager,
)
from app.services.simulation_feedback_loop import SimulationFeedbackLoop
from app.services.state.signals import SignalDetector
from evaluation.fixtures import (
    persona_a_direct_advisor,
    persona_c_sensitive_partner,
)
from evaluation.simulation_v21_human_review import (
    PairedHumanReview,
    VersionScore,
    summarize_paired_reviews,
)
from evaluation.strategy_evaluation_baseline import load_baseline_catalog


def _guidance(
    *,
    mode: ResponseMode = ResponseMode.ENGAGE,
    persona_refs: list[str] | None = None,
    memory_refs: list[str] | None = None,
) -> TargetResponseGuidance:
    return TargetResponseGuidance(
        guidance_id="guidance_v21",
        interpretation=TargetInterpretation(
            perceived_intent="用户希望得到回应。",
            perceived_tone="中性。",
            salient_point="用户提出当前请求。",
            perceived_concern="人物会按自身立场反应。",
        ),
        possible_response_modes=[
            ResponseModeHypothesis(
                mode=mode,
                probability=1.0,
                reason="当前候选方向。",
            )
        ],
        recommended_mode=mode,
        communication_goal="保持人物真实反应。",
        required_content=["回应核心内容"],
        forbidden_content=["虚构事实"],
        tone_range=ToneRange(
            warmth_min=20,
            warmth_max=80,
            directness_min=20,
            directness_max=90,
            formality=50,
            emotional_intensity_max=70,
            preferred_length="medium",
        ),
        persona_evidence_refs=persona_refs or [],
        memory_evidence_refs=memory_refs or [],
        confidence=0.8,
        uncertainty_notes=[],
    )


def _analysis(
    *,
    pressure: float = 0.0,
    boundary_violation: float = 0.0,
    risks: list[str] | None = None,
) -> TurnStateAnalysis:
    return TurnStateAnalysis(
        user_intent="希望得到回应",
        user_emotion="中性",
        behavior_signals=TurnBehaviorSignals(
            politeness=0.7,
            clarity=0.8,
            accountability=0.6,
            pressure=pressure,
            blame=0.0,
            vulnerability=0.0,
            boundary_violation=boundary_violation,
            honesty_signal=0.7,
        ),
        persona_triggers=[],
        detected_events=[],
        risk_flags=risks or [],
        state_delta=TurnStateDelta(
            **{name: 0.0 for name in TurnStateDelta.model_fields}
        ),
        confidence=0.85,
    )


def _generation_input(
    policy: ResponsePolicy,
    *,
    strategy_action: str,
) -> ResponseGenerationInput:
    persona = persona_c_sensitive_partner()
    return ResponseGenerationInput(
        persona=persona,
        current_state=SimulationState(
            session_id="session_v21",
            persona_id=persona.persona_id,
        ),
        response_policy=policy,
        strategy_policy_id="guidance_v21",
        strategy_action=strategy_action,
        strategy_guidance_id="guidance_v21",
        recommended_mode=strategy_action,
        user_message="请你考虑一下。",
    )


def _score(value: int) -> EvaluationScoreItem:
    return EvaluationScoreItem(
        score=value,
        reason="固定回归评分",
        evidence=["persona_snapshot:eval_persona_a"],
    )


def _evaluation_response(
    value: int,
    *,
    hard_errors: list[HardErrorCode] | None = None,
) -> SimulationEvaluationResponse:
    item = _score(value)
    return SimulationEvaluationResponse(
        evaluation_id="raw",
        simulation_success_score=value,
        confidence=0.9,
        verdict=EvaluationVerdict.ACCEPT,
        failure_attribution=FailureAttribution.NONE,
        persona_fidelity=item.model_copy(deep=True),
        dyadic_consistency=item.model_copy(deep=True),
        state_continuity=item.model_copy(deep=True),
        strategy_adherence=item.model_copy(deep=True),
        reaction_plausibility=item.model_copy(deep=True),
        style_fidelity=item.model_copy(deep=True),
        evidence_grounding=item.model_copy(deep=True),
        critical_issues=[],
        hard_errors=hard_errors or [],
        correction_for_strategy=None,
        correction_for_simulation=None,
        session_learning_signals=[],
        evaluator_notes=[],
    )


def _evaluation_request(
    guidance: TargetResponseGuidance,
) -> SimulationEvaluationRequest:
    persona = persona_a_direct_advisor()
    persona.evidence_summary.chat_record_available = True
    persona.evidence_summary.evidence_count = 3
    persona.evidence_summary.overall_confidence = 0.85
    return SimulationEvaluationRequest(
        trace_id="trace_v21",
        session_id="session_v21",
        turn_id="turn_v21",
        persona_snapshot=persona,
        relationship_state_before=SimulationState(
            session_id="session_v21",
            persona_id=persona.persona_id,
        ).relationship_state,
        session_memory=SessionMemory(
            conversation_summary="",
            user_strategy_pattern=[],
            target_sensitive_points=[],
            resolved_points=[],
            unresolved_points=[],
            important_events=[],
            next_suggested_focus="",
        ),
        recent_messages=[StrategyMessage(role="user", content="请考虑。")],
        user_message="请考虑。",
        response_guidance=guidance,
        simulation_result=SimulationEvaluationResult(
            reply="我需要再想想。",
            attitude="观望",
            emotion="克制",
            perceived_user_tone="中性",
            state_delta={},
            risk_flags=[],
            policy_id=guidance.guidance_id,
            guidance_id=guidance.guidance_id,
            used_evidence_refs=[],
        ),
        strategy_prompt_version="strategy-v2.5-v21-guidance",
        simulation_prompt_version="simulation-v2.5-v21-persona-decision",
        evaluation_prompt_version="evaluation-v2.5-v21-hard-errors-only",
    )


def test_mild_decline_is_not_forced_cold_by_strategy_label() -> None:
    policy = ResponsePolicy(
        action="REPLY_NORMAL",
        content_goals=["温和说明目前不能答应"],
        tone="专业但温和",
        reply_length="medium",
        must_avoid=["冷淡指责"],
    )
    result = ResponseGenerator().post_process(
        generated=GeneratedResponse(
            response_text="我理解你的需要，不过这次我可能没办法答应。",
            response_action="REPLY_COLD",
        ),
        request=_generation_input(policy, strategy_action="decline"),
    )
    assert result.response_action == "REPLY_NORMAL"
    assert result.response_text.startswith("我理解")


def test_partial_acceptance_can_remain_warm_and_professional() -> None:
    policy = ResponsePolicy(
        action="REPLY_NORMAL",
        content_goals=["接受可完成部分并说明条件"],
        tone="温和、专业",
        reply_length="medium",
        must_avoid=["无条件承诺"],
    )
    text = "这部分我可以先帮你确认，剩下的等材料齐了我们再一起看。"
    result = ResponseGenerator().post_process(
        generated=GeneratedResponse(
            response_text=text,
            response_action="REPLY_NORMAL",
        ),
        request=_generation_input(
            policy,
            strategy_action="limited_support",
        ),
    )
    assert result.response_action == "REPLY_NORMAL"
    assert result.response_text == text


def test_long_reply_persona_is_not_mapped_down_to_medium() -> None:
    policy = ResponsePolicy(
        action="REPLY_NORMAL",
        content_goals=["完整解释感受与原因"],
        tone="情绪细腻",
        reply_length="long",
        must_avoid=[],
    )
    text = "我想把我的感受和原因完整告诉你。" * 18
    assert 240 < len(text) < 500
    result = ResponseGenerator().post_process(
        generated=GeneratedResponse(
            response_text=text,
            response_action="REPLY_NORMAL",
        ),
        request=_generation_input(policy, strategy_action="engage"),
    )
    assert result.response_text == text


def test_persona_evidence_can_legitimately_override_guidance() -> None:
    decision = SimulationDecisionOutput(
        response_policy=ResponsePolicy(
            action="REPLY_NORMAL",
            content_goals=["先了解更多信息"],
            tone="克制",
            reply_length="medium",
            must_avoid=[],
        ),
        confidence=0.84,
        guidance_followed=False,
        guidance_deviation_reason="人物一贯先确认事实，再决定是否拒绝。",
    )
    assert not decision.guidance_followed
    assert "人物" in decision.guidance_deviation_reason


def test_score_72_without_hard_error_never_requests_regeneration() -> None:
    guidance = _guidance()
    evaluated = EvaluationAgent().post_process(
        result=_evaluation_response(72),
        request=_evaluation_request(guidance),
    )
    assert evaluated.verdict == EvaluationVerdict.ACCEPT_WITH_FEEDBACK
    assert evaluated.hard_errors == []
    assert SimulationFeedbackLoop().plan(
        evaluated,
        corrections_used=0,
    ).action.value == "none"


def test_persona_hard_conflict_allows_only_one_correction() -> None:
    guidance = _guidance()
    evaluated = EvaluationAgent().post_process(
        result=_evaluation_response(
            72,
            hard_errors=[HardErrorCode.PERSONA_VIOLATION],
        ),
        request=_evaluation_request(guidance),
    )
    loop = SimulationFeedbackLoop()
    assert loop.plan(evaluated, corrections_used=0).action.value == (
        "replan_and_regenerate"
    )
    assert loop.plan(evaluated, corrections_used=1).action.value == "none"


def test_first_turn_can_keep_no_reply_with_persona_and_current_evidence() -> None:
    persona = persona_a_direct_advisor()
    state = SimulationState(
        session_id="session_v21",
        persona_id=persona.persona_id,
    )
    guidance = _guidance(
        mode=ResponseMode.NO_REPLY,
        persona_refs=["persona_field:stable_traits.boundary_strictness"],
    )
    request = SimulationDecisionRequest(
        persona=persona,
        current_state=state,
        scenario="advisor",
        goal="获得回应",
        user_message="你必须马上答应，不然我会一直催。",
        turn_state_analysis=_analysis(
            pressure=0.9,
            boundary_violation=0.8,
            risks=["pressure"],
        ),
        strategy_guidance=guidance,
    )
    output = SimulationDecisionOutput(
        response_policy=ResponsePolicy(
            action="READ_NO_REPLY",
            content_goals=[],
            tone="不回应",
            reply_length="short",
            must_avoid=[],
        ),
        confidence=0.8,
        guidance_followed=True,
    )
    processed = SimulationDecisionEngine().post_process(
        result=output,
        request=request,
    )
    assert processed.response_policy.action == "READ_NO_REPLY"


def test_extreme_guidance_stays_candidate_but_is_not_recommended_without_evidence() -> None:
    persona = persona_a_direct_advisor()
    guidance = _guidance(mode=ResponseMode.NO_REPLY)
    request = TargetResponseStrategyRequest(
        trace_id="trace_guard",
        session_id="session_guard",
        turn_id="turn_guard",
        scenario="advisor",
        persona_snapshot=persona,
        relationship_state=SimulationState(
            session_id="session_guard",
            persona_id=persona.persona_id,
        ).relationship_state,
        user_message="老师，您看到了吗？",
        turn_state_analysis=_analysis(),
    )
    processed = StrategyAgent().post_process(
        result=guidance,
        request=request,
    )
    modes = {item.mode for item in processed.possible_response_modes}
    assert ResponseMode.NO_REPLY in modes
    assert processed.recommended_mode == ResponseMode.DEFER


def test_negated_pressure_and_refusal_are_not_detected() -> None:
    relationship = RelationshipState(
        trust=50,
        respect=50,
        familiarity=50,
        affinity=50,
        authority=50,
        emotional=0,
    )
    persona = Persona(
        title="测试人物",
        style="自然",
        speed="正常",
        focus="事实",
        risk="施压",
        strategy="沟通",
        state=relationship,
    )
    signals = SignalDetector().detect(
        StateEvaluateRequest(
            scenario="advisor",
            goal="确认",
            outcome="",
            persona=persona,
            messages=[],
            user_message="这不是必须马上完成的，你可以慢慢考虑。",
            target_reply="我并非不接受，只是还要看材料。",
            current_state=relationship,
            simulation_attitude="观望",
            simulation_emotion="平静",
            perceived_user_tone="中性",
        )
    )
    assert not signals.pressure
    assert not signals.explicit_refusal


def test_production_auto_mode_uses_unified_settings() -> None:
    settings = SimpleNamespace(
        app_env="production",
        evaluation_execution_mode="auto",
    )
    with patch(
        "app.services.evaluation_execution_policy.get_settings",
        return_value=settings,
    ):
        assert resolve_evaluation_execution_mode() == "production_hybrid"


def test_v21_feature_flag_migrates_to_v3_production_path() -> None:
    assert resolve_simulation_agent_version("v2.1") == "v3"
    assert resolve_simulation_agent_version("invalid") == "v3"


def test_session_learning_uses_numeric_temporary_style_preferences() -> None:
    manager = SimulationAdjustmentManager()
    for turn in range(1, 4):
        context = manager.begin_turn("session_style")
        observed = manager.observe(
            session_id="session_style",
            turn_number=context.turn_number,
            evaluation_id=f"evaluation_{turn}",
            signals=["reply_too_long"],
            confidence=0.9,
            failure_attribution=FailureAttribution.NONE,
        )
    assert observed.profile is not None
    assert observed.profile.style.length_scale == 0.9
    assert observed.profile.style_adjustments == []
    assert observed.profile.strategy_adjustments == []


@pytest.mark.asyncio
async def test_pipeline_exposes_guidance_and_persona_owned_final_decision() -> None:
    legacy_persona = Persona(
        title="会先了解情况的导师",
        style="专业、平和",
        speed="正常",
        focus="事实完整度",
        risk="无依据承诺",
        strategy="先确认事实",
        state=RelationshipState(
            trust=60,
            respect=70,
            familiarity=30,
            affinity=45,
            authority=80,
            emotional=0,
        ),
    )
    request = SessionMessageRequest(
        scenario="advisor",
        goal="请导师接受延期",
        outcome="允许延期",
        role="导师",
        relation="师生",
        persona=legacy_persona,
        messages=[],
        user_message="老师，我想申请延期一天。",
        persona_id="pipeline_persona",
        session_id="pipeline_session",
    )
    state = SimulationState(
        session_id="pipeline_session",
        persona_id="pipeline_persona",
    )
    updated = state.model_copy(deep=True)
    updated.conversation_state.turn_count = 1

    analyzer = AsyncMock()
    analyzer.prompt_version = "turn-state-v2.1-test"
    analyzer.run.return_value = TurnStateAnalysisResult(
        analysis=_analysis(),
        updated_state=updated,
    )
    guidance = _guidance(mode=ResponseMode.CONDITIONAL_SUPPORT)
    strategy = AsyncMock()
    strategy.prompt_version = "strategy-v2.5-v21-test"
    strategy.run.return_value = guidance
    decision_engine = AsyncMock()
    decision_engine.prompt_version = "simulation-decision-v2.1-test"
    decision_engine.run.return_value = SimulationDecisionOutput(
        response_policy=ResponsePolicy(
            action="ASK_CLARIFICATION",
            content_goals=["询问缺少哪些材料"],
            tone="专业、平和",
            reply_length="medium",
            must_avoid=["直接接受或拒绝"],
        ),
        confidence=0.88,
        guidance_followed=False,
        guidance_deviation_reason="人物一贯先确认事实。",
    )
    generator = AsyncMock()
    generator.prompt_version = "simulation-v2.5-v21-test"
    generator.run.return_value = GeneratedResponse(
        response_text="具体还缺哪些材料？",
        response_action="ASK_CLARIFICATION",
    )
    evaluator = AsyncMock()
    evaluator.prompt_version = "evaluation-v2.5-v21-test"
    deferred: list[tuple] = []

    def defer(function, *args) -> None:
        deferred.append((function, args))

    agent = SimulationAgentV2(
        strategy_agent=strategy,
        turn_state_analyzer=analyzer,
        simulation_decision_engine=decision_engine,
        response_generator=generator,
        evaluation_agent=evaluator,
        evaluation_execution_mode="production_hybrid",
    )
    response = await agent.run(request, defer_background=defer)

    assert response.response.action == "ASK_CLARIFICATION"
    assert response.strategy_meta.recommended_mode == "conditional_support"
    assert response.strategy_meta.final_action == "ASK_CLARIFICATION"
    assert not response.strategy_meta.guidance_followed
    assert response.strategy_meta.guidance_deviation_reason
    assert response.runtime_meta.decision_fallback_used is False
    assert len(deferred) == 1

    failing_strategy = AsyncMock()
    failing_strategy.prompt_version = "strategy-v2.5-v21-test"
    failing_strategy.run.side_effect = RuntimeError("strategy unavailable")
    evaluator.run.return_value = _evaluation_response(90)
    fallback_agent = SimulationAgentV2(
        strategy_agent=failing_strategy,
        turn_state_analyzer=analyzer,
        simulation_decision_engine=decision_engine,
        response_generator=generator,
        evaluation_agent=evaluator,
        evaluation_execution_mode="production_hybrid",
    )
    fallback_response = await fallback_agent.run(request)
    assert fallback_response.response.action == "ASK_CLARIFICATION"
    assert fallback_response.runtime_meta.strategy_fallback_used is True
    assert fallback_response.runtime_meta.decision_fallback_used is False


def test_release_summary_requires_and_scores_all_36_fixed_cases() -> None:
    catalog = load_baseline_catalog()
    reviews = [
        PairedHumanReview(
            case_id=case.case_id,
            winner="v2.1",
            v1=VersionScore(
                naturalness=4,
                persona_consistency=4,
                emotional_continuity=4,
            ),
            v21=VersionScore(
                naturalness=5,
                persona_consistency=4,
                emotional_continuity=5,
            ),
            ordinary_turn=True,
            v21_evaluation_intervened=False,
        )
        for case in catalog.cases
    ]
    summary = summarize_paired_reviews(reviews, catalog=catalog)
    assert summary.case_count == 36
    assert summary.gates_passed
