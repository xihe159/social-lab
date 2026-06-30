from fastapi import APIRouter, HTTPException

#G 20260929
from app.services.session_orchestrator import SessionOrchestrator
#G 20260929 #
from app.llm.client import LLMClientError
from app.schemas.session import SessionMessageRequest, SessionMessageResponse


router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("/message", response_model=SessionMessageResponse)
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
        # G 20260929
        orchestrator = SessionOrchestrator()
        # G 20260929
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
