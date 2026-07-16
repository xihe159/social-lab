from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError


llm_client_stub = types.ModuleType("app.llm.client")
llm_client_stub.generate_structured = AsyncMock()
sys.modules.setdefault("app.llm.client", llm_client_stub)

from app.agents.simulation.decision_engine import (
    TurnDecisionEngine,
    apply_simulation_state_delta,
)
from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.simulation_decision import (
    BehaviorSignals,
    ResponsePolicy,
    SimulationStateDelta,
    TurnAnalysis,
    TurnDecisionInput,
    TurnDecisionOutput,
)
from app.schemas.simulation_state import (
    EmotionalState,
    RelationshipStateV2,
    SimulationState,
)


def build_delta(**overrides: float) -> SimulationStateDelta:
    values = {
        "trust": 0.0,
        "respect": 0.0,
        "warmth": 0.0,
        "patience": 0.0,
        "psychological_safety": 0.0,
        "willingness_to_engage": 0.0,
        "irritation": 0.0,
        "hurt": 0.0,
        "anxiety": 0.0,
        "defensiveness": 0.0,
        "fatigue": 0.0,
        "conflict_level": 0.0,
        "topic_resolution": 0.0,
        "boundary_pressure": 0.0,
    }
    values.update(overrides)
    return SimulationStateDelta(**values)


def build_decision(
    *,
    delta: SimulationStateDelta | None = None,
    events: list[str] | None = None,
    politeness: float = 0.7,
) -> TurnDecisionOutput:
    return TurnDecisionOutput(
        turn_analysis=TurnAnalysis(
            intent="request_help",
            behavior_signals=BehaviorSignals(
                politeness=politeness,
                clarity=0.7,
                accountability=0.6,
                pressure=0.1,
                blame=0.0,
                vulnerability=0.2,
                boundary_violation=0.0,
                honesty_signal=0.7,
            ),
            detected_events=events or [],
        ),
        state_delta=delta or build_delta(),
        response_policy=ResponsePolicy(
            action="REPLY_NORMAL",
            content_goals=["确认收到请求"],
            tone="neutral",
            reply_length="medium",
            must_avoid=[],
        ),
        confidence=0.8,
    )


def build_state() -> SimulationState:
    return SimulationState(
        session_id="session_test",
        persona_id="persona_test",
        relationship_state=RelationshipStateV2(
            trust=0.6,
            respect=0.7,
            warmth=0.5,
            patience=0.6,
            psychological_safety=0.6,
            willingness_to_engage=0.7,
        ),
        emotional_state=EmotionalState(
            irritation=0.5,
            hurt=0.2,
            anxiety=0.1,
            defensiveness=0.3,
            fatigue=0.1,
        ),
    )


class TurnDecisionSchemaTests(unittest.TestCase):
    def test_behavior_signal_outside_unit_range_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            BehaviorSignals(
                politeness=1.2,
                clarity=0.5,
                accountability=0.5,
                pressure=0.5,
                blame=0.5,
                vulnerability=0.5,
                boundary_violation=0.5,
                honesty_signal=0.5,
            )

    def test_decision_input_rejects_mismatched_persona_state(self) -> None:
        with self.assertRaises(ValidationError):
            TurnDecisionInput(
                persona=PersonaModelV2(persona_id="persona_other"),
                current_state=build_state(),
                scenario="advisor",
                goal="请求建议",
                user_message="老师您好。",
            )

    def test_normal_turn_delta_is_clamped_to_point_fifteen(self) -> None:
        result = TurnDecisionEngine().post_process(
            decision=build_decision(
                delta=build_delta(trust=-0.8, irritation=0.9),
            ),
            current_state=build_state(),
        )

        self.assertEqual(result.decision.state_delta.trust, -0.15)
        self.assertEqual(result.decision.state_delta.irritation, 0.15)

    def test_recognized_major_event_allows_point_twenty_five(self) -> None:
        result = TurnDecisionEngine().post_process(
            decision=build_decision(
                delta=build_delta(respect=-0.8, defensiveness=0.7),
                events=["severe_insult"],
            ),
            current_state=build_state(),
        )

        self.assertEqual(result.decision.state_delta.respect, -0.25)
        self.assertEqual(result.decision.state_delta.defensiveness, 0.25)


class SimulationStateUpdateTests(unittest.TestCase):
    def test_state_update_applies_decay_without_mutating_previous_state(self) -> None:
        previous = build_state()
        updated = apply_simulation_state_delta(
            state=previous,
            delta=build_delta(trust=0.1, irritation=0.1, conflict_level=0.1),
        )

        self.assertEqual(updated.relationship_state.trust, 0.7)
        self.assertEqual(updated.emotional_state.irritation, 0.55)
        self.assertEqual(updated.conversation_state.conflict_level, 0.1)
        self.assertEqual(updated.conversation_state.turn_count, 1)
        self.assertEqual(previous.relationship_state.trust, 0.6)
        self.assertEqual(previous.emotional_state.irritation, 0.5)


class TurnDecisionEngineRunTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_uses_structured_llm_output_and_updates_state(self) -> None:
        model_output = build_decision(delta=build_delta(trust=0.05))
        request = TurnDecisionInput(
            persona=PersonaModelV2(persona_id="persona_test"),
            current_state=build_state(),
            scenario="advisor",
            goal="请求导师提供建议",
            user_message="老师您好，请问您方便给我一些建议吗？",
        )

        with patch(
            "app.agents.simulation.decision_engine.generate_structured",
            new=AsyncMock(return_value=model_output),
        ) as generate:
            result = await TurnDecisionEngine().run(request)

        self.assertEqual(result.updated_state.relationship_state.trust, 0.65)
        self.assertEqual(generate.await_args.kwargs["output_model"], TurnDecisionOutput)

    async def test_polite_and_rude_turns_keep_distinct_model_decisions(self) -> None:
        polite_output = build_decision(
            politeness=0.9,
            delta=build_delta(respect=0.04, warmth=0.03),
        )
        rude_output = build_decision(
            politeness=0.1,
            delta=build_delta(respect=-0.12, warmth=-0.08, irritation=0.12),
        )
        base = {
            "persona": PersonaModelV2(persona_id="persona_test"),
            "current_state": build_state(),
            "scenario": "advisor",
            "goal": "请求导师提供建议",
        }
        polite_request = TurnDecisionInput(
            **base,
            user_message="老师您好，请问您方便给我一些建议吗？",
        )
        rude_request = TurnDecisionInput(
            **base,
            user_message="你现在就给我改，别再问了。",
        )
        generate = AsyncMock(side_effect=[polite_output, rude_output])

        with patch(
            "app.agents.simulation.decision_engine.generate_structured",
            new=generate,
        ):
            polite = await TurnDecisionEngine().run(polite_request)
            rude = await TurnDecisionEngine().run(rude_request)

        self.assertGreater(
            polite.decision.state_delta.respect,
            rude.decision.state_delta.respect,
        )
        self.assertLess(
            polite.decision.state_delta.irritation,
            rude.decision.state_delta.irritation,
        )


if __name__ == "__main__":
    unittest.main()
