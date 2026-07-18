from __future__ import annotations

from app.agents.simulation.decision_engine import apply_simulation_state_delta
from app.schemas.simulation_decision import (
    BehaviorSignals,
    ResponsePolicy,
    SimulationStateDelta,
    TurnAnalysis,
    TurnDecisionOutput,
    TurnDecisionResult,
)
from app.schemas.simulation_state import SimulationState
from app.schemas.strategy import ResponseAction, TargetResponsePolicy


STRATEGY_TO_SIMULATION_ACTION = {
    ResponseAction.ANSWER: "REPLY_NORMAL",
    ResponseAction.ACKNOWLEDGE: "REPLY_BRIEF",
    ResponseAction.ASK_CLARIFICATION: "ASK_CLARIFICATION",
    ResponseAction.ACCEPT: "REPLY_NORMAL",
    ResponseAction.ACCEPT_WITH_CONDITION: "REPLY_NORMAL",
    ResponseAction.PARTIAL_ACCEPT: "REPLY_COLD",
    ResponseAction.REFUSE: "REPLY_COLD",
    ResponseAction.CHALLENGE: "CONFRONT",
    ResponseAction.SET_BOUNDARY: "SET_BOUNDARY",
    ResponseAction.DEFER: "DEFER_REPLY",
    ResponseAction.NO_REPLY: "READ_NO_REPLY",
    ResponseAction.END_CONVERSATION: "END_CONVERSATION",
}

NEGATIVE_TONE_MARKERS = (
    "不礼貌",
    "冒犯",
    "施压",
    "威胁",
    "指责",
    "攻击",
    "贬低",
    "越界",
    "hostile",
    "pressure",
    "threat",
    "blame",
)
POSITIVE_TONE_MARKERS = (
    "礼貌",
    "真诚",
    "道歉",
    "负责",
    "承担责任",
    "诚恳",
    "polite",
    "apology",
    "accountable",
)


def adapt_strategy_policy(policy: TargetResponsePolicy) -> ResponsePolicy:
    """Translate the single Strategy-owned policy into the V2 renderer contract."""

    action = STRATEGY_TO_SIMULATION_ACTION[policy.action]
    tone = (
        f"stance={policy.stance}; warmth={policy.tone_profile.warmth}; "
        f"directness={policy.tone_profile.directness}; "
        f"formality={policy.tone_profile.formality}; "
        f"emotional_intensity={policy.tone_profile.emotional_intensity}"
    )
    content_goals = [policy.response_goal, *policy.required_content]
    return ResponsePolicy(
        action=action,
        content_goals=_unique(content_goals, limit=6),
        tone=tone,
        reply_length=(
            "short"
            if policy.tone_profile.length in {"very_short", "short"}
            else "medium"
        ),
        must_avoid=_unique(policy.forbidden_content, limit=6),
    )


def build_decision_result_from_strategy(
    *,
    policy: TargetResponsePolicy,
    current_state: SimulationState,
) -> TurnDecisionResult:
    """Build state and evaluator context without a second policy-deciding LLM."""

    signals, events, tone_class = _signals_from_interpretation(policy)
    delta = _state_delta(policy.action, tone_class=tone_class)
    response_policy = adapt_strategy_policy(policy)
    decision = TurnDecisionOutput(
        turn_analysis=TurnAnalysis(
            intent=policy.interpretation.perceived_intent,
            behavior_signals=signals,
            detected_events=events,
        ),
        state_delta=delta,
        response_policy=response_policy,
        confidence=policy.confidence,
    )
    return TurnDecisionResult(
        decision=decision,
        updated_state=apply_simulation_state_delta(
            state=current_state,
            delta=delta,
        ),
    )


def _signals_from_interpretation(
    policy: TargetResponsePolicy,
) -> tuple[BehaviorSignals, list[str], str]:
    interpretation = policy.interpretation
    text = " ".join(
        [
            interpretation.perceived_tone,
            interpretation.perceived_intent,
            interpretation.salient_point,
            interpretation.perceived_concern,
        ]
    ).lower()
    negative = any(marker in text for marker in NEGATIVE_TONE_MARKERS)
    positive = any(marker in text for marker in POSITIVE_TONE_MARKERS)

    if negative:
        tone_class = "negative"
        events = ["user_pressure_or_boundary_risk"]
        signals = BehaviorSignals(
            politeness=0.25,
            clarity=0.6,
            accountability=0.25,
            pressure=0.75,
            blame=0.55,
            vulnerability=0.1,
            boundary_violation=0.65,
            honesty_signal=0.45,
        )
    elif positive:
        tone_class = "positive"
        events = ["polite_or_accountable_expression"]
        signals = BehaviorSignals(
            politeness=0.85,
            clarity=0.75,
            accountability=0.8,
            pressure=0.1,
            blame=0.0,
            vulnerability=0.25,
            boundary_violation=0.0,
            honesty_signal=0.75,
        )
    else:
        tone_class = "neutral"
        events = []
        signals = BehaviorSignals(
            politeness=0.5,
            clarity=0.6,
            accountability=0.5,
            pressure=0.2,
            blame=0.1,
            vulnerability=0.1,
            boundary_violation=0.0,
            honesty_signal=0.55,
        )
    return signals, events, tone_class


def _state_delta(
    action: ResponseAction,
    *,
    tone_class: str,
) -> SimulationStateDelta:
    values = {name: 0.0 for name in SimulationStateDelta.model_fields}

    if tone_class == "positive":
        _add(
            values,
            trust=0.03,
            respect=0.03,
            warmth=0.025,
            patience=0.02,
            psychological_safety=0.02,
            willingness_to_engage=0.03,
            irritation=-0.02,
            defensiveness=-0.02,
            topic_resolution=0.04,
        )
    elif tone_class == "negative":
        _add(
            values,
            trust=-0.04,
            respect=-0.04,
            warmth=-0.035,
            patience=-0.04,
            psychological_safety=-0.04,
            willingness_to_engage=-0.035,
            irritation=0.06,
            defensiveness=0.05,
            conflict_level=0.06,
            boundary_pressure=0.05,
        )

    if action in {
        ResponseAction.ACCEPT,
        ResponseAction.ACCEPT_WITH_CONDITION,
        ResponseAction.PARTIAL_ACCEPT,
    }:
        _add(values, topic_resolution=0.05, willingness_to_engage=0.02)
    elif action == ResponseAction.ACKNOWLEDGE:
        _add(values, topic_resolution=0.02)
    elif action == ResponseAction.ASK_CLARIFICATION:
        _add(values, willingness_to_engage=0.015, anxiety=0.01)
    elif action == ResponseAction.REFUSE:
        _add(values, topic_resolution=0.02, boundary_pressure=0.025)
    elif action == ResponseAction.CHALLENGE:
        _add(values, conflict_level=0.03, defensiveness=0.025)
    elif action == ResponseAction.SET_BOUNDARY:
        _add(values, willingness_to_engage=-0.02, boundary_pressure=0.05)
    elif action == ResponseAction.DEFER:
        _add(values, willingness_to_engage=-0.03, fatigue=0.025)
    elif action == ResponseAction.NO_REPLY:
        _add(values, willingness_to_engage=-0.05, fatigue=0.04)
    elif action == ResponseAction.END_CONVERSATION:
        _add(
            values,
            willingness_to_engage=-0.08,
            topic_resolution=0.05,
            boundary_pressure=0.08,
        )

    return SimulationStateDelta(
        **{name: _bounded(value) for name, value in values.items()}
    )


def _add(values: dict[str, float], **changes: float) -> None:
    for name, change in changes.items():
        values[name] += change


def _bounded(value: float) -> float:
    return round(max(-0.15, min(0.15, value)), 3)


def _unique(values: list[str], *, limit: int) -> list[str]:
    result: list[str] = []
    for value in values:
        item = str(value).strip()
        if item and item not in result:
            result.append(item[:200])
    return result[:limit]
