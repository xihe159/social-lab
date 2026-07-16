from __future__ import annotations

from app.agents.simulation.prompts import (
    TURN_DECISION_SYSTEM_PROMPT,
    build_turn_decision_prompt,
)
from app.llm.client import generate_structured
from app.schemas.simulation_decision import (
    SimulationStateDelta,
    TurnDecisionInput,
    TurnDecisionOutput,
    TurnDecisionResult,
)
from app.schemas.simulation_state import (
    ConversationState,
    EmotionalState,
    RelationshipStateV2,
    SimulationState,
)


NORMAL_DELTA_LIMIT = 0.15
MAJOR_DELTA_LIMIT = 0.25
EMOTIONAL_DECAY = 0.90

MAJOR_EVENT_NAMES = {
    "severe_insult",
    "major_deception",
    "serious_boundary_violation",
    "严重侮辱",
    "重大欺骗",
    "严重边界侵犯",
}


class TurnDecisionEngine:
    """Analyze one user turn, update state, and select response behavior."""

    async def run(self, request: TurnDecisionInput) -> TurnDecisionResult:
        decision = await generate_structured(
            system_prompt=TURN_DECISION_SYSTEM_PROMPT,
            user_prompt=build_turn_decision_prompt(request),
            output_model=TurnDecisionOutput,
            temperature=0.25,
        )
        return self.post_process(decision=decision, current_state=request.current_state)

    def post_process(
        self,
        *,
        decision: TurnDecisionOutput,
        current_state: SimulationState,
    ) -> TurnDecisionResult:
        self._normalize_analysis(decision)
        self._normalize_response_policy(decision)
        self._clamp_state_delta(decision)

        updated_state = apply_simulation_state_delta(
            state=current_state,
            delta=decision.state_delta,
        )
        return TurnDecisionResult(decision=decision, updated_state=updated_state)

    def _normalize_analysis(self, decision: TurnDecisionOutput) -> None:
        analysis = decision.turn_analysis
        analysis.intent = analysis.intent.strip() or "unknown"
        analysis.detected_events = _clean_string_list(
            analysis.detected_events,
            max_items=8,
            max_length=80,
        )
        decision.confidence = _clamp(decision.confidence, 0.0, 1.0)

    def _normalize_response_policy(self, decision: TurnDecisionOutput) -> None:
        policy = decision.response_policy
        policy.tone = policy.tone.strip() or "neutral"
        policy.content_goals = _clean_string_list(
            policy.content_goals,
            max_items=5,
            max_length=120,
        )
        policy.must_avoid = _clean_string_list(
            policy.must_avoid,
            max_items=5,
            max_length=120,
        )

        if not policy.content_goals:
            policy.content_goals = ["回应用户当前表达"]

    def _clamp_state_delta(self, decision: TurnDecisionOutput) -> None:
        normalized_events = {
            event.strip().lower() for event in decision.turn_analysis.detected_events
        }
        is_major_event = bool(normalized_events & MAJOR_EVENT_NAMES)
        limit = MAJOR_DELTA_LIMIT if is_major_event else NORMAL_DELTA_LIMIT

        delta = decision.state_delta
        for field_name in SimulationStateDelta.model_fields:
            value = getattr(delta, field_name)
            setattr(delta, field_name, _clamp(value, -limit, limit))


def apply_simulation_state_delta(
    *,
    state: SimulationState,
    delta: SimulationStateDelta,
) -> SimulationState:
    """Return a new V2 state with emotional decay and bounded 0-1 values."""

    relationship = state.relationship_state
    emotion = state.emotional_state
    conversation = state.conversation_state

    return SimulationState(
        session_id=state.session_id,
        persona_id=state.persona_id,
        relationship_state=RelationshipStateV2(
            trust=_unit(relationship.trust + delta.trust),
            respect=_unit(relationship.respect + delta.respect),
            warmth=_unit(relationship.warmth + delta.warmth),
            patience=_unit(relationship.patience + delta.patience),
            psychological_safety=_unit(
                relationship.psychological_safety + delta.psychological_safety
            ),
            willingness_to_engage=_unit(
                relationship.willingness_to_engage + delta.willingness_to_engage
            ),
        ),
        emotional_state=EmotionalState(
            irritation=_unit(emotion.irritation * EMOTIONAL_DECAY + delta.irritation),
            hurt=_unit(emotion.hurt * EMOTIONAL_DECAY + delta.hurt),
            anxiety=_unit(emotion.anxiety * EMOTIONAL_DECAY + delta.anxiety),
            defensiveness=_unit(
                emotion.defensiveness * EMOTIONAL_DECAY + delta.defensiveness
            ),
            fatigue=_unit(emotion.fatigue * EMOTIONAL_DECAY + delta.fatigue),
        ),
        conversation_state=ConversationState(
            turn_count=conversation.turn_count + 1,
            conflict_level=_unit(
                conversation.conflict_level + delta.conflict_level
            ),
            topic_resolution=_unit(
                conversation.topic_resolution + delta.topic_resolution
            ),
            boundary_pressure=_unit(
                conversation.boundary_pressure + delta.boundary_pressure
            ),
        ),
    )


def _clean_string_list(
    values: list[str],
    *,
    max_items: int,
    max_length: int,
) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        item = value.strip()
        if not item or item in cleaned:
            continue
        cleaned.append(item[:max_length])
    return cleaned[:max_items]


def _unit(value: float) -> float:
    return _clamp(value, 0.0, 1.0)


def _clamp(value: float, low: float, high: float) -> float:
    return round(max(low, min(high, float(value))), 3)
