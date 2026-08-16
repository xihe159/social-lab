from __future__ import annotations

import asyncio
import logging
from typing import Protocol
from uuid import uuid4

from app.agents.failure_policies import (
    EVALUATION_AUDIT_BEST_EFFORT,
    GENERATION_FINAL_DEGRADED,
    GENERATION_FIRST_ATTEMPT_BEST_EFFORT,
    SIMULATION_DECISION_DEGRADED,
    STRATEGY_ADVISORY_DEGRADED,
    TURN_ANALYSIS_DEGRADED,
)
from app.agents.simulation.response_generator import build_fallback_response
from app.core.agent_failure import run_agent_call
from app.schemas.evaluation import (
    EvaluationVerdict,
    FailureAttribution,
    SessionEvaluationMeta,
    SimulationEvaluationRequest,
    SimulationEvaluationResponse,
    SimulationEvaluationResult,
)
from app.schemas.evidence_retrieval import SessionEvidenceMeta
from app.schemas.feedback import InternalCorrection
from app.schemas.session import (
    ChatMessage,
    SessionActionResponse,
    SessionMessageResponse,
    SessionStrategyMeta,
    SimulationReply,
)
from app.schemas.simulation_adjustment import SessionAdjustmentMeta
from app.schemas.simulation_decision import DecisionMessage
from app.schemas.simulation_generation import GeneratedResponse, ResponseGenerationInput
from app.schemas.simulation_guidance import SimulationDecisionRequest
from app.schemas.simulation_turn import SafeTurnAnalysis, SessionRuntimeMeta, SimulationTurnRecord
from app.schemas.strategy import (
    StrategyMessage,
    TargetResponsePolicy,
    TargetResponseStrategyRequest,
)
from app.schemas.turn_state import TurnContextMessage, TurnStateAnalysisRequest
from app.services.persona_v2_adapter import compile_legacy_persona
from app.services.simulation_state_service import create_initial_simulation_state
from app.services.strategy_guidance import guidance_from_legacy_policy

from .context import SimulationCandidate, SimulationPipelineContext
from .runtime import measured_call, prompt_version, record_runtime_metric
from .services import SimulationPipelineServices
from .utils import (
    SILENT_ACTIONS,
    attitude_label,
    build_legacy_decision_result,
    digest_text,
    dominant_emotion,
    empty_session_memory,
    fallback_simulation_decision,
    fallback_strategy_guidance,
    fallback_turn_state_analysis,
    legacy_delta,
    perceived_tone,
    stable_persona_id,
    stable_session_id,
    status_text,
    style_adjustment_count,
    to_legacy_relationship_state,
    unique_strings,
)

logger = logging.getLogger(__name__)


class SimulationPipelineStage(Protocol):
    name: str

    async def execute(self, context: SimulationPipelineContext) -> SimulationPipelineContext:
        ...


class BaseStage:
    name = "base"

    def __init__(self, services: SimulationPipelineServices) -> None:
        self.services = services


class PrepareStage(BaseStage):
    name = "prepare"

    async def execute(self, context: SimulationPipelineContext) -> SimulationPipelineContext:
        request = context.request
        persona_id = (
            request.persona_id
            or (request.simulation_state.persona_id if request.simulation_state else None)
            or (request.persona_v2.persona_id if request.persona_v2 else None)
            or stable_persona_id(request)
        )
        session_id = (
            request.session_id
            or (request.simulation_state.session_id if request.simulation_state else None)
            or stable_session_id(request, persona_id)
        )
        adjustment_context = self.services.adjustment_manager.begin_turn(session_id)

        if request.persona_v2 is not None:
            persona_v2 = request.persona_v2.model_copy(
                deep=True,
                update={"persona_id": persona_id},
            )
        else:
            persona_v2 = compile_legacy_persona(
                request.persona,
                persona_id=persona_id,
                role=request.role,
                relation=request.relation,
                scenario=request.scenario,
            )

        current_state = request.simulation_state or create_initial_simulation_state(
            persona_v2,
            session_id=session_id,
        )
        recent_turns = [
            DecisionMessage(role=message.role, content=message.content)
            for message in request.messages[-6:]
        ]
        evidence_context = self.services.context_builder.build_evidence_context(
            persona_id=persona_id,
            user_message=request.user_message,
            state=current_state,
            top_k=4,
        )

        context.persona_id = persona_id
        context.session_id = session_id
        context.trace_id = f"trace_{uuid4().hex}"
        context.turn_id = f"turn_{current_state.conversation_state.turn_count + 1}"
        context.persona_v2 = persona_v2
        context.current_state = current_state
        context.recent_turns = recent_turns
        context.evidence_context = evidence_context
        context.retrieval = evidence_context.retrieval
        context.adjustment_context = adjustment_context
        context.active_adjustments = adjustment_context.profile
        context.resulting_adjustments = adjustment_context.profile
        context.adjustment_remaining_turns = adjustment_context.remaining_turns
        return context


class TurnAnalysisStage(BaseStage):
    name = "analyze_turn"

    async def execute(self, context: SimulationPipelineContext) -> SimulationPipelineContext:
        request = context.request
        current_state = context.require_current_state()
        analysis_request = TurnStateAnalysisRequest(
            persona=context.persona_v2,
            current_state=current_state,
            scenario=request.scenario,
            goal=request.goal,
            outcome=request.outcome or "",
            recent_turns=[
                TurnContextMessage(role=item.role, content=item.content)
                for item in request.messages[-6:]
            ],
            relevant_evidence=list(context.evidence_context.decision_evidence),
            user_message=request.user_message,
        )
        outcome = await run_agent_call(
            agent="TurnStateAnalyzer",
            policy=TURN_ANALYSIS_DEGRADED,
            call=lambda: measured_call(
                self.services.runtime_metrics,
                trace_id=context.trace_id,
                session_id=context.session_id,
                turn_id=context.turn_id,
                agent="TurnStateAnalyzer",
                version=prompt_version(
                    self.services.turn_state_analyzer,
                    "prompt_version",
                    "turn-state-v2.1",
                ),
                run_mode="synchronous",
                call=lambda: self.services.turn_state_analyzer.run(analysis_request),
            ),
            fallback=lambda: fallback_turn_state_analysis(current_state),
            trace_id=context.trace_id,
            on_failure=context.record_failure,
        )
        context.flags.turn_state_fallback_used = outcome.degraded
        context.turn_state_result = outcome.require_value()
        return context


class StrategyStage(BaseStage):
    name = "strategy_guidance"

    async def execute(self, context: SimulationPipelineContext) -> SimulationPipelineContext:
        request = context.request
        turn_state_result = context.require_turn_state()
        strategy_request = TargetResponseStrategyRequest(
            trace_id=context.trace_id,
            session_id=context.session_id,
            turn_id=context.turn_id,
            scenario=request.scenario,
            user_goal=request.goal,
            persona_snapshot=context.persona_v2,
            relationship_state=turn_state_result.updated_state.relationship_state,
            session_memory=request.memory,
            recent_messages=[
                StrategyMessage(role=item.role, content=item.content)
                for item in request.messages[-6:]
            ],
            user_message=request.user_message,
            turn_state_analysis=turn_state_result.analysis,
            simulation_adjustments=context.active_adjustments,
        )
        context.strategy_request = strategy_request

        legacy_response_policy = request.__dict__.get("response_policy")
        if request.response_guidance is not None:
            context.strategy_guidance = request.response_guidance.model_copy(deep=True)
            return context
        if legacy_response_policy is not None:
            context.strategy_guidance = guidance_from_legacy_policy(legacy_response_policy)
            return context

        outcome = await run_agent_call(
            agent="StrategyAgent",
            policy=STRATEGY_ADVISORY_DEGRADED,
            call=lambda: measured_call(
                self.services.runtime_metrics,
                trace_id=context.trace_id,
                session_id=context.session_id,
                turn_id=context.turn_id,
                agent="StrategyAgent",
                version=prompt_version(
                    self.services.strategy_agent,
                    "prompt_version",
                    "strategy-v2.5-v21-guidance",
                ),
                run_mode="synchronous",
                call=lambda: self.services.strategy_agent.run(strategy_request),
            ),
            fallback=lambda: fallback_strategy_guidance(strategy_request),
            trace_id=context.trace_id,
            on_failure=context.record_failure,
        )
        result = outcome.require_value()
        context.flags.strategy_fallback_used = outcome.degraded
        context.strategy_guidance = (
            guidance_from_legacy_policy(result)
            if isinstance(result, TargetResponsePolicy)
            else result
        )
        return context


class DecisionStage(BaseStage):
    name = "persona_decision"

    async def execute(self, context: SimulationPipelineContext) -> SimulationPipelineContext:
        request = context.request
        turn_state_result = context.require_turn_state()
        guidance = context.require_strategy_guidance()
        decision_request = SimulationDecisionRequest(
            persona=context.persona_v2,
            current_state=turn_state_result.updated_state,
            scenario=request.scenario,
            goal=request.goal,
            outcome=request.outcome or "",
            recent_turns=context.recent_turns,
            relevant_evidence=list(context.evidence_context.decision_evidence),
            session_memory=request.memory,
            user_message=request.user_message,
            turn_state_analysis=turn_state_result.analysis,
            strategy_guidance=guidance,
        )
        outcome = await run_agent_call(
            agent="SimulationDecisionEngine",
            policy=SIMULATION_DECISION_DEGRADED,
            call=lambda: measured_call(
                self.services.runtime_metrics,
                trace_id=context.trace_id,
                session_id=context.session_id,
                turn_id=context.turn_id,
                agent="SimulationDecisionEngine",
                version=prompt_version(
                    self.services.simulation_decision_engine,
                    "prompt_version",
                    "simulation-decision-v2.1",
                ),
                run_mode="synchronous",
                call=lambda: self.services.simulation_decision_engine.run(decision_request),
            ),
            fallback=lambda: fallback_simulation_decision(guidance),
            trace_id=context.trace_id,
            on_failure=context.record_failure,
        )
        context.flags.decision_fallback_used = outcome.degraded
        simulation_decision = outcome.require_value()

        decision_result = build_legacy_decision_result(
            turn_state_result=turn_state_result,
            simulation_decision=simulation_decision,
            user_message=request.user_message,
        )
        context.simulation_decision = simulation_decision
        context.decision_result = decision_result
        return context


class GenerationStage(BaseStage):
    name = "generate_response"

    async def execute(self, context: SimulationPipelineContext) -> SimulationPipelineContext:
        request = context.request
        decision_result = context.require_decision()
        guidance = context.require_strategy_guidance()
        response_policy = decision_result.decision.response_policy

        if response_policy.action in SILENT_ACTIONS:
            generated = GeneratedResponse(response_text="", response_action=response_policy.action)
            generation_input = None
        else:
            generation_input = ResponseGenerationInput(
                persona=context.persona_v2,
                current_state=decision_result.updated_state,
                response_policy=response_policy,
                strategy_policy_id=guidance.guidance_id,
                strategy_action=guidance.recommended_mode.value,
                strategy_guidance_id=guidance.guidance_id,
                recommended_mode=guidance.recommended_mode.value,
                strategy_evidence_refs=[
                    *guidance.persona_evidence_refs,
                    *guidance.memory_evidence_refs,
                ],
                recent_turns=context.recent_turns,
                user_message=request.user_message,
                relevant_linguistic_evidence=list(
                    context.evidence_context.linguistic_evidence
                ),
                simulation_adjustments=context.active_adjustments,
                generation_attempt=1,
            )
            generated = await self._generate_with_recovery(context, generation_input)

        context.generation_input = generation_input
        context.generated = generated
        context.candidate = SimulationCandidate(
            strategy_guidance=guidance,
            simulation_decision=context.simulation_decision,
            decision_result=decision_result,
            generation_input=generation_input,
            generated=generated,
        )
        return context

    async def _generate_with_recovery(
        self,
        context: SimulationPipelineContext,
        generation_input: ResponseGenerationInput,
    ) -> GeneratedResponse:
        async def invoke(input_value: ResponseGenerationInput) -> GeneratedResponse:
            return await measured_call(
                self.services.runtime_metrics,
                trace_id=context.trace_id,
                session_id=context.session_id,
                turn_id=context.turn_id,
                agent="SimulationResponseGenerator",
                version=prompt_version(
                    self.services.response_generator,
                    "prompt_version",
                    "simulation-v2.5-v21-persona-decision",
                ),
                run_mode="synchronous",
                call=lambda: self.services.response_generator.run(input_value),
            )

        first = await run_agent_call(
            agent="SimulationResponseGenerator",
            policy=GENERATION_FIRST_ATTEMPT_BEST_EFFORT,
            call=lambda: invoke(generation_input),
            trace_id=context.trace_id,
            on_failure=context.record_failure,
        )
        if not first.skipped:
            return first.require_value()

        context.flags.generator_retry_count = 1
        retry_input = generation_input.model_copy(
            deep=True,
            update={
                "generation_attempt": 2,
                "evaluation_correction": InternalCorrection(
                    keep=["保持原 Response Policy。"],
                    change=["重新生成合法、简洁且符合人物风格的回复。"],
                    must_not=["不得改变 Response Action 或人物状态。"],
                ),
            },
        )
        second = await run_agent_call(
            agent="SimulationResponseGenerator",
            policy=GENERATION_FINAL_DEGRADED,
            call=lambda: invoke(retry_input),
            fallback=lambda: build_fallback_response(
                generation_input.response_policy,
                strategy_action=generation_input.strategy_action,
            ),
            trace_id=context.trace_id,
            on_failure=context.record_failure,
        )
        context.flags.generator_fallback_used = second.degraded
        return second.require_value()


class EvaluationAuditStage(BaseStage):
    name = "evaluation_audit"

    async def execute(self, context: SimulationPipelineContext) -> SimulationPipelineContext:
        """
        Audit a fixed candidate. It never rewrites the current turn.

        This is the main behavioral simplification versus old V2: evaluator feedback is
        learned through bounded cross-turn adjustments, while response ownership stays
        with TurnAnalysis -> PersonaDecision -> ResponseGeneration.
        """
        candidate = context.candidate
        if candidate is None:
            raise RuntimeError("GenerationStage did not build candidate")

        meta = SessionEvaluationMeta()
        context.evaluation_meta = meta
        if context.flags.decision_fallback_used:
            meta.execution_mode = "not_run"
            self._observe_context_gap(context)
            return context

        execution = self.services.evaluation_execution_policy.decide(
            session_id=context.session_id,
            strategy_guidance=candidate.strategy_guidance,
            decision_result=candidate.decision_result,
            adjustment_manager=self.services.adjustment_manager,
            user_message=context.request.user_message,
        )
        meta.execution_mode = "synchronous" if execution.synchronous else "background"
        meta.critical_reasons = list(execution.reasons)
        evaluation_request = self._build_evaluation_request(context)

        if execution.synchronous:
            context.flags.evaluation_call_count = 1
            outcome = await run_agent_call(
                agent="EvaluationAgent",
                policy=EVALUATION_AUDIT_BEST_EFFORT,
                call=lambda: self._evaluate(context, evaluation_request, "synchronous"),
                trace_id=context.trace_id,
                on_failure=context.record_failure,
            )
            if outcome.skipped:
                meta.evaluator_failed = True
                self._observe_context_gap(context)
                return context
            evaluation = outcome.require_value()
            self._set_audit_meta(meta, evaluation)
            observation = self.services.adjustment_manager.observe(
                session_id=context.session_id,
                turn_number=context.adjustment_context.turn_number,
                evaluation_id=evaluation.evaluation_id,
                signals=evaluation.session_learning_signals,
                confidence=evaluation.confidence,
                failure_attribution=evaluation.failure_attribution,
            )
            context.adjustment_observation = observation
            if observation.profile is not None:
                context.resulting_adjustments = observation.profile
            if observation.activated_this_turn and observation.profile is not None:
                context.adjustment_remaining_turns = observation.profile.expires_after_turns
            return context

        meta.background_scheduled = True
        background_request = evaluation_request.model_copy(deep=True)
        args = (
            background_request,
            context.session_id,
            context.adjustment_context.turn_number,
        )
        if context.defer_background is not None:
            context.defer_background(self._run_background_evaluation, *args)
        else:
            task = asyncio.create_task(self._run_background_evaluation(*args))
            self.services.background_tasks.add(task)
            task.add_done_callback(self.services.background_tasks.discard)
        return context

    async def _evaluate(
        self,
        context: SimulationPipelineContext,
        request: SimulationEvaluationRequest,
        run_mode: str,
    ) -> SimulationEvaluationResponse:
        return await measured_call(
            self.services.runtime_metrics,
            trace_id=request.trace_id,
            session_id=request.session_id,
            turn_id=request.turn_id,
            agent="EvaluationAgent",
            version=request.evaluation_prompt_version,
            run_mode=run_mode,
            call=lambda: self.services.evaluation_agent.run(request),
        )

    async def _run_background_evaluation(
        self,
        request: SimulationEvaluationRequest,
        session_id: str,
        turn_number: int,
    ) -> None:
        outcome = await run_agent_call(
            agent="EvaluationAgent",
            policy=EVALUATION_AUDIT_BEST_EFFORT,
            call=lambda: measured_call(
                self.services.runtime_metrics,
                trace_id=request.trace_id,
                session_id=request.session_id,
                turn_id=request.turn_id,
                agent="EvaluationAgent",
                version=request.evaluation_prompt_version,
                run_mode="background",
                call=lambda: self.services.evaluation_agent.run(request),
            ),
            trace_id=request.trace_id,
        )
        if outcome.skipped:
            self.services.adjustment_manager.observe(
                session_id=session_id,
                turn_number=turn_number,
                evaluation_id="",
                signals=[],
                confidence=0.0,
                failure_attribution=FailureAttribution.CONTEXT_GAP,
            )
            return
        evaluation = outcome.require_value()

        observation = self.services.adjustment_manager.observe(
            session_id=session_id,
            turn_number=turn_number,
            evaluation_id=evaluation.evaluation_id,
            signals=evaluation.session_learning_signals,
            confidence=evaluation.confidence,
            failure_attribution=evaluation.failure_attribution,
        )
        logger.info(
            "background_evaluation_finished",
            extra={
                "trace_id": request.trace_id,
                "session_id": session_id,
                "turn_id": request.turn_id,
                "evaluation_id": evaluation.evaluation_id,
                "score": evaluation.simulation_success_score,
                "verdict": evaluation.verdict.value,
                "adjustment_activated": observation.activated_this_turn,
            },
        )

    def _build_evaluation_request(
        self,
        context: SimulationPipelineContext,
    ) -> SimulationEvaluationRequest:
        candidate = context.candidate
        assert candidate is not None
        decision = candidate.decision_result.decision
        guidance = candidate.strategy_guidance
        retrieved_ids = [item.evidence_id for item in context.retrieval.items]
        used_refs = unique_strings(
            [*guidance.persona_evidence_refs, *guidance.memory_evidence_refs, *retrieved_ids],
            limit=12,
        )
        return SimulationEvaluationRequest(
            trace_id=context.trace_id,
            session_id=context.session_id,
            turn_id=context.turn_id,
            persona_snapshot=context.persona_v2,
            relationship_state_before=context.require_current_state().relationship_state,
            session_memory=context.request.memory or empty_session_memory(),
            recent_messages=[
                StrategyMessage(role=item.role, content=item.content)
                for item in context.request.messages[-6:]
            ],
            user_message=context.request.user_message,
            response_guidance=guidance,
            simulation_result=SimulationEvaluationResult(
                reply=candidate.generated.response_text,
                attitude=attitude_label(candidate.generated.response_action),
                emotion=dominant_emotion(candidate.decision_result.updated_state.emotional_state),
                perceived_user_tone=perceived_tone(decision.turn_analysis.behavior_signals),
                state_delta=decision.state_delta.model_dump(),
                risk_flags=decision.turn_analysis.detected_events[:5],
                policy_id=guidance.guidance_id,
                guidance_id=guidance.guidance_id,
                used_evidence_refs=used_refs,
            ),
            strategy_prompt_version=prompt_version(
                self.services.strategy_agent,
                "prompt_version",
                "strategy-v2.5-v21-guidance",
            ),
            simulation_prompt_version=prompt_version(
                self.services.response_generator,
                "prompt_version",
                "simulation-v2.5-v21-persona-decision",
            ),
            evaluation_prompt_version=prompt_version(
                self.services.evaluation_agent,
                "prompt_version",
                "evaluation-v2.5-v21-hard-errors-only",
            ),
        )

    @staticmethod
    def _set_audit_meta(meta: SessionEvaluationMeta, evaluation: SimulationEvaluationResponse) -> None:
        meta.evaluated = True
        meta.initial_evaluation_id = evaluation.evaluation_id
        meta.final_evaluation_id = evaluation.evaluation_id
        meta.initial_score = evaluation.simulation_success_score
        meta.final_score = evaluation.simulation_success_score
        meta.score_delta = 0
        meta.initial_verdict = evaluation.verdict
        meta.final_verdict = evaluation.verdict
        meta.initial_failure_attribution = evaluation.failure_attribution
        meta.final_failure_attribution = evaluation.failure_attribution
        meta.hard_error_count = len(evaluation.hard_errors)

    def _observe_context_gap(self, context: SimulationPipelineContext) -> None:
        observation = self.services.adjustment_manager.observe(
            session_id=context.session_id,
            turn_number=context.adjustment_context.turn_number,
            evaluation_id="",
            signals=[],
            confidence=0.0,
            failure_attribution=FailureAttribution.CONTEXT_GAP,
        )
        context.adjustment_observation = observation


class AssemblyStage(BaseStage):
    name = "assemble_response"

    async def execute(self, context: SimulationPipelineContext) -> SimulationPipelineContext:
        request = context.request
        decision_result = context.require_decision()
        generated = context.require_generated()
        guidance = context.require_strategy_guidance()
        simulation_decision = context.simulation_decision
        assert simulation_decision is not None
        response_policy = decision_result.decision.response_policy
        analysis = decision_result.decision.turn_analysis
        legacy_updated_state = to_legacy_relationship_state(
            request.persona.state,
            decision_result.updated_state,
        )
        state_delta = legacy_delta(request.persona.state, legacy_updated_state)
        status = status_text(generated.response_action)
        is_silent = generated.response_action in SILENT_ACTIONS
        visible_text = status if is_silent else generated.response_text
        retrieval = context.retrieval
        observation = context.adjustment_observation
        resulting_adjustments = context.resulting_adjustments

        context.response = SessionMessageResponse(
            target_message=ChatMessage(
                role="system" if is_silent else "target",
                content=visible_text,
            ),
            simulation=SimulationReply(
                reply=visible_text,
                attitude=attitude_label(generated.response_action),
                emotion=dominant_emotion(decision_result.updated_state.emotional_state),
                perceived_user_tone=perceived_tone(analysis.behavior_signals),
                state_delta=state_delta,
                risk_flags=analysis.detected_events[:5],
            ),
            updated_state=legacy_updated_state,
            response=SessionActionResponse(
                action=generated.response_action,
                text=generated.response_text,
                status_text=status,
                conversation_ended=generated.response_action == "END_CONVERSATION",
            ),
            strategy_meta=SessionStrategyMeta(
                policy_id=guidance.guidance_id,
                strategy_action=guidance.recommended_mode.value,
                simulation_action=response_policy.action,
                confidence=guidance.confidence,
                persona_evidence_refs=guidance.persona_evidence_refs,
                memory_evidence_refs=guidance.memory_evidence_refs,
                prompt_version=prompt_version(
                    self.services.strategy_agent,
                    "prompt_version",
                    "strategy-v2.5-v21-guidance",
                ),
                fallback_used=context.flags.strategy_fallback_used,
                guidance_id=guidance.guidance_id,
                recommended_mode=guidance.recommended_mode.value,
                final_action=response_policy.action,
                decision_confidence=simulation_decision.confidence,
                guidance_followed=simulation_decision.guidance_followed,
                guidance_deviation_reason=simulation_decision.guidance_deviation_reason,
            ),
            simulation_state=decision_result.updated_state,
            evidence_meta=SessionEvidenceMeta(
                retrieval_mode=retrieval.retrieval_mode,
                evidence_ids=[item.evidence_id for item in retrieval.items],
                episode_ids=[item.episode_id for item in retrieval.items],
                relevance_scores=[item.relevance_score for item in retrieval.items],
            ),
            evaluation_meta=context.evaluation_meta,
            adjustment_meta=SessionAdjustmentMeta(
                applied=context.active_adjustments is not None,
                activated_this_turn=bool(observation and observation.activated_this_turn),
                style_adjustment_count=(
                    style_adjustment_count(resulting_adjustments)
                    if resulting_adjustments is not None
                    else 0
                ),
                strategy_adjustment_count=(
                    int(resulting_adjustments.style.prevent_unplanned_commitment)
                    if resulting_adjustments is not None
                    else 0
                ),
                remaining_turns=context.adjustment_remaining_turns,
            ),
            runtime_meta=SessionRuntimeMeta(
                turn_state_fallback_used=context.flags.turn_state_fallback_used,
                decision_fallback_used=context.flags.decision_fallback_used,
                strategy_fallback_used=context.flags.strategy_fallback_used,
                generator_retry_count=context.flags.generator_retry_count,
                generator_fallback_used=context.flags.generator_fallback_used,
                evaluation_call_count=context.flags.evaluation_call_count,
                feedback_retry_count=0,
                strategy_replan_count=0,
                simulation_revision_count=0,
                rejected_candidate_discarded=False,
            ),
        )
        return context


class PersistenceStage(BaseStage):
    name = "persist_and_measure"

    async def execute(self, context: SimulationPipelineContext) -> SimulationPipelineContext:
        response = context.require_response()
        decision_result = context.require_decision()
        self._record_turn(context, response)
        record_runtime_metric(
            self.services.runtime_metrics,
            trace_id=context.trace_id,
            session_id=context.session_id,
            turn_id=context.turn_id,
            agent="SimulationAgentV2Pipeline",
            version="v2.6-pipeline-audit",
            run_mode="pipeline",
            started_at=context.pipeline_started_at,
            success=True,
            correction_applied=False,
            score_delta=context.evaluation_meta.score_delta,
        )
        return context

    def _record_turn(
        self,
        context: SimulationPipelineContext,
        response: SessionMessageResponse,
    ) -> None:
        decision_result = context.require_decision()
        evaluation = response.evaluation_meta
        try:
            record = SimulationTurnRecord(
                turn_id=f"turn_{uuid4().hex}",
                persona_id=context.persona_id,
                session_id=context.session_id,
                user_message_digest=digest_text(context.request.user_message),
                user_message_length=len(context.request.user_message),
                state_before=context.require_current_state(),
                turn_analysis=SafeTurnAnalysis(
                    intent_digest=digest_text(decision_result.decision.turn_analysis.intent),
                    behavior_signals=decision_result.decision.turn_analysis.behavior_signals,
                    detected_event_digests=[
                        digest_text(item)
                        for item in decision_result.decision.turn_analysis.detected_events
                    ],
                ),
                state_delta=decision_result.decision.state_delta,
                state_after=decision_result.updated_state,
                response_action=(response.response.action if response.response else "REPLY_NORMAL"),
                response_text_digest=digest_text(
                    response.response.text if response.response else response.target_message.content
                ),
                response_text_length=len(
                    response.response.text if response.response else response.target_message.content
                ),
                decision_confidence=decision_result.decision.confidence,
                retrieved_evidence_ids=(
                    response.evidence_meta.evidence_ids if response.evidence_meta else []
                ),
                evaluator_triggered=bool(evaluation and evaluation.evaluated),
                evaluation_execution_mode=(
                    evaluation.execution_mode if evaluation else "not_run"
                ),
                background_evaluation_scheduled=bool(
                    evaluation and evaluation.background_scheduled
                ),
                evaluation_critical_reasons=(
                    evaluation.critical_reasons if evaluation else []
                ),
                evaluator_passed=(
                    evaluation.final_verdict
                    in {EvaluationVerdict.ACCEPT, EvaluationVerdict.ACCEPT_WITH_FEEDBACK}
                    if evaluation and evaluation.final_verdict is not None
                    else None
                ),
                initial_evaluation_score=(evaluation.initial_score if evaluation else None),
                final_evaluation_score=(evaluation.final_score if evaluation else None),
                evaluation_verdict=(
                    evaluation.final_verdict.value
                    if evaluation and evaluation.final_verdict
                    else None
                ),
                failure_attribution=(
                    evaluation.final_failure_attribution.value
                    if evaluation and evaluation.final_failure_attribution
                    else None
                ),
                feedback_action=(evaluation.feedback_action.value if evaluation else "none"),
                feedback_retry_count=0,
                rejected_candidate_discarded=False,
                adjustment_applied=bool(
                    response.adjustment_meta and response.adjustment_meta.applied
                ),
                adjustment_activated=bool(
                    response.adjustment_meta and response.adjustment_meta.activated_this_turn
                ),
                adjustment_style_count=(
                    response.adjustment_meta.style_adjustment_count
                    if response.adjustment_meta
                    else 0
                ),
                adjustment_strategy_count=(
                    response.adjustment_meta.strategy_adjustment_count
                    if response.adjustment_meta
                    else 0
                ),
                adjustment_remaining_turns=(
                    response.adjustment_meta.remaining_turns
                    if response.adjustment_meta
                    else 0
                ),
                decision_fallback_used=context.flags.decision_fallback_used,
                strategy_fallback_used=context.flags.strategy_fallback_used,
                generator_retry_count=context.flags.generator_retry_count,
                generator_fallback_used=context.flags.generator_fallback_used,
            )
            self.services.turn_store.append(record)
        except Exception:
            logger.exception(
                "simulation_turn_store_failed_without_blocking_response",
                extra={"persona_id": context.persona_id, "session_id": context.session_id},
            )
