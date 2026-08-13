from __future__ import annotations

from fastapi import APIRouter

from app.agents.evaluation_agent import EvaluationAgent
from app.agents.failure_policies import DIRECT_AGENT_REQUIRED
from app.api.error_handling import to_agent_http_exception
from app.core.agent_failure import AgentExecutionError, run_agent_call
from app.schemas.evaluation import SimulationEvaluationRequest, SimulationEvaluationResponse

router = APIRouter(prefix="/api/session", tags=["evaluation"])
evaluation_agent = EvaluationAgent()


@router.post(
    "/evaluate",
    response_model=SimulationEvaluationResponse,
    operation_id="evaluate_simulation_fidelity_v2",
)
async def evaluate_session(request: SimulationEvaluationRequest):
    try:
        outcome = await run_agent_call(
            agent="EvaluationAgent",
            policy=DIRECT_AGENT_REQUIRED,
            call=lambda: evaluation_agent.run(request),
            trace_id=request.trace_id,
        )
        return outcome.require_value()
    except AgentExecutionError as exc:
        raise to_agent_http_exception(exc) from exc
