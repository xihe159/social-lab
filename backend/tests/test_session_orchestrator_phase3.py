from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import AsyncMock


llm_client_stub = sys.modules.setdefault(
    "app.llm.client",
    types.ModuleType("app.llm.client"),
)


class StubLLMClientError(RuntimeError):
    pass


llm_client_stub.LLMClientError = StubLLMClientError
if not hasattr(llm_client_stub, "generate_structured"):
    llm_client_stub.generate_structured = AsyncMock()

from app.schemas.common import RelationshipState
from app.schemas.persona import Persona
from app.schemas.safety import SafetyCheckResponse
from app.schemas.session import (
    ChatMessage,
    SessionMessageRequest,
    SessionMessageResponse,
    SimulationReply,
    StateDelta,
)
from app.services.session_orchestrator import SessionOrchestrator


def build_request() -> SessionMessageRequest:
    return SessionMessageRequest(
        scenario="advisor",
        goal="请求建议",
        persona=Persona(
            title="导师",
            style="直接",
            speed="正常",
            focus="结果",
            risk="失礼",
            strategy="说明计划",
            state=RelationshipState(
                trust=60,
                respect=70,
                familiarity=40,
                affinity=50,
                authority=80,
                emotional=10,
            ),
        ),
        user_message="老师您好。",
    )


def build_response() -> SessionMessageResponse:
    state = RelationshipState(
        trust=60,
        respect=70,
        familiarity=40,
        affinity=50,
        authority=80,
        emotional=10,
    )
    return SessionMessageResponse(
        target_message=ChatMessage(role="target", content="你说。"),
        simulation=SimulationReply(
            reply="你说。",
            attitude="正常参与交流",
            emotion="平静",
            perceived_user_tone="礼貌",
            state_delta=StateDelta(
                trust=0,
                respect=0,
                familiarity=0,
                affinity=0,
                authority=0,
                emotional=0,
            ),
            risk_flags=[],
        ),
        updated_state=state,
    )


def build_safety() -> SafetyCheckResponse:
    return SafetyCheckResponse(
        allowed=True,
        risk_level="none",
        action="allow",
        risk_types=[],
        user_notice="",
        safe_rewrite_hint="",
        should_redact=False,
        redacted_fields=[],
    )


class SessionOrchestratorPhase3Tests(unittest.IsolatedAsyncioTestCase):
    async def test_v2_skips_legacy_state_agent(self) -> None:
        orchestrator = SessionOrchestrator(simulation_agent_version="v2")
        orchestrator._run_safety_agent = AsyncMock(return_value=build_safety())
        orchestrator._run_simulation_agent = AsyncMock(return_value=build_response())
        orchestrator._run_state_agent_with_fallback = AsyncMock()
        orchestrator._run_memory_agent_with_fallback = AsyncMock(return_value=None)

        response = await orchestrator.handle_message(build_request())

        self.assertEqual(response.target_message.content, "你说。")
        orchestrator._run_state_agent_with_fallback.assert_not_awaited()
        orchestrator._run_memory_agent_with_fallback.assert_awaited_once()

    async def test_v1_keeps_legacy_state_agent(self) -> None:
        orchestrator = SessionOrchestrator(simulation_agent_version="v1")
        response = build_response()
        delta = response.simulation.state_delta
        orchestrator._run_safety_agent = AsyncMock(return_value=build_safety())
        orchestrator._run_simulation_agent = AsyncMock(return_value=response)
        orchestrator._run_state_agent_with_fallback = AsyncMock(
            return_value=(delta, [])
        )
        orchestrator._run_memory_agent_with_fallback = AsyncMock(return_value=None)

        await orchestrator.handle_message(build_request())

        orchestrator._run_state_agent_with_fallback.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
