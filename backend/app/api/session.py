# social-lab/backend/app/api/session.py
# 2026/07/01

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthUser, optional_current_user
from app.services.session_orchestrator import SessionOrchestrator
from app.services.persistence import PersistenceService
from app.llm.client import LLMClientError
from app.schemas.session import SessionMessageRequest, SessionMessageResponse


router = APIRouter(prefix="/api/session", tags=["session"])

orchestrator = SessionOrchestrator()

@router.post("/message", response_model=SessionMessageResponse)
async def send_message(
    request: SessionMessageRequest,
    user: AuthUser | None = Depends(optional_current_user),
) -> SessionMessageResponse:
    """
    发送一轮模拟对话。

    当前流程：
    1. SimulationAgent 生成目标人物回复；
    2. StateAgent 评估本轮关系状态变化；
    3. SessionOrchestrator 合并并返回结果。
    """

    try:
        result = await orchestrator.handle_message(request)

        if user is not None:
            try:
                store = PersistenceService()
                session_id = request.session_id or store.create_session(
                    user=user,
                    scenario=request.scenario,
                    goal=request.goal,
                    persona_id=request.persona_id,
                )
                store.save_message(
                    session_id=session_id,
                    role="user",
                    content=request.user_message,
                )
                store.save_message(
                    session_id=session_id,
                    role=result.target_message.role,
                    content=result.target_message.content,
                )
                store.save_relationship_state(
                    session_id=session_id,
                    state=result.updated_state,
                )
                return result.model_copy(
                    update={"session_id": session_id, "saved": True}
                )
            except Exception:
                return result.model_copy(update={"saved": False})

        return result
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
