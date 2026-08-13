from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.agents.simulation.pipeline import (
    SimulationPipeline,
    SimulationPipelineContext,
    SimulationPipelineServices,
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
async def test_pipeline_executes_stages_in_declared_order() -> None:
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


def test_pipeline_package_exports_are_available() -> None:
    # This specifically guards against the IDE/runtime issue where the package
    # exists but its public pipeline symbols are not exported from __init__.py.
    assert SimulationPipeline is not None
    assert SimulationPipelineContext is not None
    assert SimulationPipelineServices is not None
    assert callable(build_default_simulation_pipeline)
