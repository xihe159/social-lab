from fastapi import APIRouter, HTTPException

from app.agents.failure_policies import DIRECT_AGENT_REQUIRED, SAFETY_LLM_ENRICHMENT_DEGRADED
from app.agents.persona_agent import PersonaAgent
from app.agents.policy_agents import PolicySafetyAgent
from app.api.error_handling import to_agent_http_exception
from app.core.agent_failure import AgentExecutionError, run_agent_call
from app.schemas.persona import PersonaCreateRequest, PersonaCreateResponse
from app.schemas.safety import SafetyCheckRequest

router = APIRouter(prefix="/api/persona", tags=["persona"])
safety_agent = PolicySafetyAgent()
persona_agent = PersonaAgent()


@router.post("/create", response_model=PersonaCreateResponse)
async def create_persona(request: PersonaCreateRequest):
    safety_request = SafetyCheckRequest(
        context="persona_create",
        scenario=request.scenario,
        goal=request.goal,
        outcome=request.outcome,
        role=request.role,
        relation=request.relation,
        habit=request.habit,
        chatLog=request.chatLog,
    )
    try:
        rule_result = safety_agent.rule_check(safety_request)
        if rule_result.risk_level == "high" or rule_result.action == "block":
            safety_result = rule_result
        else:
            safety_outcome = await run_agent_call(
                agent="SafetyAgent.LLMEnrichment",
                policy=SAFETY_LLM_ENRICHMENT_DEGRADED,
                call=lambda: safety_agent.enrich(safety_request, rule_result=rule_result),
                fallback=lambda: rule_result,
            )
            safety_result = safety_outcome.require_value()

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

        outcome = await run_agent_call(
            agent="PersonaAgent",
            policy=DIRECT_AGENT_REQUIRED,
            call=lambda: persona_agent.run(request),
        )
        return outcome.require_value()
    except HTTPException:
        raise
    except AgentExecutionError as exc:
        raise to_agent_http_exception(exc) from exc
