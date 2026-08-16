from __future__ import annotations

from typing import Any

from app.agents.failure_policies import SESSION_STATE_DEGRADED
from app.agents.simulation_agent import apply_state_delta
from app.core.agent_failure import run_agent_call
from app.schemas.state import StateEvaluateRequest
from app.services.session.context import SessionExecutionContext
from app.services.session.policies import append_safety_warning_if_needed, merge_risk_flags
from app.services.session.telemetry import SessionTelemetry, safe_dump


class StateStage:
    """StateAgent 是 DEGRADED：失败时沿用 SimulationAgent 的 state_delta。"""

    def __init__(self, *, agent: Any, override_relationship_state: bool, telemetry: SessionTelemetry):
        self.agent = agent
        self.override_relationship_state = override_relationship_state
        self.telemetry = telemetry

    async def execute(self, context: SessionExecutionContext) -> SessionExecutionContext:
        request = context.request
        response = context.require_response()
        safety_result = context.require_safety_result()
        fallback_state_delta = context.require_state_delta()
        fallback_risk_flags = list(context.risk_flags)
        started_at = self.telemetry.agent_started(
            context,
            agent="StateAgent",
            fallback="simulation_agent_state_delta",
            override_relationship_state=self.override_relationship_state,
            has_current_dynamics=request.current_dynamics is not None,
        )

        outcome = await run_agent_call(
            agent="StateAgent",
            policy=SESSION_STATE_DEGRADED,
            call=lambda: self.agent.run(
                StateEvaluateRequest(
                    scenario=request.scenario,
                    goal=request.goal,
                    outcome=request.outcome,
                    persona=request.persona,
                    messages=request.messages,
                    user_message=request.user_message,
                    target_reply=response.target_message.content,
                    current_state=request.persona.state,
                    simulation_attitude=response.simulation.attitude,
                    simulation_emotion=response.simulation.emotion,
                    perceived_user_tone=response.simulation.perceived_user_tone,
                    current_dynamics=request.current_dynamics,
                )
            ),
            fallback=lambda: None,
            trace_id=context.trace_id,
            on_failure=context.record_failure,
        )
        evaluation = outcome.value
        if evaluation is None:
            context.state_delta = fallback_state_delta
            context.risk_flags = fallback_risk_flags
            self.telemetry.agent_finished(
                context,
                agent="StateAgent",
                started_at=started_at,
                status="degraded",
                fallback=SESSION_STATE_DEGRADED.fallback_name,
                failure_kind=outcome.failure.kind.value if outcome.failure else None,
            )
            return context

        risk_flags = merge_risk_flags(fallback_risk_flags, list(evaluation.risk_flags))
        append_safety_warning_if_needed(risk_flags=risk_flags, safety_result=safety_result)
        if self.override_relationship_state:
            state_delta = evaluation.state_delta
            response.simulation.state_delta = state_delta
            response.updated_state = apply_state_delta(state=request.persona.state, delta=state_delta)
        else:
            state_delta = fallback_state_delta
        response.simulation.risk_flags = risk_flags
        response.dynamics_update = evaluation.dynamics_update
        context.state_delta = state_delta
        context.risk_flags = risk_flags
        self.telemetry.agent_finished(
            context,
            agent="StateAgent",
            started_at=started_at,
            status="success",
            override_relationship_state=self.override_relationship_state,
            state_delta=safe_dump(state_delta),
            risk_flags=risk_flags,
            updated_state=safe_dump(response.updated_state),
            dynamics_delta=safe_dump(evaluation.dynamics_update.dynamics_delta),
            updated_dynamics=safe_dump(evaluation.dynamics_update.updated_dynamics),
        )
        return context
