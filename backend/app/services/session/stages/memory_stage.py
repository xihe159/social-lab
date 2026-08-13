from __future__ import annotations

from typing import Any

from app.agents.failure_policies import SESSION_MEMORY_DEGRADED
from app.core.agent_failure import run_agent_call
from app.schemas.memory import MemoryUpdateRequest
from app.services.session.context import SessionExecutionContext
from app.services.session.telemetry import SessionTelemetry


class MemoryStage:
    """MemoryAgent 是 DEGRADED：失败时保留上一轮 memory。"""

    def __init__(self, agent: Any, telemetry: SessionTelemetry):
        self.agent = agent
        self.telemetry = telemetry

    async def execute(self, context: SessionExecutionContext) -> SessionExecutionContext:
        request = context.request
        response = context.require_response()
        state_delta = context.require_state_delta()
        started_at = self.telemetry.agent_started(
            context,
            agent="MemoryAgent",
            has_previous_memory=request.memory is not None,
            risk_flag_count=len(context.risk_flags),
        )
        outcome = await run_agent_call(
            agent="MemoryAgent",
            policy=SESSION_MEMORY_DEGRADED,
            call=lambda: self.agent.run(
                MemoryUpdateRequest(
                    scenario=request.scenario,
                    goal=request.goal,
                    outcome=request.outcome,
                    persona=request.persona,
                    messages=request.messages,
                    user_message=request.user_message,
                    target_reply=response.target_message.content,
                    state_delta=state_delta,
                    risk_flags=context.risk_flags,
                    current_memory=request.memory,
                )
            ),
            fallback=lambda: None,
            trace_id=context.trace_id,
            on_failure=context.record_failure,
        )
        memory_response = outcome.value
        if memory_response is None:
            response.updated_memory = request.memory
            self.telemetry.agent_finished(
                context,
                agent="MemoryAgent",
                started_at=started_at,
                status="degraded",
                fallback=SESSION_MEMORY_DEGRADED.fallback_name,
                failure_kind=outcome.failure.kind.value if outcome.failure else None,
            )
            return context

        response.updated_memory = memory_response.memory
        memory = memory_response.memory
        self.telemetry.agent_finished(
            context,
            agent="MemoryAgent",
            started_at=started_at,
            status="success",
            has_memory=memory is not None,
            conversation_summary_length=len(memory.conversation_summary),
            user_strategy_pattern_count=len(memory.user_strategy_pattern),
            target_sensitive_point_count=len(memory.target_sensitive_points),
            resolved_point_count=len(memory.resolved_points),
            unresolved_point_count=len(memory.unresolved_points),
            important_event_count=len(memory.important_events),
            has_memory_reason=bool(memory_response.memory_reason.strip()),
            new_fact_count=len(memory_response.new_facts),
            has_next_focus=bool(memory_response.next_focus.strip()),
        )
        return context
