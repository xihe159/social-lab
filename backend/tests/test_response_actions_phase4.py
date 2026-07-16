from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import AsyncMock


llm_client_stub = types.ModuleType("app.llm.client")
llm_client_stub.generate_structured = AsyncMock()
sys.modules.setdefault("app.llm.client", llm_client_stub)

from app.agents.simulation.response_generator import ResponseGenerator
from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.simulation_decision import ResponsePolicy
from app.schemas.simulation_generation import GeneratedResponse, ResponseGenerationInput
from app.schemas.simulation_state import SimulationState


ALL_ACTIONS = [
    "REPLY_NORMAL",
    "REPLY_BRIEF",
    "REPLY_COLD",
    "ASK_CLARIFICATION",
    "SET_BOUNDARY",
    "CONFRONT",
    "DEFER_REPLY",
    "READ_NO_REPLY",
    "END_CONVERSATION",
]


def build_input(action: str) -> ResponseGenerationInput:
    return ResponseGenerationInput(
        persona=PersonaModelV2(persona_id="persona_test"),
        current_state=SimulationState(
            session_id="session_test",
            persona_id="persona_test",
        ),
        response_policy=ResponsePolicy(
            action=action,
            content_goals=[],
            tone="neutral",
            reply_length="short",
            must_avoid=[],
        ),
        user_message="测试消息",
    )


class ResponseActionPhase4Tests(unittest.TestCase):
    def test_schema_accepts_all_nine_actions(self) -> None:
        for action in ALL_ACTIONS:
            with self.subTest(action=action):
                self.assertEqual(build_input(action).response_policy.action, action)

    def test_silent_actions_force_empty_generated_text(self) -> None:
        for action in ["DEFER_REPLY", "READ_NO_REPLY"]:
            with self.subTest(action=action):
                result = ResponseGenerator().post_process(
                    generated=GeneratedResponse(
                        response_text="这段文字不应该显示。",
                        response_action=action,
                    ),
                    request=build_input(action),
                )
                self.assertEqual(result.response_text, "")


if __name__ == "__main__":
    unittest.main()
