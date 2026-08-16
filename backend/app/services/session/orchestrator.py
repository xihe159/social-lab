from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from app.agents.memory_agent import MemoryAgent
from app.agents.policy_agents import PolicySafetyAgent
from app.agents.simulation_agent_factory import create_simulation_agent, resolve_simulation_agent_version
from app.agents.state_agent import StateAgent
from app.schemas.session import SessionMessageRequest, SessionMessageResponse
from app.services.session.context import SessionExecutionContext
from app.services.session.stages import MemoryStage, SafetyStage, SimulationStage, StateStage
from app.services.session.telemetry import SessionTelemetry

logger = logging.getLogger(__name__)


class SessionOrchestrator:
    """Safety -> Simulation -> State -> Memory with one shared failure contract."""

    def __init__(
        self,
        simulation_agent_version: str | None = None,
        *,
        safety_agent: Any | None = None,
        simulation_agent: Any | None = None,
        state_agent: Any | None = None,
        memory_agent: Any | None = None,
        telemetry: SessionTelemetry | None = None,
    ):
        self.telemetry = telemetry or SessionTelemetry()
        self.safety_agent = safety_agent or PolicySafetyAgent()
        self.state_agent = state_agent or StateAgent()
        self.memory_agent = memory_agent or MemoryAgent()
        if simulation_agent is None:
            self.simulation_agent_version, self.simulation_agent = create_simulation_agent(simulation_agent_version)
        else:
            self.simulation_agent_version = resolve_simulation_agent_version(simulation_agent_version)
            self.simulation_agent = simulation_agent

        self.safety_stage = SafetyStage(self.safety_agent, self.telemetry)
        self.simulation_stage = SimulationStage(
            agent=self.simulation_agent,
            version=self.simulation_agent_version,
            telemetry=self.telemetry,
        )
        self.state_stage = StateStage(
            agent=self.state_agent,
            override_relationship_state=(self.simulation_agent_version == "v1"),
            telemetry=self.telemetry,
        )
        self.memory_stage = MemoryStage(self.memory_agent, self.telemetry)
        logger.info(
            "session_orchestrator_initialized",
            extra={
                "service": "SessionOrchestrator",
                "simulation_agent_version": self.simulation_agent_version,
                "pipeline": ["SafetyStage", "SimulationStage", "StateStage", "MemoryStage"],
                "failure_contract": "required/degraded/best_effort",
            },
        )

    async def handle_message(
        self,
        request: SessionMessageRequest,
        *,
        defer_background: Callable[..., None] | None = None,
    ) -> SessionMessageResponse:
        context = SessionExecutionContext(
            request=request,
            simulation_agent_version=self.simulation_agent_version,
            defer_background=defer_background,
        )
        self.telemetry.session_started(context)
        context = await self.safety_stage.execute(context)
        if context.blocked:
            self.telemetry.session_finished(context, status="blocked")
            return context.require_response()

        context = await self.simulation_stage.execute(context)
        context = await self.state_stage.execute(context)
        context = await self.memory_stage.execute(context)
        self.telemetry.session_finished(
            context,
            status="degraded" if context.degraded else "success",
        )
        return context.require_response()
