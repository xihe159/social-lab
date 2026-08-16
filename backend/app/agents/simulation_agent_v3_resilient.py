from __future__ import annotations

import asyncio
import logging
from dataclasses import replace
from uuid import uuid4

from app.agents.failure_policies import (
    EVALUATION_AUDIT_BEST_EFFORT,
    SIMULATION_CORE_REQUIRED,
    STRATEGY_ADVISORY_DEGRADED,
)
from app.agents.fallbacks import fallback_strategy_guidance
from app.agents.simulation_agent_v3 import (
    SimulationAgentV3,
    _build_evaluation_request,
    _infer_visible_reaction,
    _modes_are_compatible,
    _stable_persona_id,
    _stable_session_id,
)
from app.core.agent_failure import AgentCallOutcome, run_agent_call
from app.schemas.evaluation import (
    SessionEvaluationMeta,
    SimulationEvaluationRequest,
    SimulationEvaluationResponse,
)
from app.schemas.session import (
    SessionMessageRequest,
    SessionMessageResponse,
    SessionStrategyMeta,
)
from app.schemas.simulation_turn import SessionRuntimeMeta
from app.schemas.strategy import (
    StrategyMessage,
    TargetResponseGuidance,
    TargetResponseStrategyRequest,
)
from app.services.evaluation_execution_policy import resolve_evaluation_execution_mode
from app.services.persona_v2_adapter import compile_legacy_persona
from app.services.simulation_state_service import create_initial_simulation_state

logger = logging.getLogger(__name__)

# Important: this is a grace period AFTER the simulation core has finished.
# Strategy starts concurrently with the core, matching the original V3 semantics.
STRATEGY_GRACE_SECONDS = 3.0


class ResilientSimulationAgentV3(SimulationAgentV3):
    """V3 behavior with auxiliary failures routed through AgentFailureRuntime.

    Ownership remains unchanged:
    - Simulation V1 core owns visible reply/state.
    - Strategy is advisory only.
    - Evaluation is audit-only and never rewrites the current turn.
    """

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

        # Both begin at the same time. Do NOT put STRATEGY_GRACE_SECONDS inside
        # Strategy's task here; that would count the core's execution time against
        # Strategy and changes original V3 behavior.
        core_task = asyncio.create_task(
            run_agent_call(
                agent="SimulationAgentV1Core",
                policy=SIMULATION_CORE_REQUIRED,
                call=lambda: self.simulation_core.run(request),
                trace_id=trace_id,
            )
        )
        strategy_task = asyncio.create_task(
            self.strategy_agent.run(strategy_request)
        )

        try:
            core_outcome = await core_task
            response = core_outcome.require_value()
        except BaseException:
            await _cancel_task(strategy_task)
            raise

        strategy_outcome = await _await_strategy_after_core(
            strategy_task=strategy_task,
            strategy_request=strategy_request,
            trace_id=trace_id,
        )
        guidance = strategy_outcome.require_value()
        strategy_fallback_used = strategy_outcome.degraded

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

        evaluation_mode = resolve_evaluation_execution_mode()

        if evaluation_mode == "development_sync":
            result = await self._run_evaluation_audit(evaluation_request)
            response.runtime_meta.evaluation_call_count = 1
            response.evaluation_meta = _sync_evaluation_meta(result)
            return response

        # V3 has no TurnDecisionResult, so it cannot safely call the V2
        # EvaluationExecutionPolicy.decide() contract. In production_hybrid,
        # keep V3 audit off the hot path and make that fact explicit in metadata.
        response.evaluation_meta = SessionEvaluationMeta(
            execution_mode="background",
            background_scheduled=True,
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

    async def _run_evaluation_audit(
        self,
        request: SimulationEvaluationRequest,
    ) -> SimulationEvaluationResponse | None:
        outcome = await run_agent_call(
            agent="EvaluationAgent",
            policy=EVALUATION_AUDIT_BEST_EFFORT,
            call=lambda: self.evaluation_agent.run(request),
            trace_id=request.trace_id,
        )
        if outcome.skipped:
            return None

        result = outcome.require_value()
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
        return result


async def _await_strategy_after_core(
    *,
    strategy_task: asyncio.Task[TargetResponseGuidance],
    strategy_request: TargetResponseStrategyRequest,
    trace_id: str,
) -> AgentCallOutcome[TargetResponseGuidance]:
    """Wait for Strategy only after the core reply is fixed.

    The 3-second grace begins here, not when Strategy started. This preserves
    original V3 concurrency semantics while still routing timeout/failure through
    the shared AgentFailureRuntime.
    """
    try:
        outcome = await run_agent_call(
            agent="StrategyAgent",
            policy=replace(
                STRATEGY_ADVISORY_DEGRADED,
                timeout_seconds=STRATEGY_GRACE_SECONDS,
            ),
            # Shield prevents asyncio.wait_for inside run_agent_call from
            # cancelling the underlying task before we classify/fallback.
            call=lambda: asyncio.shield(strategy_task),
            fallback=lambda: fallback_strategy_guidance(strategy_request),
            trace_id=trace_id,
        )
    except BaseException:
        await _cancel_task(strategy_task)
        raise

    if outcome.degraded and not strategy_task.done():
        await _cancel_task(strategy_task)
    return outcome


async def _cancel_task(task: asyncio.Task[object]) -> None:
    if task.done():
        # Retrieve a completed exception so asyncio does not emit
        # "Task exception was never retrieved".
        await asyncio.gather(task, return_exceptions=True)
        return
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


def _sync_evaluation_meta(
    result: SimulationEvaluationResponse | None,
) -> SessionEvaluationMeta:
    if result is None:
        return SessionEvaluationMeta(
            evaluated=False,
            execution_mode="synchronous",
            background_scheduled=False,
            evaluator_failed=True,
            final_evaluator_failed=True,
        )

    return SessionEvaluationMeta(
        evaluated=True,
        execution_mode="synchronous",
        background_scheduled=False,
        initial_evaluation_id=result.evaluation_id,
        final_evaluation_id=result.evaluation_id,
        initial_score=result.simulation_success_score,
        final_score=result.simulation_success_score,
        score_delta=0,
        initial_verdict=result.verdict,
        final_verdict=result.verdict,
        initial_failure_attribution=result.failure_attribution,
        final_failure_attribution=result.failure_attribution,
        hard_error_count=len(result.hard_errors),
    )
