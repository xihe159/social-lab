from fastapi import APIRouter, HTTPException

from app.agents.simulation_agent import SimulationAgent
from app.llm.client import LLMClientError
from app.schemas.session import SessionMessageRequest, SessionMessageResponse


router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("/message", response_model=SessionMessageResponse)
async def send_message(request: SessionMessageRequest) -> SessionMessageResponse:
    """
    发送一轮模拟对话。

    输入当前 persona、历史消息和用户最新发言，
    由 SimulationAgent 生成目标人物回复，并返回更新后的关系状态。
    """

    try:
        agent = SimulationAgent()
        return await agent.run(request)
    except LLMClientError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"SimulationAgent 调用 LLM 失败：{exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"SimulationAgent 处理失败：{exc}",
        ) from exc
