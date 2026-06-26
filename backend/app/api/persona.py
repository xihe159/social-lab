from fastapi import APIRouter, HTTPException

from app.agents.persona_agent import PersonaAgent
from app.llm.client import LLMClientError
from app.schemas.persona import PersonaCreateRequest, PersonaCreateResponse


router = APIRouter(prefix="/api/persona", tags=["persona"])


@router.post("/create", response_model=PersonaCreateResponse)
async def create_persona(request: PersonaCreateRequest) -> PersonaCreateResponse:
    """
    创建目标人物画像。

    输入用户的沟通场景、目标、对方身份、双方关系、沟通习惯和聊天记录，
    由 PersonaAgent 生成结构化 PersonaCreateResponse。
    """

    try:
        agent = PersonaAgent()
        return await agent.run(request)
    except LLMClientError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"PersonaAgent 调用 LLM 失败：{exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"PersonaAgent 处理失败：{exc}",
        ) from exc
