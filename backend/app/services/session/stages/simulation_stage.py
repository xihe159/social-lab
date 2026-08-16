from __future__ import annotations

from typing import Any

from app.agents.failure_policies import SESSION_SIMULATION_REQUIRED
from app.core.agent_failure import run_agent_call
from app.services.session.context import SessionExecutionContext
from app.services.session.policies import append_safety_warning_if_needed
from app.services.session.telemetry import SessionTelemetry


class SimulationStage:
    """主模拟是 REQUIRED：没有目标人物回复就不能伪造一轮成功 Session。"""

    def __init__(self, *, agent: Any, version: str, telemetry: SessionTelemetry):
        self.agent = agent
        self.version = version
        self.telemetry = telemetry

    async def execute(self, context: SessionExecutionContext) -> SessionExecutionContext:
        request = context.request
        safety_result = context.require_safety_result()
        started_at = self.telemetry.agent_started(
            context,
            agent="SimulationAgent",
            simulation_agent_version=self.version,
            message_count=len(request.messages),
            has_memory=request.memory is not None,
        )

        async def invoke():
            if self.version in {"v3", "v2_pipeline"}:
                return await self.agent.run(
                    request,
                    defer_background=context.defer_background,
                )
            return await self.agent.run(request)

        outcome = await run_agent_call(
            agent="SimulationAgent",
            policy=SESSION_SIMULATION_REQUIRED,
            call=invoke,
            trace_id=context.trace_id,
            on_failure=context.record_failure,
        )
        response = outcome.require_value()
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
            status="success",
            simulation_agent_version=self.version,
            **self.telemetry.simulation_fields(response),
        )
        return context
