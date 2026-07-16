from __future__ import annotations

import logging
import os
from typing import Literal, Protocol

from app.agents.simulation_agent import SimulationAgentV1
from app.agents.simulation_agent_v2 import SimulationAgentV2
from app.schemas.session import SessionMessageRequest, SessionMessageResponse


logger = logging.getLogger(__name__)

SimulationAgentVersion = Literal["v1", "v2"]
DEFAULT_SIMULATION_AGENT_VERSION: SimulationAgentVersion = "v1"
SUPPORTED_SIMULATION_AGENT_VERSIONS = {"v1", "v2"}


class SimulationAgentRunner(Protocol):
    async def run(self, request: SessionMessageRequest) -> SessionMessageResponse:
        ...


def resolve_simulation_agent_version(value: str | None = None) -> SimulationAgentVersion:
    """Resolve the feature flag, falling back safely to V1 on invalid input."""

    raw_value = value if value is not None else os.getenv("SIMULATION_AGENT_VERSION")
    normalized = (raw_value or DEFAULT_SIMULATION_AGENT_VERSION).strip().lower()

    if normalized not in SUPPORTED_SIMULATION_AGENT_VERSIONS:
        logger.warning(
            "invalid_simulation_agent_version_falling_back_to_v1",
            extra={
                "configured_version": raw_value,
                "fallback_version": DEFAULT_SIMULATION_AGENT_VERSION,
            },
        )
        return DEFAULT_SIMULATION_AGENT_VERSION

    return normalized  # type: ignore[return-value]


def create_simulation_agent(
    version: str | None = None,
) -> tuple[SimulationAgentVersion, SimulationAgentRunner]:
    selected_version = resolve_simulation_agent_version(version)

    if selected_version == "v2":
        return selected_version, SimulationAgentV2()

    return selected_version, SimulationAgentV1()
