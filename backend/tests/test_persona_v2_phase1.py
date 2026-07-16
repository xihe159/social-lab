from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.schemas.common import RelationshipState
from app.schemas.persona import Persona
from app.schemas.persona_v2 import PersonaModelV2, StableTraits
from app.schemas.simulation_state import EmotionalState, RelationshipStateV2
from app.services.persona_v2_adapter import compile_legacy_persona
from app.services.simulation_state_service import create_initial_simulation_state


def build_legacy_advisor_persona() -> Persona:
    return Persona(
        title="严格、直接、责任导向的导师",
        style="理性、结果导向、回复简洁",
        speed="偏慢",
        focus="是否承担责任并给出明确计划",
        risk="不尊重或反复找借口",
        strategy="说明事实、承担责任、提出方案",
        state=RelationshipState(
            trust=60,
            respect=80,
            familiarity=45,
            affinity=40,
            authority=85,
            emotional=20,
        ),
    )


class PersonaModelV2Tests(unittest.TestCase):
    def test_defaults_create_a_valid_persona_model(self) -> None:
        persona = PersonaModelV2(persona_id="persona_default")

        self.assertEqual(persona.version, "2.0")
        self.assertEqual(persona.stable_traits.directness, 0.5)
        self.assertEqual(persona.behavior_patterns, [])

    def test_legacy_advisor_converts_to_persona_v2(self) -> None:
        persona = compile_legacy_persona(
            build_legacy_advisor_persona(),
            persona_id="persona_advisor",
            role="导师",
            relation="关系尊敬",
            scenario="advisor",
            evidence_count=3,
            confidence=0.65,
        )

        validated = PersonaModelV2.model_validate(persona.model_dump())

        self.assertEqual(validated.basic_profile.role, "导师")
        self.assertEqual(validated.basic_profile.relationship_type, "关系尊敬")
        self.assertEqual(validated.basic_profile.power_dynamic, "target_high_authority")
        self.assertGreaterEqual(validated.stable_traits.directness, 0.75)
        self.assertGreaterEqual(validated.stable_traits.responsibility_orientation, 0.75)
        self.assertEqual(validated.dyadic_profile.trust, 0.6)
        self.assertEqual(validated.dyadic_profile.respect, 0.8)
        self.assertEqual(validated.evidence_summary.evidence_count, 3)

    def test_scores_outside_unit_range_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            StableTraits(directness=1.1)

        with self.assertRaises(ValidationError):
            EmotionalState(irritation=-0.1)

    def test_unknown_fields_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            RelationshipStateV2(trust=0.5, unknown=1)


class SimulationStateInitializationTests(unittest.TestCase):
    def test_initial_state_uses_dyadic_relationship_and_neutral_emotions(self) -> None:
        persona = compile_legacy_persona(
            build_legacy_advisor_persona(),
            persona_id="persona_advisor",
            scenario="advisor",
        )

        state = create_initial_simulation_state(
            persona,
            session_id="session_test",
        )

        self.assertEqual(state.session_id, "session_test")
        self.assertEqual(state.persona_id, persona.persona_id)
        self.assertEqual(state.relationship_state.trust, persona.dyadic_profile.trust)
        self.assertEqual(state.relationship_state.respect, persona.dyadic_profile.respect)
        self.assertEqual(state.emotional_state, EmotionalState())
        self.assertEqual(state.conversation_state.turn_count, 0)

    def test_each_session_receives_an_independent_state(self) -> None:
        persona = PersonaModelV2(persona_id="persona_independent")

        first = create_initial_simulation_state(persona, session_id="session_first")
        second = create_initial_simulation_state(persona, session_id="session_second")
        first.relationship_state.trust = 0.2

        self.assertEqual(second.relationship_state.trust, 0.5)
        self.assertNotEqual(first.session_id, second.session_id)


if __name__ == "__main__":
    unittest.main()
