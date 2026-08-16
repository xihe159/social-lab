from __future__ import annotations

from fastapi import APIRouter

from app.agents.failure_policies import DIRECT_AGENT_REQUIRED
from app.agents.strategy_agent import StrategyAgent
from app.api.error_handling import to_agent_http_exception
from app.core.agent_failure import AgentExecutionError, run_agent_call
from app.schemas.strategy import TargetResponseGuidance, TargetResponseStrategyRequest

router = APIRouter(prefix="/api/session", tags=["strategy"])
strategy_agent = StrategyAgent(mode="shadow")


@router.post("/strategy", response_model=TargetResponseGuidance)
async def create_strategy(request: TargetResponseStrategyRequest):
    try:
        outcome = await run_agent_call(
            agent="StrategyAgent",
            policy=DIRECT_AGENT_REQUIRED,
            call=lambda: strategy_agent.run(request),
            trace_id=request.trace_id,
        )
        return outcome.require_value()
    except AgentExecutionError as exc:
        raise to_agent_http_exception(exc) from exc
