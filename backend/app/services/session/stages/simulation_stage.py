# social-lab/backend/app/services/session/stages/safety_stage.py
# 2026/07/28

from __future__ import annotations

from typing import Any

from app.services.session.context import SessionExecutionContext
from app.services.session.policies import append_safety_warning_if_needed
from app.services.session.telemetry import SessionTelemetry


class SimulationStage:
    """主流程 Stage；失败时保持原行为，直接让请求失败。"""

    def __init__(
        self,
        *,
        agent: Any,
        version: str,
        telemetry: SessionTelemetry,
    ):
        self.agent = agent
        self.version = version
        self.telemetry = telemetry

    async def execute(
        self,
        context: SessionExecutionContext,
    ) -> SessionExecutionContext:
        request = context.request
        safety_result = context.require_safety_result()

        started_at = self.telemetry.agent_started(
            context,
            agent="SimulationAgent",
            simulation_agent_version=self.version,
            message_count=len(request.messages),
            has_memory=request.memory is not None,
        )

        if self.version == "v3":
            response = await self.agent.run(
                request,
                defer_background=context.defer_background,
            )
        else:
            response = await self.agent.run(request)

        response.safety = safety_result
        append_safety_warning_if_needed(
            risk_flags=response.simulation.risk_flags,
            safety_result=safety_result,
        )

        context.response = response
        context.state_delta = response.simulation.state_delta
        context.risk_flags = list(response.simulation.risk_flags)

        self.telemetry.agent_finished(
            context,
            agent="SimulationAgent",
            started_at=started_at,
            simulation_agent_version=self.version,
            **self.telemetry.simulation_fields(response),
        )
        return context
