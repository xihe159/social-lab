# social-lab/backend/app/api/session.py
# 2026/07/01

from fastapi import APIRouter, HTTPException

from app.core.identity import validate_anonymous_user_id
from app.services.session_orchestrator import SessionOrchestrator
from app.services.cloudbase import CloudBaseError
from app.services.persistence import get_persistence
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
        anonymous_id = validate_anonymous_user_id(request.user_id)
        persistence = get_persistence()
        session_id = persistence.ensure_session(
            anonymous_id,
            scenario=request.scenario,
            goal=request.goal,
            persona_id=request.persona_id,
            session_id=request.session_id,
        )

        result = await orchestrator.handle_message(request)

        if session_id:
            persistence.save_message(
                anonymous_id,
                session_id,
                request.latest_chat_message(),
            )
            persistence.save_message(
                anonymous_id,
                session_id,
                result.target_message,
            )
            persistence.save_relationship_state(
                anonymous_id,
                session_id,
                result.updated_state.model_dump(),
            )

        return result.model_copy(
            update={
                "session_id": session_id,
                "saved": bool(session_id),
            }
        )
    except HTTPException:
        raise
    except CloudBaseError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"CloudBase 保存 Session 失败：{exc}",
        ) from exc
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
