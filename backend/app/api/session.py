# social-lab/backend/app/api/session.py
# 2026/07/01

from fastapi import APIRouter, HTTPException

from app.services.session_orchestrator import SessionOrchestrator
from app.llm.client import LLMClientError
from app.schemas.session import SessionMessageRequest, SessionMessageResponse


router = APIRouter(prefix="/api/session", tags=["session"])

orchestrator = SessionOrchestrator()

@router.post("/message", response_model=SessionMessageResponse)
async def send_message(request: SessionMessageRequest) -> SessionMessageResponse:
    """
    发送一轮模拟对话。

    当前流程：
    1. SimulationAgent 生成目标人物回复；
    2. StateAgent 评估本轮关系状态变化；
    3. SessionOrchestrator 合并并返回结果。
    """

    try:
        return await orchestrator.handle_message(request)
    except LLMClientError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"SessionOrchestrator 调用 LLM 失败：{exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"SessionOrchestrator 处理失败：{exc}",
        ) from exc
