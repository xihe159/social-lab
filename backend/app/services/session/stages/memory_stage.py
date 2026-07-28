from __future__ import annotations

from typing import Any

from app.llm.client import LLMClientError
from app.schemas.memory import MemoryUpdateRequest
from app.services.session.context import SessionExecutionContext
from app.services.session.telemetry import SessionTelemetry


class MemoryStage:
    """MemoryAgent 是 FALLBACK Stage；失败时保留上一轮 memory。"""

    def __init__(self, agent: Any, telemetry: SessionTelemetry):
        self.agent = agent
        self.telemetry = telemetry

    async def execute(
        self,
        context: SessionExecutionContext,
    ) -> SessionExecutionContext:
        request = context.request
        response = context.require_response()
        state_delta = context.require_state_delta()

        started_at = self.telemetry.agent_started(
            context,
            agent="MemoryAgent",
            has_previous_memory=request.memory is not None,
            risk_flag_count=len(context.risk_flags),
        )

        try:
            memory_response = await self.agent.run(
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
            )
            response.updated_memory = memory_response.memory

            memory = memory_response.memory
            self.telemetry.agent_finished(
                context,
                agent="MemoryAgent",
                started_at=started_at,
                status="success",
                has_memory=memory is not None,
                conversation_summary_length=len(
                    memory.conversation_summary
                ),
                user_strategy_pattern_count=len(
                    memory.user_strategy_pattern
                ),
                target_sensitive_point_count=len(
                    memory.target_sensitive_points
                ),
                resolved_point_count=len(memory.resolved_points),
                unresolved_point_count=len(memory.unresolved_points),
                important_event_count=len(memory.important_events),
                has_memory_reason=bool(
                    memory_response.memory_reason.strip()
                ),
                new_fact_count=len(memory_response.new_facts),
                has_next_focus=bool(memory_response.next_focus.strip()),
            )
            return context

        except LLMClientError:
            self.telemetry.agent_fallback(
                context,
                agent="MemoryAgent",
                started_at=started_at,
                fallback="use_previous_memory",
                error_kind="llm",
            )
        except Exception:
            self.telemetry.agent_fallback(
                context,
                agent="MemoryAgent",
                started_at=started_at,
                fallback="use_previous_memory",
                error_kind="unexpected",
            )

        response.updated_memory = request.memory
        return context
