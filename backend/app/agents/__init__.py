"""Public API for Social Lab agents.

This package intentionally uses lazy imports.

Why:
- many agents depend on each other indirectly through Session/Simulation services;
- policy wrappers subclass or compose ordinary agents;
- Simulation V3 has compatibility/resilience wrappers;
- importing every agent eagerly from ``app.agents`` would make circular imports
  much easier to introduce.

Preferred external usage::

    from app.agents import StateAgent, StrategyAgent
    from app.agents import create_simulation_agent

Internal modules may still import the concrete implementation directly when that
makes a dependency boundary clearer::

    from app.agents.state_agent import StateAgent

Prompt definitions belong to ``app.prompts``.
Failure policies belong to ``app.agents.failure_policies`` / ``app.core``.
Simulation pipeline internals belong to ``app.agents.simulation.pipeline``.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any


# Public name -> (module, attribute)
#
# Keep this list intentionally small: expose top-level Agent entry points and the
# Simulation factory, not every helper/reducer/prompt/pipeline implementation.
_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # Report / analysis
    "AnalysisAgent": ("app.agents.analysis_agent", "AnalysisAgent"),
    "PredictionAgent": ("app.agents.prediction_agent", "PredictionAgent"),
    "RewriteAgent": ("app.agents.rewrite_agent", "RewriteAgent"),
    "CoachAgent": ("app.agents.coach_agent", "CoachAgent"),

    # Session agents
    "PersonaAgent": ("app.agents.persona_agent", "PersonaAgent"),
    "SafetyAgent": ("app.agents.safety_agent", "SafetyAgent"),
    "StateAgent": ("app.agents.state_agent", "StateAgent"),
    "MemoryAgent": ("app.agents.memory_agent", "MemoryAgent"),

    # Strategy / evaluation
    "StrategyAgent": ("app.agents.strategy_agent", "StrategyAgent"),
    "EvaluationAgent": ("app.agents.evaluation_agent", "EvaluationAgent"),

    # Shared-failure-policy wrappers
    "PolicyAnalysisAgent": ("app.agents.policy_agents", "PolicyAnalysisAgent"),
    "PolicySafetyAgent": ("app.agents.policy_agents", "PolicySafetyAgent"),

    # Simulation implementations
    "SimulationAgentV1": ("app.agents.simulation_agent", "SimulationAgentV1"),
    "SimulationAgentV2": ("app.agents.simulation_agent_v2", "SimulationAgentV2"),
    "SimulationAgentV3": ("app.agents.simulation_agent_v3", "SimulationAgentV3"),
    "ResilientSimulationAgentV3": (
        "app.agents.simulation_agent_v3_resilient",
        "ResilientSimulationAgentV3",
    ),

    # Simulation factory / public contract
    "SimulationAgentRunner": (
        "app.agents.simulation_agent_factory",
        "SimulationAgentRunner",
    ),
    "SimulationAgentVersion": (
        "app.agents.simulation_agent_factory",
        "SimulationAgentVersion",
    ),
    "create_simulation_agent": (
        "app.agents.simulation_agent_factory",
        "create_simulation_agent",
    ),
    "resolve_simulation_agent_version": (
        "app.agents.simulation_agent_factory",
        "resolve_simulation_agent_version",
    ),
}


__all__ = sorted(_LAZY_EXPORTS)


def __getattr__(name: str) -> Any:
    """Load public Agent symbols only when they are first requested.

    PEP 562 module-level ``__getattr__`` keeps ``import app.agents`` cheap and,
    more importantly, prevents package initialization from eagerly importing the
    entire Agent graph.
    """
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attribute_name = target
    module = import_module(module_name)
    value = getattr(module, attribute_name)

    # Cache after first successful resolution. Future access has normal module
    # attribute performance and does not call __getattr__ again.
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Expose lazy public symbols to IDEs and interactive shells."""
    return sorted(set(globals()) | set(__all__))


if TYPE_CHECKING:
    # These imports exist only for static type checkers / IDE completion.
    # They are not executed at runtime, so they cannot introduce import cycles.
    from app.agents.analysis_agent import AnalysisAgent as AnalysisAgent
    from app.agents.coach_agent import CoachAgent as CoachAgent
    from app.agents.evaluation_agent import EvaluationAgent as EvaluationAgent
    from app.agents.memory_agent import MemoryAgent as MemoryAgent
    from app.agents.persona_agent import PersonaAgent as PersonaAgent
    from app.agents.policy_agents import (
        PolicyAnalysisAgent as PolicyAnalysisAgent,
        PolicySafetyAgent as PolicySafetyAgent,
    )
    from app.agents.prediction_agent import PredictionAgent as PredictionAgent
    from app.agents.rewrite_agent import RewriteAgent as RewriteAgent
    from app.agents.safety_agent import SafetyAgent as SafetyAgent
    from app.agents.simulation_agent import SimulationAgentV1 as SimulationAgentV1
    from app.agents.simulation_agent_factory import (
        SimulationAgentRunner as SimulationAgentRunner,
        SimulationAgentVersion as SimulationAgentVersion,
        create_simulation_agent as create_simulation_agent,
        resolve_simulation_agent_version as resolve_simulation_agent_version,
    )
    from app.agents.simulation_agent_v2 import SimulationAgentV2 as SimulationAgentV2
    from app.agents.simulation_agent_v3 import SimulationAgentV3 as SimulationAgentV3
    from app.agents.simulation_agent_v3_resilient import (
        ResilientSimulationAgentV3 as ResilientSimulationAgentV3,
    )
    from app.agents.state_agent import StateAgent as StateAgent
    from app.agents.strategy_agent import StrategyAgent as StrategyAgent
