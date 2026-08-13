from fastapi import APIRouter, BackgroundTasks

from app.api.error_handling import to_agent_http_exception
from app.core.agent_failure import AgentExecutionError
from app.schemas.runtime_metrics import RuntimeMetricsSnapshot
from app.schemas.session import SessionMessageRequest, SessionMessageResponse
from app.services.agent_runtime_metrics import agent_runtime_metrics_store
from app.services.session_orchestrator import SessionOrchestrator

router = APIRouter(prefix="/api/session", tags=["session"])
orchestrator = SessionOrchestrator()


@router.post("/message", response_model=SessionMessageResponse)
async def send_message(request: SessionMessageRequest, background_tasks: BackgroundTasks) -> SessionMessageResponse:
    try:
        return await orchestrator.handle_message(
            request,
            defer_background=background_tasks.add_task,
        )
    except AgentExecutionError as exc:
        raise to_agent_http_exception(exc) from exc


@router.get("/metrics", response_model=RuntimeMetricsSnapshot)
async def get_runtime_metrics() -> RuntimeMetricsSnapshot:
    return agent_runtime_metrics_store.snapshot()
