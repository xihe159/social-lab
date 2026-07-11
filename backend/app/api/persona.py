# social-lab/backend/app/api/persona.py
# 2026/07/04

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthUser, optional_current_user
from app.agents.persona_agent import PersonaAgent
from app.agents.safety_agent import SafetyAgent

from app.llm.client import LLMClientError

from app.schemas.persona import PersonaCreateRequest, PersonaCreateResponse
from app.schemas.safety import SafetyCheckRequest
from app.services.persistence import PersistenceService

router = APIRouter(prefix="/api/persona", tags=["persona"])

safety_agent = SafetyAgent()
persona_agent = PersonaAgent()

@router.post("/create", response_model=PersonaCreateResponse)
async def create_persona(
    request: PersonaCreateRequest,
    user: AuthUser | None = Depends(optional_current_user),
):
    try:
        safety_result = await safety_agent.run(
            SafetyCheckRequest(
                context="persona_create",
                scenario=request.scenario,
                goal=request.goal,
                outcome=request.outcome,
                role=request.role,
                relation=request.relation,
                habit=request.habit,
                chatLog=request.chatLog,
            )
        )

        if (
            not safety_result.allowed
            or safety_result.action == "block"
            or safety_result.risk_level == "high"
        ):
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "输入包含较高安全风险，已阻止人物画像生成。",
                    "safety": safety_result.model_dump(),
                },
            )

        result = await persona_agent.run(request)

        if user is not None:
            try:
                persona_id = PersistenceService().save_persona(
                    user=user,
                    scenario=request.scenario,
                    role=request.role,
                    goal=request.goal,
                    persona=result.persona,
                )
                return result.model_copy(
                    update={"persona_id": persona_id, "saved": True}
                )
            except Exception:
                return result.model_copy(update={"saved": False})

        return result

    except HTTPException:
        raise

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
