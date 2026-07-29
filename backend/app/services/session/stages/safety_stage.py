from __future__ import annotations

from typing import Any

from app.schemas.safety import SafetyCheckRequest
from app.services.session.context import SessionExecutionContext
from app.services.session.policies import build_blocked_response, should_block
from app.services.session.telemetry import SessionTelemetry


class SafetyStage:
    """安全检查是 REQUIRED Stage；异常直接向上抛出。"""

    def __init__(self, agent: Any, telemetry: SessionTelemetry):
        self.agent = agent
        self.telemetry = telemetry

    async def execute(
        self,
        context: SessionExecutionContext,
    ) -> SessionExecutionContext:
        request = context.request
        started_at = self.telemetry.agent_started(
            context,
            agent="SafetyAgent",
            context="session_message",
            message_count=len(request.messages),
            has_memory=request.memory is not None,
            user_message_length=len(request.user_message),
        )

        result = await self.agent.run(
            SafetyCheckRequest(
                context="session_message",
                scenario=request.scenario,
                goal=request.goal,
                outcome=request.outcome,
                persona=request.persona,
                messages=request.messages,
                user_message=request.user_message,
                current_memory=request.memory,
            )
        )
        context.safety_result = result

        self.telemetry.agent_finished(
            context,
            agent="SafetyAgent",
            started_at=started_at,
            allowed=result.allowed,
            action=result.action,
            risk_level=result.risk_level,
            risk_types=result.risk_types,
            should_redact=result.should_redact,
            redacted_fields=result.redacted_fields,
        )

        if should_block(result):
            context.response = build_blocked_response(
                request=request,
                safety_result=result,
            )
            context.state_delta = context.response.simulation.state_delta
            context.risk_flags = list(context.response.simulation.risk_flags)
            context.blocked = True

        return context
