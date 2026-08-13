from __future__ import annotations

from hashlib import sha256

from app.agents.simulation.decision_engine import apply_simulation_state_delta
from app.schemas.common import RelationshipState
from app.schemas.memory import SessionMemory
from app.schemas.session import SessionMessageRequest, StateDelta
from app.schemas.simulation_adjustment import SimulationAdjustmentProfile
from app.schemas.simulation_decision import (
    BehaviorSignals,
    DecisionAction,
    ResponsePolicy,
    SimulationStateDelta,
    TurnAnalysis,
    TurnDecisionOutput,
    TurnDecisionResult,
)
from app.schemas.simulation_guidance import SimulationDecisionOutput
from app.schemas.simulation_state import EmotionalState, SimulationState
from app.schemas.strategy import (
    ResponseMode,
    ResponseModeHypothesis,
    TargetInterpretation,
    TargetResponseGuidance,
    TargetResponseStrategyRequest,
    ToneRange,
)
from app.services.state.constants import PRESSURE_WORDS
from app.services.state.utils import contains_affirmed_any
from app.schemas.turn_state import (
    TurnBehaviorSignals,
    TurnStateAnalysis,
    TurnStateAnalysisResult,
    TurnStateDelta,
)

SILENT_ACTIONS = {"DEFER_REPLY", "READ_NO_REPLY"}


def stable_persona_id(request: SessionMessageRequest) -> str:
    value = f"{request.persona.title}|{request.persona.style}|{request.role}"
    return f"persona_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def stable_session_id(request: SessionMessageRequest, persona_id: str) -> str:
    value = f"{persona_id}|{request.scenario}|{request.goal}"
    return f"session_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def fallback_strategy_guidance(request: TargetResponseStrategyRequest) -> TargetResponseGuidance:
    return TargetResponseGuidance(
        guidance_id=f"guidance_fallback_{request.turn_id}",
        interpretation=TargetInterpretation(
            perceived_intent="当前无法可靠判断用户意图。",
            perceived_tone="中性或不确定。",
            salient_point="需要对用户当前表达作出保守回应。",
            perceived_concern="上下文或策略服务暂时不可用。",
        ),
        possible_response_modes=[
            ResponseModeHypothesis(
                mode=ResponseMode.ENGAGE,
                probability=1.0,
                reason="Strategy 暂不可用，保留人物决策空间。",
            )
        ],
        recommended_mode=ResponseMode.ENGAGE,
        communication_goal="理解当前表达并保持人物自身的真实反应。",
        required_content=["回应用户当前表达"],
        forbidden_content=["升级冲突", "虚构事实", "替用户制定下一句话"],
        tone_range=ToneRange(
            warmth_min=25,
            warmth_max=70,
            directness_min=30,
            directness_max=75,
            formality=50,
            emotional_intensity_max=55,
            preferred_length="medium",
        ),
        persona_evidence_refs=[f"persona_snapshot:{request.persona_snapshot.persona_id}"],
        memory_evidence_refs=[],
        confidence=0.0,
        uncertainty_notes=["StrategyAgent 不可用，使用开放式建议。"],
    )


def fallback_turn_state_analysis(current_state: SimulationState) -> TurnStateAnalysisResult:
    state_delta = TurnStateDelta(**{name: 0.0 for name in TurnStateDelta.model_fields})
    analysis = TurnStateAnalysis(
        user_intent="当前用户意图暂时无法可靠解析。",
        user_emotion="不确定",
        behavior_signals=TurnBehaviorSignals(
            politeness=0.5,
            clarity=0.5,
            accountability=0.5,
            pressure=0.0,
            blame=0.0,
            vulnerability=0.0,
            boundary_violation=0.0,
            honesty_signal=0.5,
        ),
        persona_triggers=[],
        detected_events=[],
        risk_flags=[],
        state_delta=state_delta,
        confidence=0.0,
    )
    updated_state = apply_simulation_state_delta(
        state=current_state,
        delta=SimulationStateDelta(**state_delta.model_dump()),
    )
    return TurnStateAnalysisResult(analysis=analysis, updated_state=updated_state)


def fallback_simulation_decision(guidance: TargetResponseGuidance) -> SimulationDecisionOutput:
    follows_guidance = guidance.recommended_mode == ResponseMode.ENGAGE
    return SimulationDecisionOutput(
        response_policy=ResponsePolicy(
            action="REPLY_NORMAL",
            content_goals=["回应用户当前表达，不新增事实或承诺"],
            tone="中性、克制",
            reply_length="medium",
            must_avoid=["虚构人物事实", "无依据地拒绝或接受"],
        ),
        confidence=0.0,
        guidance_followed=follows_guidance,
        guidance_deviation_reason="" if follows_guidance else "人物决策层不可用，使用中性安全回退。",
    )


def build_legacy_decision_result(
    *,
    turn_state_result: TurnStateAnalysisResult,
    simulation_decision: SimulationDecisionOutput,
    user_message: str,
) -> TurnDecisionResult:
    analysis = turn_state_result.analysis
    detected_events = confirmed_turn_risks(
        analysis=analysis,
        user_message=user_message,
    )
    return TurnDecisionResult(
        decision=TurnDecisionOutput(
            turn_analysis=TurnAnalysis(
                intent=analysis.user_intent,
                behavior_signals=BehaviorSignals(**analysis.behavior_signals.model_dump()),
                detected_events=detected_events,
            ),
            state_delta=SimulationStateDelta(**analysis.state_delta.model_dump()),
            response_policy=simulation_decision.response_policy,
            confidence=simulation_decision.confidence,
        ),
        updated_state=turn_state_result.updated_state,
    )


def confirmed_turn_risks(
    *,
    analysis: TurnStateAnalysis,
    user_message: str,
) -> list[str]:
    """Expose only risk labels with deterministic semantic support.

    This preserves the upstream V2 compatibility behavior while keeping the
    failure-policy refactor focused on execution semantics rather than changing
    conversation-risk semantics.
    """
    semantic_pressure = contains_affirmed_any(
        user_message,
        (
            *PRESSURE_WORDS,
            "威胁",
            "逼你",
            "必须答应",
            "or else",
            "threat",
        ),
    )
    semantic_insult = contains_affirmed_any(
        user_message,
        ("废物", "蠢", "滚", "没用", "都是你的错", "insult", "stupid"),
    )
    semantic_deception = contains_affirmed_any(
        user_message,
        ("骗", "撒谎", "隐瞒", "deceive", "lied"),
    )
    semantic_refusal = contains_affirmed_any(
        user_message,
        ("拒绝", "不接受", "不愿意", "不想", "不要再", "别再"),
    )

    explicit_risk_events = [
        value
        for value in analysis.detected_events
        if any(
            marker in value.lower()
            for marker in (
                "pressure",
                "threat",
                "boundary",
                "insult",
                "施压",
                "威胁",
                "越界",
                "侮辱",
            )
        )
    ]

    confirmed: list[str] = []
    for value in [*analysis.risk_flags, *explicit_risk_events]:
        normalized = value.lower()
        is_pressure_risk = any(
            marker in normalized
            for marker in (
                "pressure",
                "threat",
                "boundary",
                "施压",
                "威胁",
                "越界",
                "催促",
            )
        )
        is_insult_risk = any(
            marker in normalized for marker in ("insult", "侮辱", "辱骂")
        )
        is_deception_risk = any(
            marker in normalized
            for marker in ("deception", "deceive", "欺骗", "撒谎", "隐瞒")
        )
        is_refusal_risk = any(
            marker in normalized
            for marker in ("refusal", "reject", "拒绝", "停止推进")
        )

        if is_pressure_risk and not semantic_pressure:
            continue
        if is_insult_risk and not semantic_insult:
            continue
        if is_deception_risk and not semantic_deception:
            continue
        if is_refusal_risk and not semantic_refusal:
            continue
        if not any(
            (is_pressure_risk, is_insult_risk, is_deception_risk, is_refusal_risk)
        ):
            continue
        confirmed.append(value)

    return unique_strings(confirmed, limit=8)


def empty_session_memory() -> SessionMemory:
    return SessionMemory(
        conversation_summary="",
        user_strategy_pattern=[],
        target_sensitive_points=[],
        resolved_points=[],
        unresolved_points=[],
        important_events=[],
        next_suggested_focus="",
    )


def unique_strings(values: list[str], *, limit: int) -> list[str]:
    result: list[str] = []
    for value in values:
        item = str(value).strip()
        if item and item not in result:
            result.append(item[:240])
        if len(result) >= limit:
            break
    return result


def digest_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def to_legacy_relationship_state(previous: RelationshipState, state: SimulationState) -> RelationshipState:
    emotional_balance = (
        state.relationship_state.psychological_safety
        - state.emotional_state.irritation
        - state.emotional_state.hurt
        - state.emotional_state.defensiveness
    )
    return RelationshipState(
        trust=round(state.relationship_state.trust * 100),
        respect=round(state.relationship_state.respect * 100),
        familiarity=previous.familiarity,
        affinity=round(state.relationship_state.warmth * 100),
        authority=previous.authority,
        emotional=max(-100, min(100, round(emotional_balance * 100))),
    )


def legacy_delta(previous: RelationshipState, updated: RelationshipState) -> StateDelta:
    def change(value: int) -> int:
        return max(-10, min(10, int(value)))
    return StateDelta(
        trust=change(updated.trust - previous.trust),
        respect=change(updated.respect - previous.respect),
        familiarity=0,
        affinity=change(updated.affinity - previous.affinity),
        authority=0,
        emotional=change(updated.emotional - previous.emotional),
    )


def attitude_label(action: DecisionAction) -> str:
    return {
        "REPLY_BRIEF": "简短回应",
        "REPLY_COLD": "态度降温",
        "ASK_CLARIFICATION": "需要澄清",
        "SET_BOUNDARY": "明确边界",
        "CONFRONT": "直接指出问题",
    }.get(action, "正常参与交流")


def dominant_emotion(state: EmotionalState) -> str:
    values = {
        "烦躁": state.irritation,
        "受伤": state.hurt,
        "焦虑": state.anxiety,
        "防御": state.defensiveness,
        "疲惫": state.fatigue,
    }
    label, score = max(values.items(), key=lambda item: item[1])
    return label if score >= 0.2 else "平静"


def perceived_tone(signals: BehaviorSignals) -> str:
    if signals.boundary_violation >= 0.6:
        return "越界或施压"
    if signals.blame >= 0.6:
        return "带有指责"
    if signals.politeness >= 0.7 and signals.accountability >= 0.5:
        return "礼貌且愿意承担责任"
    if signals.politeness <= 0.3:
        return "直接且不够礼貌"
    return "中性表达"


def status_text(action: DecisionAction) -> str:
    return {
        "DEFER_REPLY": "对方暂时没有回复。",
        "READ_NO_REPLY": "对方已读了消息。",
        "END_CONVERSATION": "对方结束了本次交流。",
    }.get(action, "")


def style_adjustment_count(profile: SimulationAdjustmentProfile) -> int:
    style = profile.style
    return sum(
        (
            style.length_scale != 1.0,
            style.explanation_ratio_delta != 0.0,
            style.punctuation_match_strength != 0.5,
            style.prevent_unplanned_commitment,
        )
    )
