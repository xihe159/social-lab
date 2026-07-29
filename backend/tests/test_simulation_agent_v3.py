from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.agents.simulation_agent import SimulationAgentV1
from app.agents.simulation_agent_factory import (
    create_simulation_agent,
    resolve_simulation_agent_version,
)
from app.agents.simulation_agent_v3 import SimulationAgentV3
from app.core.config import Settings
from app.schemas.common import RelationshipState
from app.schemas.persona import Persona
from app.schemas.session import (
    ChatMessage,
    SessionMessageRequest,
    SessionMessageResponse,
    SimulationReply,
    StateDelta,
)
from app.schemas.strategy import (
    ResponseMode,
    ResponseModeHypothesis,
    TargetInterpretation,
    TargetResponseGuidance,
    ToneRange,
)


def _request() -> SessionMessageRequest:
    state = RelationshipState(
        trust=65,
        respect=70,
        familiarity=55,
        affinity=60,
        authority=50,
        emotional=10,
    )
    return SessionMessageRequest(
        scenario="work",
        goal="沟通任务分配",
        outcome="讨论一个可执行的调整方案",
        role="直属领导",
        relation="合作两年，平时沟通直接",
        persona=Persona(
            title="直接但愿意讨论事实的领导",
            style="专业、直接，也会解释判断",
            speed="正常",
            focus="事实、进度和可执行方案",
            risk="反感无证据地评价同事",
            strategy="提供事实后共同讨论",
            state=state,
        ),
        messages=[ChatMessage(role="target", content="你具体说说。")],
        user_message="最近任务确实很多，我整理好工作量后想和您讨论调整。",
    )


def _v1_response() -> SessionMessageResponse:
    simulation = SimulationReply(
        reply="可以，你把当前任务、预计时间和希望调整的部分列出来，我们一起看。",
        attitude="愿意基于具体信息继续讨论。",
        emotion="平静、务实",
        perceived_user_tone="认真且愿意承担责任",
        state_delta=StateDelta(
            trust=2,
            respect=1,
            familiarity=0,
            affinity=1,
            authority=0,
            emotional=2,
        ),
        risk_flags=[],
    )
    return SessionMessageResponse(
        target_message=ChatMessage(role="target", content=simulation.reply),
        simulation=simulation,
        updated_state=RelationshipState(
            trust=67,
            respect=71,
            familiarity=55,
            affinity=61,
            authority=50,
            emotional=12,
        ),
    )


def _guidance(mode: ResponseMode = ResponseMode.DECLINE) -> TargetResponseGuidance:
    return TargetResponseGuidance(
        guidance_id="guidance_v3_test",
        interpretation=TargetInterpretation(
            perceived_intent="希望调整任务",
            perceived_tone="理性",
            salient_point="用户将补充工作量信息",
            perceived_concern="是否影响整体进度",
        ),
        possible_response_modes=[
            ResponseModeHypothesis(
                mode=mode,
                probability=1.0,
                reason="用于验证 Strategy 不拥有回复控制权。",
            )
        ],
        recommended_mode=mode,
        communication_goal="记录一种可能反应",
        required_content=[],
        forbidden_content=["虚构事实"],
        tone_range=ToneRange(
            warmth_min=0,
            warmth_max=100,
            directness_min=0,
            directness_max=100,
            formality=50,
            emotional_intensity_max=100,
            preferred_length="medium",
        ),
        persona_evidence_refs=["persona_field:risk"],
        memory_evidence_refs=[],
        confidence=0.8,
        uncertainty_notes=[],
    )


@pytest.mark.asyncio
async def test_v3_keeps_v1_visible_reply_when_strategy_disagrees() -> None:
    original = _v1_response()
    simulation_core = AsyncMock()
    simulation_core.run.return_value = original
    strategy_agent = AsyncMock()
    strategy_agent.prompt_version = "strategy-v3-test"
    strategy_agent.run.return_value = _guidance(ResponseMode.DECLINE)
    evaluation_agent = AsyncMock()
    evaluation_agent.prompt_version = "evaluation-v3-test"
    deferred: list[tuple[object, object]] = []

    agent = SimulationAgentV3(
        simulation_core=simulation_core,
        strategy_agent=strategy_agent,
        evaluation_agent=evaluation_agent,
    )
    response = await agent.run(
        _request(),
        defer_background=lambda fn, arg: deferred.append((fn, arg)),
    )

    assert response.target_message.content == original.target_message.content
    assert response.simulation == original.simulation
    assert response.updated_state == original.updated_state
    assert response.strategy_meta is not None
    assert response.strategy_meta.recommended_mode == "decline"
    assert response.strategy_meta.final_action == "REPLY_NORMAL"
    assert response.strategy_meta.guidance_followed is False
    evaluation_agent.run.assert_not_awaited()
    assert len(deferred) == 1

    audit, audit_request = deferred[0]
    evaluation_agent.run.return_value = AsyncMock(
        simulation_success_score=90,
        hard_errors=[],
    )
    await audit(audit_request)
    evaluation_agent.run.assert_awaited_once()
    assert audit_request.simulation_result.reply == original.simulation.reply


@pytest.mark.asyncio
async def test_v3_strategy_failure_cannot_block_or_replace_v1_reply() -> None:
    original = _v1_response()
    simulation_core = AsyncMock()
    simulation_core.run.return_value = original
    strategy_agent = AsyncMock()
    strategy_agent.prompt_version = "strategy-v3-test"
    strategy_agent.run.side_effect = RuntimeError("strategy unavailable")
    evaluation_agent = AsyncMock()
    evaluation_agent.prompt_version = "evaluation-v3-test"

    response = await SimulationAgentV3(
        simulation_core=simulation_core,
        strategy_agent=strategy_agent,
        evaluation_agent=evaluation_agent,
    ).run(_request(), defer_background=lambda *_: None)

    assert response.simulation.reply == original.simulation.reply
    assert response.strategy_meta is not None
    assert response.strategy_meta.fallback_used is True
    assert response.strategy_meta.confidence == 0.0


def test_v3_is_default_and_v2_values_migrate_without_startup_failure() -> None:
    assert Settings(simulation_agent_version="v2").simulation_agent_version == "v3"
    assert Settings(simulation_agent_version="v2.1").simulation_agent_version == "v3"
    assert resolve_simulation_agent_version(" v2.1 ") == "v3"

    version, agent = create_simulation_agent("v3")
    assert version == "v3"
    assert isinstance(agent, SimulationAgentV3)

    rollback_version, rollback_agent = create_simulation_agent("v1")
    assert rollback_version == "v1"
    assert isinstance(rollback_agent, SimulationAgentV1)


def test_unknown_version_uses_v3_instead_of_retired_v2() -> None:
    version, agent = create_simulation_agent("future")
    assert version == "v3"
    assert isinstance(agent, SimulationAgentV3)
