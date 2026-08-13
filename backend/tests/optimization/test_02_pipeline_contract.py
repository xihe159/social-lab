from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.agents.simulation.pipeline import (
    SimulationPipeline,
    SimulationPipelineContext,
    build_default_simulation_pipeline,
)


class _RecordingStage:
    def __init__(self, name: str, calls: list[str], *, terminal: bool = False) -> None:
        self.name = name
        self.calls = calls
        self.terminal = terminal

    async def execute(
        self,
        context: SimulationPipelineContext,
    ) -> SimulationPipelineContext:
        self.calls.append(self.name)
        if self.terminal:
            context.response = MagicMock(name="SessionMessageResponse")
        return context


@pytest.mark.asyncio
async def test_pipeline_executes_declared_order() -> None:
    calls: list[str] = []
    pipeline = SimulationPipeline(
        (
            _RecordingStage("prepare", calls),
            _RecordingStage("analyze", calls),
            _RecordingStage("decide", calls),
            _RecordingStage("assemble", calls, terminal=True),
        )
    )

    response = await pipeline.run(MagicMock(name="SessionMessageRequest"))
    assert calls == ["prepare", "analyze", "decide", "assemble"]
    assert response is not None


def test_default_pipeline_stage_order_is_explicit() -> None:
    pipeline = build_default_simulation_pipeline(MagicMock(name="services"))
    assert [stage.name for stage in pipeline.stages] == [
        "prepare",
        "analyze_turn",
        "strategy_guidance",
        "persona_decision",
        "generate_response",
        "evaluation_audit",
        "assemble_response",
        "persist_and_measure",
    ]


@pytest.mark.asyncio
async def test_simulation_agent_v2_is_only_a_pipeline_facade() -> None:
    from app.agents.simulation_agent_v2 import SimulationAgentV2

    request = MagicMock(name="request")
    response = MagicMock(name="response")

    class _Pipeline:
        def __init__(self) -> None:
            self.calls = 0

        async def run(self, received, *, defer_background=None):
            self.calls += 1
            assert received is request
            return response

    pipeline = _Pipeline()
    agent = object.__new__(SimulationAgentV2)
    agent.pipeline = pipeline

    result = await agent.run(request)
    assert result is response
    assert pipeline.calls == 1


def test_v2_pipeline_factory_is_explicit_opt_in() -> None:
    from app.agents.simulation_agent_factory import resolve_simulation_agent_version

    assert resolve_simulation_agent_version("v2") == "v3"
    assert resolve_simulation_agent_version("v2.1") == "v3"
    assert resolve_simulation_agent_version("v2_pipeline") == "v2_pipeline"
    assert resolve_simulation_agent_version("v2-pipeline") == "v2_pipeline"
