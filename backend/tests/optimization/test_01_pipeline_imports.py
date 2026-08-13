from __future__ import annotations


def test_pipeline_submodules_import() -> None:
    from app.agents.simulation.pipeline.context import SimulationPipelineContext
    from app.agents.simulation.pipeline.runner import (
        SimulationPipeline,
        build_default_simulation_pipeline,
    )
    from app.agents.simulation.pipeline.services import SimulationPipelineServices

    assert SimulationPipelineContext is not None
    assert SimulationPipeline is not None
    assert SimulationPipelineServices is not None
    assert callable(build_default_simulation_pipeline)


def test_pipeline_public_api_import() -> None:
    from app.agents.simulation.pipeline import (
        SimulationPipeline,
        SimulationPipelineContext,
        SimulationPipelineServices,
        build_default_simulation_pipeline,
    )

    assert SimulationPipeline is not None
    assert SimulationPipelineContext is not None
    assert SimulationPipelineServices is not None
    assert callable(build_default_simulation_pipeline)
