from fastapi import APIRouter

from app.agents.coach_agent import CoachAgent
from app.api.error_handling import to_agent_http_exception
from app.core.agent_failure import AgentExecutionError
from app.schemas.report import ReportRequest, ReportResponse

router = APIRouter(prefix="/api/session", tags=["report"])
coach_agent = CoachAgent()


@router.post("/report", response_model=ReportResponse)
async def create_report(request: ReportRequest) -> ReportResponse:
    try:
        return await coach_agent.run(request)
    except AgentExecutionError as exc:
        raise to_agent_http_exception(exc) from exc
