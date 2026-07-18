from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from uuid import uuid4

from app.agents.evaluation_agent import EvaluationAgent
from app.agents.strategy_agent import StrategyAgent
from app.agents.simulation.response_generator import (
    ResponseGenerator,
    build_fallback_response,
)
from app.agents.simulation.context_builder import SimulationContextBuilder
from app.agents.simulation.strategy_policy_adapter import (
    build_decision_result_from_strategy,
)
from app.schemas.common import RelationshipState
from app.schemas.session import (
    ChatMessage,
    SessionActionResponse,
    SessionStrategyMeta,
    SessionMessageRequest,
    SessionMessageResponse,
    SimulationReply,
    StateDelta,
)
from app.schemas.evidence_retrieval import SessionEvidenceMeta
from app.schemas.evaluation import (
    EvaluationVerdict,
    FailureAttribution,
    FeedbackAction,
    SessionEvaluationMeta,
    SimulationEvaluationRequest,
    SimulationEvaluationResponse,
    SimulationEvaluationResult,
)
from app.schemas.feedback import InternalCorrection
from app.schemas.simulation_adjustment import (
    SessionAdjustmentMeta,
    SimulationAdjustmentProfile,
)
from app.schemas.memory import SessionMemory
from app.schemas.simulation_decision import (
    BehaviorSignals,
    DecisionAction,
    DecisionMessage,
    TurnDecisionResult,
    SimulationStateDelta,
)
from app.schemas.simulation_generation import GeneratedResponse, ResponseGenerationInput
from app.schemas.simulation_state import EmotionalState, SimulationState
from app.schemas.strategy import (
    ResponseAction as StrategyResponseAction,
    TargetInterpretation,
    TargetResponsePolicy,
    TargetResponseStrategyRequest,
    ToneProfile,
    StrategyMessage,
)
from app.schemas.simulation_turn import (
    SafeTurnAnalysis,
    SessionRuntimeMeta,
    SimulationTurnRecord,
)
from app.schemas.runtime_metrics import AgentRuntimeMetric
from app.services.persona_v2_adapter import compile_legacy_persona
from app.services.simulation_state_service import create_initial_simulation_state
from app.services.evidence_retriever import EvidenceRetriever
from app.services.simulation_feedback_loop import SimulationFeedbackLoop
from app.services.simulation_turn_store import SimulationTurnStore, simulation_turn_store
from app.services.simulation_adjustment_manager import (
    SimulationAdjustmentManager,
    simulation_adjustment_manager,
)
from app.services.agent_runtime_metrics import (
    AgentRuntimeMetricsStore,
    agent_runtime_metrics_store,
)
from app.services.evaluation_execution_policy import EvaluationExecutionPolicy


SILENT_ACTIONS = {"DEFER_REPLY", "READ_NO_REPLY"}
logger = logging.getLogger(__name__)


@dataclass
class _SimulationCandidate:
    trace_id: str
    turn_id: str
    strategy_policy: TargetResponsePolicy
    decision_result: TurnDecisionResult
    generation_input: ResponseGenerationInput | None
    generated: GeneratedResponse
    generator_retry_count: int = 0
    generator_fallback_used: bool = False


class SimulationAgentV2:
    """V2 pipeline with one Strategy-owned policy and one bounded feedback loop."""

    version = "v2.3-phase6-hybrid-evaluation"

    def __init__(
        self,
        strategy_agent: StrategyAgent | None = None,
        response_generator: ResponseGenerator | None = None,
        evidence_retriever: EvidenceRetriever | None = None,
        context_builder: SimulationContextBuilder | None = None,
        evaluation_agent: EvaluationAgent | None = None,
        feedback_loop: SimulationFeedbackLoop | None = None,
        turn_store: SimulationTurnStore | None = None,
        adjustment_manager: SimulationAdjustmentManager | None = None,
        evaluation_execution_mode: str | None = None,
        runtime_metrics: AgentRuntimeMetricsStore | None = None,
    ) -> None:
        self.strategy_agent = strategy_agent or StrategyAgent(mode="active")
        self.response_generator = response_generator or ResponseGenerator()
        self.context_builder = context_builder or SimulationContextBuilder(
            evidence_retriever or EvidenceRetriever()
        )
        self.evaluation_agent = evaluation_agent or EvaluationAgent()
        self.feedback_loop = feedback_loop or SimulationFeedbackLoop()
        self.turn_store = turn_store or simulation_turn_store
        self.adjustment_manager = adjustment_manager or simulation_adjustment_manager
        self.evaluation_execution_policy = EvaluationExecutionPolicy(
            evaluation_execution_mode
        )
        self.runtime_metrics = runtime_metrics or agent_runtime_metrics_store
        self._background_tasks: set[asyncio.Task[None]] = set()

    async def run(
        self,
        request: SessionMessageRequest,
        *,
        defer_background: Callable[..., None] | None = None,
    ) -> SessionMessageResponse:
        pipeline_started_at = time.perf_counter()
        persona_id = (
            request.persona_id
            or (request.simulation_state.persona_id if request.simulation_state else None)
            or (request.persona_v2.persona_id if request.persona_v2 else None)
            or _stable_persona_id(request)
        )
        session_id = (
            request.session_id
            or (request.simulation_state.session_id if request.simulation_state else None)
            or _stable_session_id(request, persona_id)
        )
        adjustment_context = self.adjustment_manager.begin_turn(session_id)
        active_adjustments = adjustment_context.profile
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
        evidence_context = self.context_builder.build_evidence_context(
            persona_id=persona_id,
            user_message=request.user_message,
            state=current_state,
            top_k=4,
        )
        retrieval = evidence_context.retrieval

        strategy_request = TargetResponseStrategyRequest(
            trace_id=f"trace_{uuid4().hex}",
            session_id=session_id,
            turn_id=f"turn_{current_state.conversation_state.turn_count + 1}",
            scenario=request.scenario,
            user_goal=request.goal,
            persona_snapshot=persona_v2,
            relationship_state=current_state.relationship_state,
            session_memory=request.memory,
            recent_messages=[
                StrategyMessage(role=item.role, content=item.content)
                for item in request.messages[-6:]
            ],
            user_message=request.user_message,
            simulation_adjustments=active_adjustments,
        )
        strategy_fallback_used = False
        if request.response_policy is not None:
            strategy_policy = request.response_policy.model_copy(deep=True)
        else:
            try:
                strategy_policy = await self._call_strategy_agent(strategy_request)
            except Exception:
                strategy_fallback_used = True
                strategy_policy = _fallback_strategy_policy(
                    request=strategy_request,
                )
                logger.exception(
                    "strategy_agent_failed_using_safe_policy_fallback",
                    extra={"persona_id": persona_id, "session_id": session_id},
                )
        candidate = await self._build_candidate(
            trace_id=strategy_request.trace_id,
            turn_id=strategy_request.turn_id,
            strategy_policy=strategy_policy,
            current_state=current_state,
            persona_v2=persona_v2,
            recent_turns=recent_turns,
            user_message=request.user_message,
            linguistic_evidence=list(evidence_context.linguistic_evidence),
            persona_id=persona_id,
            session_id=session_id,
            freeze_state=strategy_fallback_used,
            allow_generation_recovery=True,
            simulation_adjustments=active_adjustments,
        )
        initial_generator_retry_count = candidate.generator_retry_count
        initial_generator_fallback_used = candidate.generator_fallback_used

        evaluation_meta = SessionEvaluationMeta()
        evaluation_call_count = 0
        feedback_retry_count = 0
        strategy_replan_count = 0
        simulation_revision_count = 0
        rejected_candidate_discarded = False
        learning_evaluation: SimulationEvaluationResponse | None = None
        execution_decision = self.evaluation_execution_policy.decide(
            session_id=session_id,
            strategy_policy=candidate.strategy_policy,
            decision_result=candidate.decision_result,
            adjustment_manager=self.adjustment_manager,
            user_message=request.user_message,
        )
        evaluation_meta.execution_mode = (
            "synchronous" if execution_decision.synchronous else "background"
        )
        evaluation_meta.critical_reasons = list(execution_decision.reasons)
        if strategy_fallback_used:
            evaluation_meta.execution_mode = "not_run"

        if not strategy_fallback_used and execution_decision.synchronous:
            try:
                evaluation_call_count = 1
                initial_evaluation = await self._call_evaluation_agent(
                    self._build_evaluation_request(
                        strategy_request=strategy_request,
                        request=request,
                        persona_v2=persona_v2,
                        current_state=current_state,
                        candidate=candidate,
                        retrieved_evidence_ids=[
                            item.evidence_id for item in retrieval.items
                        ],
                    ),
                    run_mode="synchronous",
                )
                self._set_initial_evaluation_meta(
                    evaluation_meta,
                    initial_evaluation,
                )

                plan = self.feedback_loop.plan(
                    initial_evaluation,
                    corrections_used=feedback_retry_count,
                )
                if plan.action != FeedbackAction.NONE:
                    feedback_retry_count = 1
                    evaluation_meta.retry_count = 1
                    evaluation_meta.feedback_action = plan.action

                    if plan.action == FeedbackAction.REVISE_SIMULATION:
                        simulation_revision_count = 1
                        candidate, correction_applied, candidate_replaced = (
                            await self._revise_simulation_candidate(
                                candidate=candidate,
                                correction=plan.simulation_correction,
                                persona_id=persona_id,
                                session_id=session_id,
                            )
                        )
                    else:
                        strategy_replan_count = 1
                        (
                            candidate,
                            correction_applied,
                            replan_fallback_used,
                        ) = await self._replan_and_regenerate_candidate(
                            strategy_request=strategy_request,
                            strategy_correction=plan.strategy_correction,
                            simulation_correction=plan.simulation_correction,
                            current_state=current_state,
                            persona_v2=persona_v2,
                            recent_turns=recent_turns,
                            user_message=request.user_message,
                            linguistic_evidence=list(
                                evidence_context.linguistic_evidence
                            ),
                            persona_id=persona_id,
                            session_id=session_id,
                        )
                        strategy_fallback_used = (
                            strategy_fallback_used or replan_fallback_used
                        )
                        candidate_replaced = True

                    evaluation_meta.correction_applied = correction_applied
                    rejected_candidate_discarded = candidate_replaced
                    evaluation_call_count = 2
                    try:
                        final_evaluation = await self._call_evaluation_agent(
                            self._build_evaluation_request(
                                strategy_request=strategy_request,
                                request=request,
                                persona_v2=persona_v2,
                                current_state=current_state,
                                candidate=candidate,
                                retrieved_evidence_ids=[
                                    item.evidence_id for item in retrieval.items
                                ],
                            ),
                            run_mode="synchronous",
                        )
                        self._set_final_evaluation_meta(
                            evaluation_meta,
                            final_evaluation,
                        )
                        learning_evaluation = final_evaluation
                    except Exception:
                        evaluation_meta.final_evaluator_failed = True
                        logger.exception(
                            "final_evaluation_failed_without_additional_retry",
                            extra={
                                "persona_id": persona_id,
                                "session_id": session_id,
                            },
                        )
                else:
                    self._set_final_evaluation_meta(
                        evaluation_meta,
                        initial_evaluation,
                    )
                    learning_evaluation = initial_evaluation
            except Exception:
                evaluation_meta.evaluator_failed = True
                logger.exception(
                    "evaluation_agent_failed_using_initial_candidate",
                    extra={"persona_id": persona_id, "session_id": session_id},
                )

        elif not strategy_fallback_used:
            background_request = self._build_evaluation_request(
                strategy_request=strategy_request,
                request=request,
                persona_v2=persona_v2,
                current_state=current_state,
                candidate=candidate,
                retrieved_evidence_ids=[
                    item.evidence_id for item in retrieval.items
                ],
            ).model_copy(deep=True)
            evaluation_meta.background_scheduled = True
            background_args = (
                background_request,
                session_id,
                adjustment_context.turn_number,
            )
            if defer_background is not None:
                defer_background(
                    self._run_background_evaluation,
                    *background_args,
                )
            else:
                task = asyncio.create_task(
                    self._run_background_evaluation(*background_args)
                )
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

        adjustment_observation = None
        if learning_evaluation is not None:
            adjustment_observation = self.adjustment_manager.observe(
                session_id=session_id,
                turn_number=adjustment_context.turn_number,
                evaluation_id=learning_evaluation.evaluation_id,
                signals=learning_evaluation.session_learning_signals,
                confidence=learning_evaluation.confidence,
                failure_attribution=learning_evaluation.failure_attribution,
            )
        elif execution_decision.synchronous or strategy_fallback_used:
            adjustment_observation = self.adjustment_manager.observe(
                session_id=session_id,
                turn_number=adjustment_context.turn_number,
                evaluation_id="",
                signals=[],
                confidence=0.0,
                failure_attribution=FailureAttribution.CONTEXT_GAP,
            )

        resulting_adjustments = (
            adjustment_observation.profile
            if adjustment_observation is not None
            and adjustment_observation.profile is not None
            else active_adjustments
        )
        adjustment_remaining_turns = (
            resulting_adjustments.expires_after_turns
            if adjustment_observation is not None
            and adjustment_observation.activated_this_turn
            and resulting_adjustments is not None
            else adjustment_context.remaining_turns
        )

        strategy_policy = candidate.strategy_policy
        decision_result = candidate.decision_result
        response_policy = decision_result.decision.response_policy
        generated = candidate.generated
        generator_retry_count = max(
            initial_generator_retry_count,
            candidate.generator_retry_count,
        )
        generator_fallback_used = (
            initial_generator_fallback_used or candidate.generator_fallback_used
        )

        legacy_updated_state = _to_legacy_relationship_state(
            request.persona.state,
            decision_result.updated_state,
        )
        legacy_delta = _legacy_delta(request.persona.state, legacy_updated_state)
        analysis = decision_result.decision.turn_analysis
        status_text = _status_text(generated.response_action)
        is_silent = generated.response_action in SILENT_ACTIONS
        legacy_visible_text = status_text if is_silent else generated.response_text

        response = SessionMessageResponse(
            target_message=ChatMessage(
                role="system" if is_silent else "target",
                content=legacy_visible_text,
            ),
            simulation=SimulationReply(
                reply=legacy_visible_text,
                attitude=_attitude_label(generated.response_action),
                emotion=_dominant_emotion(decision_result.updated_state.emotional_state),
                perceived_user_tone=_perceived_tone(analysis.behavior_signals),
                state_delta=legacy_delta,
                risk_flags=analysis.detected_events[:5],
            ),
            updated_state=legacy_updated_state,
            response=SessionActionResponse(
                action=generated.response_action,
                text=generated.response_text,
                status_text=status_text,
                conversation_ended=generated.response_action == "END_CONVERSATION",
            ),
            strategy_meta=SessionStrategyMeta(
                policy_id=strategy_policy.policy_id,
                strategy_action=strategy_policy.action.value,
                simulation_action=response_policy.action,
                confidence=strategy_policy.confidence,
                persona_evidence_refs=strategy_policy.persona_evidence_refs,
                memory_evidence_refs=strategy_policy.memory_evidence_refs,
                prompt_version=getattr(
                    self.strategy_agent,
                    "prompt_version",
                    "strategy-v2.2-phase5-session-adaptation",
                ),
                fallback_used=strategy_fallback_used,
            ),
            simulation_state=decision_result.updated_state,
            evidence_meta=SessionEvidenceMeta(
                retrieval_mode=retrieval.retrieval_mode,
                evidence_ids=[item.evidence_id for item in retrieval.items],
                episode_ids=[item.episode_id for item in retrieval.items],
                relevance_scores=[item.relevance_score for item in retrieval.items],
            ),
            evaluation_meta=evaluation_meta,
            adjustment_meta=SessionAdjustmentMeta(
                applied=active_adjustments is not None,
                activated_this_turn=bool(
                    adjustment_observation
                    and adjustment_observation.activated_this_turn
                ),
                style_adjustment_count=(
                    len(resulting_adjustments.style_adjustments)
                    if resulting_adjustments is not None
                    else 0
                ),
                strategy_adjustment_count=(
                    len(resulting_adjustments.strategy_adjustments)
                    if resulting_adjustments is not None
                    else 0
                ),
                remaining_turns=adjustment_remaining_turns,
            ),
            runtime_meta=SessionRuntimeMeta(
                decision_fallback_used=False,
                strategy_fallback_used=strategy_fallback_used,
                generator_retry_count=generator_retry_count,
                generator_fallback_used=generator_fallback_used,
                evaluation_call_count=evaluation_call_count,
                feedback_retry_count=feedback_retry_count,
                strategy_replan_count=strategy_replan_count,
                simulation_revision_count=simulation_revision_count,
                rejected_candidate_discarded=rejected_candidate_discarded,
            ),
        )
        self._record_turn(
            request=request,
            response=response,
            state_before=current_state,
            decision_result=decision_result,
            persona_id=persona_id,
            session_id=session_id,
        )
        self._record_runtime_metric(
            trace_id=strategy_request.trace_id,
            session_id=session_id,
            turn_id=strategy_request.turn_id,
            agent="SimulationAgentV2",
            version=self.version,
            run_mode="pipeline",
            started_at=pipeline_started_at,
            success=True,
            correction_applied=evaluation_meta.correction_applied,
            score_delta=evaluation_meta.score_delta,
        )
        return response

    async def _run_background_evaluation(
        self,
        evaluation_request: SimulationEvaluationRequest,
        session_id: str,
        turn_number: int,
    ) -> None:
        try:
            evaluation = await self._call_evaluation_agent(
                evaluation_request,
                run_mode="background",
            )
        except Exception:
            self.adjustment_manager.observe(
                session_id=session_id,
                turn_number=turn_number,
                evaluation_id="",
                signals=[],
                confidence=0.0,
                failure_attribution=FailureAttribution.CONTEXT_GAP,
            )
            logger.exception(
                "background_evaluation_failed_without_blocking_response",
                extra={
                    "trace_id": evaluation_request.trace_id,
                    "session_id": session_id,
                    "turn_id": evaluation_request.turn_id,
                },
            )
            return

        observation = self.adjustment_manager.observe(
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
                "trace_id": evaluation_request.trace_id,
                "session_id": session_id,
                "turn_id": evaluation_request.turn_id,
                "evaluation_id": evaluation.evaluation_id,
                "score": evaluation.simulation_success_score,
                "verdict": evaluation.verdict.value,
                "failure_attribution": evaluation.failure_attribution.value,
                "adjustment_activated": observation.activated_this_turn,
            },
        )

    async def _call_strategy_agent(
        self,
        request: TargetResponseStrategyRequest,
    ) -> TargetResponsePolicy:
        started_at = time.perf_counter()
        try:
            result = await self.strategy_agent.run(request)
        except Exception:
            self._record_runtime_metric(
                trace_id=request.trace_id,
                session_id=request.session_id,
                turn_id=request.turn_id,
                agent="StrategyAgent",
                version=_prompt_version(
                    self.strategy_agent,
                    "prompt_version",
                    "strategy-v2.2-phase5-session-adaptation",
                ),
                run_mode="synchronous",
                started_at=started_at,
                success=False,
            )
            raise
        self._record_runtime_metric(
            trace_id=request.trace_id,
            session_id=request.session_id,
            turn_id=request.turn_id,
            agent="StrategyAgent",
            version=_prompt_version(
                self.strategy_agent,
                "prompt_version",
                "strategy-v2.2-phase5-session-adaptation",
            ),
            run_mode="synchronous",
            started_at=started_at,
            success=True,
        )
        return result

    async def _call_evaluation_agent(
        self,
        request: SimulationEvaluationRequest,
        *,
        run_mode: str,
    ) -> SimulationEvaluationResponse:
        started_at = time.perf_counter()
        try:
            result = await self.evaluation_agent.run(request)
        except Exception:
            self._record_runtime_metric(
                trace_id=request.trace_id,
                session_id=request.session_id,
                turn_id=request.turn_id,
                agent="EvaluationAgent",
                version=request.evaluation_prompt_version,
                run_mode=run_mode,
                started_at=started_at,
                success=False,
            )
            raise
        self._record_runtime_metric(
            trace_id=request.trace_id,
            session_id=request.session_id,
            turn_id=request.turn_id,
            agent="EvaluationAgent",
            version=request.evaluation_prompt_version,
            run_mode=run_mode,
            started_at=started_at,
            success=True,
        )
        return result

    async def _call_response_generator(
        self,
        request: ResponseGenerationInput,
        *,
        trace_id: str,
        session_id: str,
        turn_id: str,
    ) -> GeneratedResponse:
        started_at = time.perf_counter()
        try:
            result = await self.response_generator.run(request)
        except Exception:
            self._record_runtime_metric(
                trace_id=trace_id,
                session_id=session_id,
                turn_id=turn_id,
                agent="SimulationResponseGenerator",
                version=_prompt_version(
                    self.response_generator,
                    "prompt_version",
                    "simulation-v2.2-phase5-session-adaptation",
                ),
                run_mode="synchronous",
                started_at=started_at,
                success=False,
            )
            raise
        self._record_runtime_metric(
            trace_id=trace_id,
            session_id=session_id,
            turn_id=turn_id,
            agent="SimulationResponseGenerator",
            version=_prompt_version(
                self.response_generator,
                "prompt_version",
                "simulation-v2.2-phase5-session-adaptation",
            ),
            run_mode="synchronous",
            started_at=started_at,
            success=True,
        )
        return result

    def _record_runtime_metric(
        self,
        *,
        trace_id: str,
        session_id: str,
        turn_id: str,
        agent: str,
        version: str,
        run_mode: str,
        started_at: float,
        success: bool,
        correction_applied: bool = False,
        score_delta: int | None = None,
    ) -> None:
        try:
            self.runtime_metrics.record(
                AgentRuntimeMetric(
                    trace_id=trace_id,
                    session_id=session_id,
                    turn_id=turn_id,
                    agent=agent,
                    version=version,
                    run_mode=run_mode,
                    latency_ms=max(
                        0,
                        int((time.perf_counter() - started_at) * 1000),
                    ),
                    success=success,
                    correction_applied=correction_applied,
                    score_delta=score_delta,
                )
            )
        except Exception:
            logger.exception(
                "agent_runtime_metric_record_failed_without_blocking_response",
                extra={
                    "trace_id": trace_id,
                    "session_id": session_id,
                    "turn_id": turn_id,
                    "agent": agent,
                },
            )

    async def _build_candidate(
        self,
        *,
        trace_id: str,
        turn_id: str,
        strategy_policy: TargetResponsePolicy,
        current_state: SimulationState,
        persona_v2,
        recent_turns: list[DecisionMessage],
        user_message: str,
        linguistic_evidence: list[str],
        persona_id: str,
        session_id: str,
        freeze_state: bool,
        allow_generation_recovery: bool,
        simulation_adjustments: SimulationAdjustmentProfile | None = None,
        evaluation_correction: InternalCorrection | None = None,
    ) -> _SimulationCandidate:
        decision_result = build_decision_result_from_strategy(
            policy=strategy_policy,
            current_state=current_state,
        )
        if freeze_state:
            decision_result.decision.state_delta = _zero_state_delta()
            decision_result.updated_state = current_state.model_copy(deep=True)

        response_policy = decision_result.decision.response_policy
        if response_policy.action in SILENT_ACTIONS:
            return _SimulationCandidate(
                trace_id=trace_id,
                turn_id=turn_id,
                strategy_policy=strategy_policy,
                decision_result=decision_result,
                generation_input=None,
                generated=GeneratedResponse(
                    response_text="",
                    response_action=response_policy.action,
                ),
            )

        generation_input = ResponseGenerationInput(
            persona=persona_v2,
            current_state=decision_result.updated_state,
            response_policy=response_policy,
            strategy_policy_id=strategy_policy.policy_id,
            strategy_action=strategy_policy.action.value,
            strategy_evidence_refs=[
                *strategy_policy.persona_evidence_refs,
                *strategy_policy.memory_evidence_refs,
            ],
            recent_turns=recent_turns,
            user_message=user_message,
            relevant_linguistic_evidence=linguistic_evidence,
            simulation_adjustments=simulation_adjustments,
            evaluation_correction=evaluation_correction,
            generation_attempt=2 if evaluation_correction else 1,
        )
        if allow_generation_recovery:
            generated, retry_count, fallback_used = await self._generate_with_recovery(
                generation_input,
                trace_id=trace_id,
                turn_id=turn_id,
                persona_id=persona_id,
                session_id=session_id,
            )
        else:
            retry_count = 0
            fallback_used = False
            try:
                generated = await self._call_response_generator(
                    generation_input,
                    trace_id=trace_id,
                    session_id=session_id,
                    turn_id=turn_id,
                )
            except Exception:
                fallback_used = True
                generated = build_fallback_response(
                    response_policy,
                    strategy_action=strategy_policy.action.value,
                )
                logger.exception(
                    "feedback_generation_failed_using_corrected_policy_fallback",
                    extra={"persona_id": persona_id, "session_id": session_id},
                )

        return _SimulationCandidate(
            trace_id=trace_id,
            turn_id=turn_id,
            strategy_policy=strategy_policy,
            decision_result=decision_result,
            generation_input=generation_input,
            generated=generated,
            generator_retry_count=retry_count,
            generator_fallback_used=fallback_used,
        )

    async def _revise_simulation_candidate(
        self,
        *,
        candidate: _SimulationCandidate,
        correction: InternalCorrection | None,
        persona_id: str,
        session_id: str,
    ) -> tuple[_SimulationCandidate, bool, bool]:
        if candidate.generation_input is None or correction is None:
            return candidate, False, False

        retry_input = candidate.generation_input.model_copy(
            deep=True,
            update={
                "evaluation_correction": correction,
                "generation_attempt": 2,
            },
        )
        correction_applied = True
        fallback_used = candidate.generator_fallback_used
        try:
            generated = await self._call_response_generator(
                retry_input,
                trace_id=candidate.trace_id,
                session_id=session_id,
                turn_id=candidate.turn_id,
            )
        except Exception:
            correction_applied = False
            fallback_used = True
            generated = build_fallback_response(
                retry_input.response_policy,
                strategy_action=retry_input.strategy_action,
            )
            logger.exception(
                "simulation_revision_failed_discarding_rejected_candidate",
                extra={"persona_id": persona_id, "session_id": session_id},
            )

        return (
            _SimulationCandidate(
                trace_id=candidate.trace_id,
                turn_id=candidate.turn_id,
                strategy_policy=candidate.strategy_policy,
                decision_result=candidate.decision_result,
                generation_input=retry_input,
                generated=generated,
                generator_retry_count=candidate.generator_retry_count,
                generator_fallback_used=fallback_used,
            ),
            correction_applied,
            True,
        )

    async def _replan_and_regenerate_candidate(
        self,
        *,
        strategy_request: TargetResponseStrategyRequest,
        strategy_correction: InternalCorrection | None,
        simulation_correction: InternalCorrection | None,
        current_state: SimulationState,
        persona_v2,
        recent_turns: list[DecisionMessage],
        user_message: str,
        linguistic_evidence: list[str],
        persona_id: str,
        session_id: str,
    ) -> tuple[_SimulationCandidate, bool, bool]:
        retry_request = strategy_request.model_copy(
            deep=True,
            update={"evaluation_correction": strategy_correction},
        )
        strategy_fallback_used = False
        try:
            revised_policy = await self._call_strategy_agent(retry_request)
        except Exception:
            strategy_fallback_used = True
            revised_policy = _fallback_strategy_policy(request=retry_request)
            logger.exception(
                "strategy_replan_failed_discarding_rejected_candidate",
                extra={"persona_id": persona_id, "session_id": session_id},
            )

        candidate = await self._build_candidate(
            trace_id=retry_request.trace_id,
            turn_id=retry_request.turn_id,
            strategy_policy=revised_policy,
            current_state=current_state,
            persona_v2=persona_v2,
            recent_turns=recent_turns,
            user_message=user_message,
            linguistic_evidence=linguistic_evidence,
            persona_id=persona_id,
            session_id=session_id,
            freeze_state=strategy_fallback_used,
            allow_generation_recovery=False,
            simulation_adjustments=strategy_request.simulation_adjustments,
            evaluation_correction=(
                simulation_correction if not strategy_fallback_used else None
            ),
        )
        return candidate, not strategy_fallback_used, strategy_fallback_used

    def _build_evaluation_request(
        self,
        *,
        strategy_request: TargetResponseStrategyRequest,
        request: SessionMessageRequest,
        persona_v2,
        current_state: SimulationState,
        candidate: _SimulationCandidate,
        retrieved_evidence_ids: list[str],
    ) -> SimulationEvaluationRequest:
        decision = candidate.decision_result.decision
        policy = candidate.strategy_policy
        used_evidence_refs = _unique_strings(
            [
                *policy.persona_evidence_refs,
                *policy.memory_evidence_refs,
                *retrieved_evidence_ids,
            ],
            limit=12,
        )
        return SimulationEvaluationRequest(
            trace_id=strategy_request.trace_id,
            session_id=strategy_request.session_id,
            turn_id=strategy_request.turn_id,
            persona_snapshot=persona_v2,
            relationship_state_before=current_state.relationship_state,
            session_memory=request.memory or _empty_session_memory(),
            recent_messages=[
                StrategyMessage(role=item.role, content=item.content)
                for item in request.messages[-6:]
            ],
            user_message=request.user_message,
            response_policy=policy,
            simulation_result=SimulationEvaluationResult(
                reply=candidate.generated.response_text,
                attitude=_attitude_label(candidate.generated.response_action),
                emotion=_dominant_emotion(
                    candidate.decision_result.updated_state.emotional_state
                ),
                perceived_user_tone=_perceived_tone(
                    decision.turn_analysis.behavior_signals
                ),
                state_delta=decision.state_delta.model_dump(),
                risk_flags=decision.turn_analysis.detected_events[:5],
                policy_id=policy.policy_id,
                used_evidence_refs=used_evidence_refs,
            ),
            strategy_prompt_version=_prompt_version(
                self.strategy_agent,
                "prompt_version",
                "strategy-v2.2-phase5-session-adaptation",
            ),
            simulation_prompt_version=_prompt_version(
                self.response_generator,
                "prompt_version",
                "simulation-v2.2-phase5-session-adaptation",
            ),
            evaluation_prompt_version=_prompt_version(
                self.evaluation_agent,
                "prompt_version",
                "evaluation-v2.1-phase5-session-signals",
            ),
        )

    @staticmethod
    def _set_initial_evaluation_meta(
        meta: SessionEvaluationMeta,
        evaluation: SimulationEvaluationResponse,
    ) -> None:
        meta.evaluated = True
        meta.initial_evaluation_id = evaluation.evaluation_id
        meta.initial_score = evaluation.simulation_success_score
        meta.initial_verdict = evaluation.verdict
        meta.initial_failure_attribution = evaluation.failure_attribution

    @staticmethod
    def _set_final_evaluation_meta(
        meta: SessionEvaluationMeta,
        evaluation: SimulationEvaluationResponse,
    ) -> None:
        meta.final_evaluation_id = evaluation.evaluation_id
        meta.final_score = evaluation.simulation_success_score
        meta.final_verdict = evaluation.verdict
        meta.final_failure_attribution = evaluation.failure_attribution
        if meta.initial_score is not None:
            meta.score_delta = meta.final_score - meta.initial_score

    async def _generate_with_recovery(
        self,
        generation_input: ResponseGenerationInput,
        *,
        trace_id: str,
        turn_id: str,
        persona_id: str,
        session_id: str,
    ) -> tuple[GeneratedResponse, int, bool]:
        try:
            return await self._call_response_generator(
                generation_input,
                trace_id=trace_id,
                session_id=session_id,
                turn_id=turn_id,
            ), 0, False
        except Exception:
            logger.exception(
                "response_generator_failed_retrying_once",
                extra={"persona_id": persona_id, "session_id": session_id},
            )

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
        try:
            return await self._call_response_generator(
                retry_input,
                trace_id=trace_id,
                session_id=session_id,
                turn_id=turn_id,
            ), 1, False
        except Exception:
            logger.exception(
                "response_generator_retry_failed_using_deterministic_fallback",
                extra={"persona_id": persona_id, "session_id": session_id},
            )
            return build_fallback_response(
                generation_input.response_policy,
                strategy_action=generation_input.strategy_action,
            ), 1, True

    def _record_turn(
        self,
        *,
        request: SessionMessageRequest,
        response: SessionMessageResponse,
        state_before: SimulationState,
        decision_result: TurnDecisionResult,
        persona_id: str,
        session_id: str,
    ) -> None:
        evaluation = response.evaluation_meta
        try:
            record = SimulationTurnRecord(
                turn_id=f"turn_{uuid4().hex}",
                persona_id=persona_id,
                session_id=session_id,
                user_message_digest=_digest_text(request.user_message),
                user_message_length=len(request.user_message),
                state_before=state_before,
                turn_analysis=SafeTurnAnalysis(
                    intent_digest=_digest_text(
                        decision_result.decision.turn_analysis.intent
                    ),
                    behavior_signals=(
                        decision_result.decision.turn_analysis.behavior_signals
                    ),
                    detected_event_digests=[
                        _digest_text(item)
                        for item in decision_result.decision.turn_analysis.detected_events
                    ],
                ),
                state_delta=decision_result.decision.state_delta,
                state_after=decision_result.updated_state,
                response_action=(
                    response.response.action if response.response else "REPLY_NORMAL"
                ),
                response_text_digest=_digest_text(
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
                    in {
                        EvaluationVerdict.ACCEPT,
                        EvaluationVerdict.ACCEPT_WITH_FEEDBACK,
                    }
                    if evaluation and evaluation.final_verdict is not None
                    else None
                ),
                initial_evaluation_score=(
                    evaluation.initial_score if evaluation else None
                ),
                final_evaluation_score=(
                    evaluation.final_score if evaluation else None
                ),
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
                feedback_action=(
                    evaluation.feedback_action.value if evaluation else "none"
                ),
                feedback_retry_count=(
                    response.runtime_meta.feedback_retry_count
                    if response.runtime_meta
                    else 0
                ),
                rejected_candidate_discarded=bool(
                    response.runtime_meta
                    and response.runtime_meta.rejected_candidate_discarded
                ),
                adjustment_applied=bool(
                    response.adjustment_meta
                    and response.adjustment_meta.applied
                ),
                adjustment_activated=bool(
                    response.adjustment_meta
                    and response.adjustment_meta.activated_this_turn
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
                decision_fallback_used=bool(
                    response.runtime_meta and response.runtime_meta.decision_fallback_used
                ),
                strategy_fallback_used=bool(
                    response.runtime_meta and response.runtime_meta.strategy_fallback_used
                ),
                generator_retry_count=(
                    response.runtime_meta.generator_retry_count
                    if response.runtime_meta
                    else 0
                ),
                generator_fallback_used=bool(
                    response.runtime_meta and response.runtime_meta.generator_fallback_used
                ),
            )
            self.turn_store.append(record)
            logger.info(
                "simulation_v2_turn_recorded",
                extra={
                    "turn_id": record.turn_id,
                    "persona_id": persona_id,
                    "session_id": session_id,
                    "user_message_length": record.user_message_length,
                    "response_action": record.response_action,
                    "response_text_length": record.response_text_length,
                    "decision_confidence": record.decision_confidence,
                    "retrieved_evidence_ids": record.retrieved_evidence_ids,
                    "evaluator_triggered": record.evaluator_triggered,
                },
            )
        except Exception:
            logger.exception(
                "simulation_turn_store_failed_without_blocking_response",
                extra={"persona_id": persona_id, "session_id": session_id},
            )


def _stable_persona_id(request: SessionMessageRequest) -> str:
    value = f"{request.persona.title}|{request.persona.style}|{request.role}"
    return f"persona_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def _fallback_strategy_policy(
    *,
    request: TargetResponseStrategyRequest,
) -> TargetResponsePolicy:
    return TargetResponsePolicy(
        policy_id=f"policy_fallback_{request.turn_id}",
        interpretation=TargetInterpretation(
            perceived_intent="当前无法可靠判断用户意图。",
            perceived_tone="中性或不确定。",
            salient_point="需要对用户当前表达作出保守回应。",
            perceived_concern="上下文或策略服务暂时不可用。",
        ),
        action=StrategyResponseAction.ACKNOWLEDGE,
        response_goal="从目标人物立场作出简短、中性且不升级冲突的回应。",
        stance="保持克制，不新增承诺。",
        required_content=["回应用户当前表达"],
        forbidden_content=["升级冲突", "虚构事实", "替用户制定下一句话"],
        tone_profile=ToneProfile(
            warmth=45,
            directness=55,
            formality=50,
            emotional_intensity=20,
            length="short",
        ),
        persona_evidence_refs=[
            f"persona_snapshot:{request.persona_snapshot.persona_id}"
        ],
        memory_evidence_refs=[],
        confidence=0.0,
        uncertainty_notes=["StrategyAgent 不可用，使用保守回退策略。"],
    )


def _zero_state_delta() -> SimulationStateDelta:
    return SimulationStateDelta(
        **{name: 0.0 for name in SimulationStateDelta.model_fields}
    )


def _empty_session_memory() -> SessionMemory:
    """Represent first-turn evidence absence without inventing memory facts."""

    return SessionMemory(
        conversation_summary="",
        user_strategy_pattern=[],
        target_sensitive_points=[],
        resolved_points=[],
        unresolved_points=[],
        important_events=[],
        next_suggested_focus="",
    )


def _unique_strings(values: list[str], *, limit: int) -> list[str]:
    result: list[str] = []
    for value in values:
        item = str(value).strip()
        if item and item not in result:
            result.append(item[:240])
        if len(result) >= limit:
            break
    return result


def _prompt_version(component, attribute: str, fallback: str) -> str:
    value = getattr(component, attribute, fallback)
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def _digest_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _stable_session_id(request: SessionMessageRequest, persona_id: str) -> str:
    value = f"{persona_id}|{request.scenario}|{request.goal}"
    return f"session_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def _to_legacy_relationship_state(
    previous: RelationshipState,
    state: SimulationState,
) -> RelationshipState:
    emotional_balance = (
        state.relationship_state.psychological_safety
        - state.emotional_state.irritation
        - state.emotional_state.hurt
        - state.emotional_state.defensiveness
    )
    return RelationshipState(
        trust=round(state.relationship_state.trust * 100),
        respect=round(state.relationship_state.respect * 100),
        familiarity=previous.familiarity,
        affinity=round(state.relationship_state.warmth * 100),
        authority=previous.authority,
        emotional=max(-100, min(100, round(emotional_balance * 100))),
    )


def _legacy_delta(
    previous: RelationshipState,
    updated: RelationshipState,
) -> StateDelta:
    return StateDelta(
        trust=_legacy_change(updated.trust - previous.trust),
        respect=_legacy_change(updated.respect - previous.respect),
        familiarity=0,
        affinity=_legacy_change(updated.affinity - previous.affinity),
        authority=0,
        emotional=_legacy_change(updated.emotional - previous.emotional),
    )


def _legacy_change(value: int) -> int:
    return max(-10, min(10, int(value)))


def _attitude_label(action: DecisionAction) -> str:
    return {
        "REPLY_BRIEF": "简短回应",
        "REPLY_COLD": "态度降温",
        "ASK_CLARIFICATION": "需要澄清",
        "SET_BOUNDARY": "明确边界",
        "CONFRONT": "直接指出问题",
    }.get(action, "正常参与交流")


def _dominant_emotion(state: EmotionalState) -> str:
    values = {
        "烦躁": state.irritation,
        "受伤": state.hurt,
        "焦虑": state.anxiety,
        "防御": state.defensiveness,
        "疲惫": state.fatigue,
    }
    label, score = max(values.items(), key=lambda item: item[1])
    return label if score >= 0.2 else "平静"


def _perceived_tone(signals: BehaviorSignals) -> str:
    if signals.boundary_violation >= 0.6:
        return "越界或施压"
    if signals.blame >= 0.6:
        return "带有指责"
    if signals.politeness >= 0.7 and signals.accountability >= 0.5:
        return "礼貌且愿意承担责任"
    if signals.politeness <= 0.3:
        return "直接且不够礼貌"
    return "中性表达"


def _status_text(action: DecisionAction) -> str:
    return {
        "DEFER_REPLY": "对方暂时没有回复。",
        "READ_NO_REPLY": "对方已读了消息。",
        "END_CONVERSATION": "对方结束了本次交流。",
    }.get(action, "")
