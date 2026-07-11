from fastapi import APIRouter, HTTPException

from app.agents.coach_agent import CoachAgent
from app.core.identity import validate_anonymous_user_id
from app.llm.client import LLMClientError
from app.schemas.report import ReportRequest, ReportResponse
from app.services.cloudbase import CloudBaseError
from app.services.persistence import get_persistence


router = APIRouter(prefix="/api/session", tags=["report"])

coach_agent = CoachAgent()

@router.post("/report", response_model=ReportResponse)
async def create_report(request: ReportRequest) -> ReportResponse:
    """
    生成沟通模拟报告。

    输入场景、目标、persona 和完整对话记录，
    由 CoachAgent 输出成功率、风险、问题、改写话术和下一步建议。
    """

    try:
        anonymous_id = validate_anonymous_user_id(request.user_id)
        persistence = get_persistence()
        session_id = persistence.ensure_session(
            anonymous_id,
            scenario=request.scenario,
            goal=request.goal,
            persona_id=request.persona_id,
            session_id=request.session_id,
        )
        response = await coach_agent.run(request)
        report_id = None
        if session_id:
            report_id = persistence.save_report(anonymous_id, session_id, response)
        return response.model_copy(
            update={
                "report_id": report_id,
                "saved": bool(report_id),
            }
        )
    except HTTPException:
        raise
    except CloudBaseError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"CloudBase 保存 Report 失败：{exc}",
        ) from exc
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
