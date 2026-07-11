from fastapi import APIRouter, HTTPException

from app.agents.coach_agent import CoachAgent
from app.llm.client import LLMClientError
from app.schemas.report import ReportRequest, ReportResponse


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
        return await coach_agent.run(request)
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
