"""Public API for the simulation pipeline package.

Use package-relative imports here.  Absolute self-imports such as
``from app.agents.simulation.pipeline.context ...`` force Python/PyCharm to resolve
``pipeline`` through the parent package while this package is still being
initialized, which can produce false unresolved-reference diagnostics and makes
circular-import problems harder to reason about.
"""

from .context import SimulationPipelineContext
from .runner import SimulationPipeline, build_default_simulation_pipeline
from .services import SimulationPipelineServices

__all__ = [
    "SimulationPipeline",
    "SimulationPipelineContext",
    "SimulationPipelineServices",
    "build_default_simulation_pipeline",
]
