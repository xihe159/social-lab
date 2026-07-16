from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import AsyncMock, patch


llm_client_stub = types.ModuleType("app.llm.client")
llm_client_stub.generate_structured = AsyncMock()
sys.modules.setdefault("app.llm.client", llm_client_stub)

from app.agents.simulation.prompts import build_response_generation_prompt
from app.agents.simulation.response_generator import ResponseGenerator
from app.schemas.persona_v2 import CommunicationStyle, PersonaModelV2
from app.schemas.simulation_decision import ResponsePolicy
from app.schemas.simulation_generation import GeneratedResponse, ResponseGenerationInput
from app.schemas.simulation_state import SimulationState


def build_generation_input(
    *,
    action: str = "REPLY_NORMAL",
    reply_length: str = "medium",
) -> ResponseGenerationInput:
    return ResponseGenerationInput(
        persona=PersonaModelV2(
            persona_id="persona_test",
            communication_style=CommunicationStyle(
                average_reply_length="short",
                formality=0.8,
                emoji_frequency=0.0,
                question_frequency=0.4,
                uses_periods=True,
                uses_multiple_messages=False,
            ),
        ),
        current_state=SimulationState(
            session_id="session_test",
            persona_id="persona_test",
        ),
        response_policy=ResponsePolicy(
            action=action,
            content_goals=["确认用户的请求", "说明下一步要求"],
            tone="克制、直接",
            reply_length=reply_length,
            must_avoid=["沟通建议", "心理旁白"],
        ),
        user_message="老师，能请您帮我看看吗？",
    )


class ResponseGeneratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_uses_structured_output(self) -> None:
        request = build_generation_input()
        model_output = GeneratedResponse(
            response_text="可以，你把材料发给我。",
            response_action="REPLY_NORMAL",
        )

        with patch(
            "app.agents.simulation.response_generator.generate_structured",
            new=AsyncMock(return_value=model_output),
        ) as generate:
            result = await ResponseGenerator().run(request)

        self.assertEqual(result.response_text, "可以，你把材料发给我。")
        self.assertEqual(generate.await_args.kwargs["output_model"], GeneratedResponse)

    async def test_generator_cannot_change_decided_action(self) -> None:
        request = build_generation_input(action="SET_BOUNDARY", reply_length="short")
        generated = GeneratedResponse(
            response_text="这件事我已经说明过了，请不要再继续要求。",
            response_action="REPLY_NORMAL",
        )

        result = ResponseGenerator().post_process(
            generated=generated,
            request=request,
        )

        self.assertEqual(result.response_action, "SET_BOUNDARY")

    async def test_brief_action_enforces_short_output(self) -> None:
        request = build_generation_input(action="REPLY_BRIEF", reply_length="long")
        generated = GeneratedResponse(
            response_text="这是一段明显超过简短回复长度要求的文本。" * 10,
            response_action="REPLY_BRIEF",
        )

        result = ResponseGenerator().post_process(
            generated=generated,
            request=request,
        )

        self.assertLessEqual(len(result.response_text), 60)
        self.assertTrue(result.response_text.endswith("…"))

    async def test_prompt_contains_communication_style_and_fixed_policy(self) -> None:
        prompt = build_response_generation_prompt(
            build_generation_input(action="REPLY_COLD", reply_length="short")
        )

        self.assertIn('"average_reply_length": "short"', prompt)
        self.assertIn('"action": "REPLY_COLD"', prompt)
        self.assertIn('"must_avoid"', prompt)


if __name__ == "__main__":
    unittest.main()
