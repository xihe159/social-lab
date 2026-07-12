from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthUser, optional_current_user
from app.agents.coach_agent import CoachAgent
from app.llm.client import LLMClientError
from app.schemas.report import ReportRequest, ReportResponse
from app.services.persistence import PersistenceService


router = APIRouter(prefix="/api/session", tags=["report"])

coach_agent = CoachAgent()

@router.post("/report", response_model=ReportResponse)
async def create_report(
    request: ReportRequest,
    user: AuthUser | None = Depends(optional_current_user),
) -> ReportResponse:
    """
    生成沟通模拟报告。

    输入场景、目标、persona 和完整对话记录，
    由 CoachAgent 输出成功率、风险、问题、改写话术和下一步建议。
    """

    try:
        result = await coach_agent.run(request)

        if user is not None:
            try:
                store = PersistenceService()
                session_id = request.session_id or store.create_session(
                    user=user,
                    scenario=request.scenario,
                    goal=request.goal,
                    persona_id=request.persona_id,
                    status="completed",
                )
                if not request.session_id:
                    for message in request.messages:
                        store.save_message(
                            session_id=session_id,
                            role=message.role,
                            content=message.content,
                        )
                report_id = store.save_report(session_id=session_id, report=result)
                store.save_relationship_state(
                    session_id=session_id,
                    state=request.persona.state,
                )
                return result.model_copy(
                    update={"report_id": report_id, "saved": True}
                )
            except Exception:
                return result.model_copy(update={"saved": False})

        return result
    except LLMClientError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"CoachAgent 调用 LLM 失败：{exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"CoachAgent 处理失败：{exc}",
        ) from exc
