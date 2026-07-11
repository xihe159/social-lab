# social-lab/backend/app/api/persona.py
# 2026/07/04

from fastapi import APIRouter, HTTPException

from app.agents.persona_agent import PersonaAgent
from app.agents.safety_agent import SafetyAgent
from app.core.identity import validate_anonymous_user_id

from app.llm.client import LLMClientError

from app.schemas.persona import PersonaCreateRequest, PersonaCreateResponse
from app.schemas.safety import SafetyCheckRequest
from app.services.cloudbase import CloudBaseError
from app.services.persistence import get_persistence

router = APIRouter(prefix="/api/persona", tags=["persona"])

safety_agent = SafetyAgent()
persona_agent = PersonaAgent()

@router.post("/create", response_model=PersonaCreateResponse)
async def create_persona(request: PersonaCreateRequest):
    try:
        anonymous_id = validate_anonymous_user_id(request.user_id)
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

        response = await persona_agent.run(request)
        persona_id = get_persistence().save_persona(
            anonymous_id,
            request,
            response.persona,
        )
        return response.model_copy(
            update={
                "persona_id": persona_id,
                "saved": bool(persona_id),
            }
        )

    except HTTPException:
        raise

    except CloudBaseError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"CloudBase 保存 Persona 失败：{exc}",
        ) from exc

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
