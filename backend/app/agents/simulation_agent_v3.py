from __future__ import annotations

import asyncio
import logging
from hashlib import sha256
from uuid import uuid4

from app.agents.evaluation_agent import EvaluationAgent
from app.agents.simulation_agent import SimulationAgentV1
from app.agents.strategy_agent import StrategyAgent
from app.schemas.evaluation import (
    SessionEvaluationMeta,
    SimulationEvaluationRequest,
    SimulationEvaluationResult,
)
from app.schemas.memory import SessionMemory
from app.schemas.session import (
    SessionMessageRequest,
    SessionMessageResponse,
    SessionStrategyMeta,
)
from app.schemas.simulation_turn import SessionRuntimeMeta
from app.schemas.strategy import (
    ResponseMode,
    ResponseModeHypothesis,
    StrategyMessage,
    TargetInterpretation,
    TargetResponseGuidance,
    TargetResponseStrategyRequest,
    ToneRange,
)
from app.services.persona_v2_adapter import compile_legacy_persona
from app.services.simulation_state_service import create_initial_simulation_state


logger = logging.getLogger(__name__)
STRATEGY_GRACE_SECONDS = 3.0


class SimulationAgentV3:
    """V1-simulation-first pipeline with advisory Strategy and audit-only Evaluation.

    The visible reply and relationship delta always come from the original V1
    SimulationAgent. Strategy never selects or rewrites the action. Evaluation
    runs after the candidate is fixed and cannot replace the current reply.
    """

    version = "v3.0-v1-core-advisory-audit"

    def __init__(
        self,
        *,
        simulation_core: SimulationAgentV1 | None = None,
        strategy_agent: StrategyAgent | None = None,
        evaluation_agent: EvaluationAgent | None = None,
    ) -> None:
        self.simulation_core = simulation_core or SimulationAgentV1()
        self.strategy_agent = strategy_agent or StrategyAgent(mode="active")
        self.evaluation_agent = evaluation_agent or EvaluationAgent()
        self._background_tasks: set[asyncio.Task[None]] = set()

    async def run(
        self,
        request: SessionMessageRequest,
        *,
        defer_background=None,
    ) -> SessionMessageResponse:
        persona_id = request.persona_id or _stable_persona_id(request)
        session_id = request.session_id or _stable_session_id(request, persona_id)
        trace_id = f"trace_{uuid4().hex}"
        turn_id = f"turn_{len(request.messages) + 1}"

        persona_v2 = (
            request.persona_v2.model_copy(
                deep=True,
                update={"persona_id": persona_id},
            )
            if request.persona_v2 is not None
            else compile_legacy_persona(
                request.persona,
                persona_id=persona_id,
                role=request.role,
                relation=request.relation,
                scenario=request.scenario,
            )
        )
        state = request.simulation_state or create_initial_simulation_state(
            persona_v2,
            session_id=session_id,
        )
        strategy_request = TargetResponseStrategyRequest(
            trace_id=trace_id,
            session_id=session_id,
            turn_id=turn_id,
            scenario=request.scenario,
            user_goal=request.goal,
            persona_snapshot=persona_v2,
            relationship_state=state.relationship_state,
            session_memory=request.memory,
            recent_messages=[
                StrategyMessage(role=item.role, content=item.content)
                for item in request.messages[-6:]
            ],
            user_message=request.user_message,
        )

        # Strategy and the original Simulation core run independently. The
        # Strategy result cannot enter the V1 generation prompt.
        simulation_task = asyncio.create_task(self.simulation_core.run(request))
        strategy_task = asyncio.create_task(
            self._guidance_with_fallback(strategy_request)
        )
        try:
            response = await simulation_task
        except Exception:
            strategy_task.cancel()
            raise
        try:
            guidance, strategy_fallback_used = await asyncio.wait_for(
                strategy_task,
                timeout=STRATEGY_GRACE_SECONDS,
            )
        except TimeoutError:
            logger.warning(
                "v3_strategy_timed_out_without_affecting_simulation",
                extra={"session_id": session_id, "turn_id": turn_id},
            )
            guidance = _fallback_guidance(strategy_request)
            strategy_fallback_used = True

        inferred_mode, final_action = _infer_visible_reaction(
            response.simulation.reply,
            response.simulation.attitude,
        )
        guidance_followed = _modes_are_compatible(
            guidance.recommended_mode,
            inferred_mode,
        )
        response.strategy_meta = SessionStrategyMeta(
            policy_id=guidance.guidance_id,
            strategy_action=guidance.recommended_mode.value,
            simulation_action=final_action,
            confidence=guidance.confidence,
            guidance_id=guidance.guidance_id,
            recommended_mode=guidance.recommended_mode.value,
            final_action=final_action,
            decision_confidence=0.0,
            guidance_followed=guidance_followed,
            guidance_deviation_reason=(
                ""
                if guidance_followed
                else "V3 保留原始 Simulation 人物反应；Strategy 仅用于对照。"
            ),
            persona_evidence_refs=guidance.persona_evidence_refs,
            memory_evidence_refs=guidance.memory_evidence_refs,
            prompt_version=getattr(
                self.strategy_agent,
                "prompt_version",
                "strategy-v2.5-v21-guidance",
            ),
            fallback_used=strategy_fallback_used,
        )
        response.evaluation_meta = SessionEvaluationMeta(
            execution_mode="background",
            background_scheduled=True,
        )
        response.runtime_meta = SessionRuntimeMeta(
            strategy_fallback_used=strategy_fallback_used,
        )

        evaluation_request = _build_evaluation_request(
            request=request,
            response=response,
            persona_v2=persona_v2,
            relationship_state=state.relationship_state,
            guidance=guidance,
            trace_id=trace_id,
            session_id=session_id,
            turn_id=turn_id,
            strategy_prompt_version=response.strategy_meta.prompt_version,
            evaluation_prompt_version=getattr(
                self.evaluation_agent,
                "prompt_version",
                "evaluation-v2.5-v21-hard-errors-only",
            ),
        )
        if defer_background is not None:
            defer_background(self._run_evaluation_audit, evaluation_request)
        else:
            task = asyncio.create_task(
                self._run_evaluation_audit(evaluation_request)
            )
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        return response

    async def _guidance_with_fallback(
        self,
        request: TargetResponseStrategyRequest,
    ) -> tuple[TargetResponseGuidance, bool]:
        try:
            return await self.strategy_agent.run(request), False
        except Exception:
            logger.exception(
                "v3_strategy_failed_without_affecting_simulation",
                extra={"session_id": request.session_id, "turn_id": request.turn_id},
            )
            return _fallback_guidance(request), True

    async def _run_evaluation_audit(
        self,
        request: SimulationEvaluationRequest,
    ) -> None:
        try:
            result = await self.evaluation_agent.run(request)
        except Exception:
            logger.exception(
                "v3_evaluation_audit_failed_without_affecting_reply",
                extra={"session_id": request.session_id, "turn_id": request.turn_id},
            )
            return
        log = logger.warning if result.hard_errors else logger.info
        log(
            "v3_evaluation_audit_finished",
            extra={
                "session_id": request.session_id,
                "turn_id": request.turn_id,
                "score": result.simulation_success_score,
                "hard_errors": [item.value for item in result.hard_errors],
                "intervened": False,
            },
        )


def _build_evaluation_request(
    *,
    request: SessionMessageRequest,
    response: SessionMessageResponse,
    persona_v2,
    relationship_state,
    guidance: TargetResponseGuidance,
    trace_id: str,
    session_id: str,
    turn_id: str,
    strategy_prompt_version: str,
    evaluation_prompt_version: str,
) -> SimulationEvaluationRequest:
    return SimulationEvaluationRequest(
        trace_id=trace_id,
        session_id=session_id,
        turn_id=turn_id,
        persona_snapshot=persona_v2,
        relationship_state_before=relationship_state,
        session_memory=request.memory or _empty_memory(),
        recent_messages=[
            StrategyMessage(role=item.role, content=item.content)
            for item in request.messages[-12:]
        ],
        user_message=request.user_message,
        response_guidance=guidance,
        simulation_result=SimulationEvaluationResult(
            reply=response.simulation.reply,
            attitude=response.simulation.attitude,
            emotion=response.simulation.emotion,
            perceived_user_tone=response.simulation.perceived_user_tone,
            state_delta=response.simulation.state_delta.model_dump(),
            risk_flags=response.simulation.risk_flags,
            policy_id=guidance.guidance_id,
            guidance_id=guidance.guidance_id,
            used_evidence_refs=[
                *guidance.persona_evidence_refs,
                *guidance.memory_evidence_refs,
            ],
        ),
        strategy_prompt_version=strategy_prompt_version,
        simulation_prompt_version="simulation-v1-original-core",
        evaluation_prompt_version=evaluation_prompt_version,
    )


def _fallback_guidance(
    request: TargetResponseStrategyRequest,
) -> TargetResponseGuidance:
    return TargetResponseGuidance(
        guidance_id=f"guidance_v3_fallback_{request.turn_id}",
        interpretation=TargetInterpretation(
            perceived_intent="暂时无法稳定识别。",
            perceived_tone="中性或不确定。",
            salient_point="保留原始 Simulation 人物反应。",
            perceived_concern="Strategy 服务暂时不可用。",
        ),
        possible_response_modes=[
            ResponseModeHypothesis(
                mode=ResponseMode.ENGAGE,
                probability=1.0,
                reason="回退 Guidance 不对人物回复施加约束。",
            )
        ],
        recommended_mode=ResponseMode.ENGAGE,
        communication_goal="记录原始人物反应。",
        required_content=[],
        forbidden_content=["虚构人物事实"],
        tone_range=ToneRange(
            warmth_min=0,
            warmth_max=100,
            directness_min=0,
            directness_max=100,
            formality=50,
            emotional_intensity_max=100,
            preferred_length="medium",
        ),
        persona_evidence_refs=[],
        memory_evidence_refs=[],
        confidence=0.0,
        uncertainty_notes=["Strategy 失败，未干预 Simulation。"],
    )


def _infer_visible_reaction(reply: str, attitude: str) -> tuple[ResponseMode, str]:
    text = f"{reply} {attitude}".lower()
    if any(marker in text for marker in ("到这里", "不想继续", "别再联系")):
        return ResponseMode.END_CONVERSATION, "END_CONVERSATION"
    if any(marker in text for marker in ("边界", "不要再", "我不接受你这样")):
        return ResponseMode.SET_BOUNDARY, "SET_BOUNDARY"
    if any(marker in text for marker in ("不能答应", "没办法答应", "不同意", "拒绝")):
        return ResponseMode.DECLINE, "REPLY_NORMAL"
    if "?" in reply or "？" in reply:
        return ResponseMode.SEEK_INFORMATION, "ASK_CLARIFICATION"
    if any(marker in text for marker in ("可以，但", "可以但", "如果", "先把")):
        return ResponseMode.CONDITIONAL_SUPPORT, "REPLY_NORMAL"
    if len(reply.strip()) <= 12:
        return ResponseMode.ENGAGE, "REPLY_BRIEF"
    return ResponseMode.ENGAGE, "REPLY_NORMAL"


def _modes_are_compatible(recommended: ResponseMode, actual: ResponseMode) -> bool:
    if recommended == actual:
        return True
    support = {
        ResponseMode.CONDITIONAL_SUPPORT,
        ResponseMode.LIMITED_SUPPORT,
        ResponseMode.ENGAGE,
    }
    return recommended in support and actual in support


def _empty_memory() -> SessionMemory:
    return SessionMemory(
        conversation_summary="",
        user_strategy_pattern=[],
        target_sensitive_points=[],
        resolved_points=[],
        unresolved_points=[],
        important_events=[],
        next_suggested_focus="",
    )


def _stable_persona_id(request: SessionMessageRequest) -> str:
    value = f"{request.persona.title}|{request.persona.style}|{request.role}"
    return f"persona_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def _stable_session_id(request: SessionMessageRequest, persona_id: str) -> str:
    value = f"{persona_id}|{request.scenario}|{request.goal}"
    return f"session_{sha256(value.encode('utf-8')).hexdigest()[:16]}"
