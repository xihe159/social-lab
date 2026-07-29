from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.schemas.common import RelationshipState

from app.schemas.safety import SafetyCheckResponse
from app.services.session.orchestrator import SessionOrchestrator


class FakeSafetyAgent:
    def __init__(self, result: SafetyCheckResponse):
        self.result = result
        self.calls = 0

    async def run(self, request):
        self.calls += 1
        return self.result


class NeverCalledAgent:
    async def run(self, *args, **kwargs):
        raise AssertionError("安全拦截后不应该调用后续 Agent")


@pytest.mark.asyncio
async def test_blocked_request_stops_pipeline():
    safety_result = SafetyCheckResponse(
        allowed=False,
        risk_level="high",
        action="block",
        risk_types=["privacy"],
        user_notice="输入包含隐私风险。",
        safe_rewrite_hint="删除真实身份信息后重试。",
        should_redact=True,
        redacted_fields=["user_message"],
    )
    safety_agent = FakeSafetyAgent(safety_result)

    orchestrator = SessionOrchestrator(
        "v2",
        safety_agent=safety_agent,
        simulation_agent=NeverCalledAgent(),
        state_agent=NeverCalledAgent(),
        memory_agent=NeverCalledAgent(),
    )

    relationship_state = RelationshipState(
        trust=50,
        respect=50,
        familiarity=20,
        affinity=30,
        authority=50,
        emotional=0,
    )
    request = SimpleNamespace(
        scenario="work",
        goal="沟通",
        outcome="",
        persona=SimpleNamespace(state=relationship_state),
        messages=[],
        user_message="测试内容",
        memory=None,
        current_dynamics=None,
    )

    response = await orchestrator.handle_message(request)

    assert safety_agent.calls == 1
    assert response.safety is safety_result
    assert response.updated_state is relationship_state
    assert response.simulation.state_delta.trust == 0
    assert "安全改写建议" in response.target_message.content
