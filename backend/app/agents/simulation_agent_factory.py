from __future__ import annotations

import logging
from typing import Literal, Protocol

from app.agents.simulation_agent import SimulationAgentV1
from app.agents.simulation_agent_v3 import SimulationAgentV3
from app.schemas.session import SessionMessageRequest, SessionMessageResponse

from app.core.config import get_settings

logger = logging.getLogger(__name__)

SimulationAgentVersion = Literal["v1", "v3"]
DEFAULT_SIMULATION_AGENT_VERSION: SimulationAgentVersion = "v3"
SUPPORTED_SIMULATION_AGENT_VERSIONS = {"v1", "v3"}
RETIRED_VERSION_ALIASES = {"v2": "v3", "v2.1": "v3", "v3.0": "v3"}


class SimulationAgentRunner(Protocol):
    async def run(self, request: SessionMessageRequest) -> SessionMessageResponse:
        ...


def resolve_simulation_agent_version(value: str | None = None) -> SimulationAgentVersion:
    """Resolve the production version and safely migrate retired V2 values."""

    raw_value = (
        value
        if value is not None
        else get_settings().simulation_agent_version
    )
    normalized = (raw_value or DEFAULT_SIMULATION_AGENT_VERSION).strip().lower()
    normalized = RETIRED_VERSION_ALIASES.get(normalized, normalized)

    if normalized not in SUPPORTED_SIMULATION_AGENT_VERSIONS:
        logger.warning(
            "invalid_simulation_agent_version_falling_back_to_v3",
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

    if selected_version == "v3":
        return selected_version, SimulationAgentV3()

    return selected_version, SimulationAgentV1()
