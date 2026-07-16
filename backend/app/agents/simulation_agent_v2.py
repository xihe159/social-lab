from __future__ import annotations

import logging
from hashlib import sha256
from uuid import uuid4

from app.agents.simulation.decision_engine import TurnDecisionEngine
from app.agents.simulation.response_generator import (
    ResponseGenerator,
    build_fallback_response,
)
from app.agents.simulation.context_builder import SimulationContextBuilder
from app.agents.simulation.consistency_evaluator import ConsistencyEvaluator
from app.schemas.common import RelationshipState
from app.schemas.session import (
    ChatMessage,
    SessionActionResponse,
    SessionMessageRequest,
    SessionMessageResponse,
    SimulationReply,
    StateDelta,
)
from app.schemas.evidence_retrieval import SessionEvidenceMeta
from app.schemas.consistency_evaluation import (
    ConsistencyEvaluationInput,
    EvaluatorTriggerResult,
    SessionEvaluationMeta,
)
from app.schemas.simulation_decision import (
    BehaviorSignals,
    DecisionAction,
    DecisionMessage,
    TurnDecisionInput,
    TurnAnalysis,
    TurnDecisionOutput,
    TurnDecisionResult,
    ResponsePolicy,
    SimulationStateDelta,
)
from app.schemas.simulation_generation import GeneratedResponse, ResponseGenerationInput
from app.schemas.simulation_state import EmotionalState, SimulationState
from app.schemas.simulation_turn import (
    SafeTurnAnalysis,
    SessionRuntimeMeta,
    SimulationTurnRecord,
)
from app.services.persona_v2_adapter import compile_legacy_persona
from app.services.simulation_state_service import create_initial_simulation_state
from app.services.evidence_retriever import EvidenceRetriever
from app.services.simulation_turn_store import SimulationTurnStore, simulation_turn_store


SILENT_ACTIONS = {"DEFER_REPLY", "READ_NO_REPLY"}
logger = logging.getLogger(__name__)


class SimulationAgentV2:
    """Two-stage V2 pipeline: decision first, language generation second."""

    version = "v2"

    def __init__(
        self,
        decision_engine: TurnDecisionEngine | None = None,
        response_generator: ResponseGenerator | None = None,
        evidence_retriever: EvidenceRetriever | None = None,
        context_builder: SimulationContextBuilder | None = None,
        consistency_evaluator: ConsistencyEvaluator | None = None,
        turn_store: SimulationTurnStore | None = None,
    ) -> None:
        self.decision_engine = decision_engine or TurnDecisionEngine()
        self.response_generator = response_generator or ResponseGenerator()
        self.context_builder = context_builder or SimulationContextBuilder(
            evidence_retriever or EvidenceRetriever()
        )
        self.consistency_evaluator = consistency_evaluator or ConsistencyEvaluator()
        self.turn_store = turn_store or simulation_turn_store

    async def run(self, request: SessionMessageRequest) -> SessionMessageResponse:
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
            for message in request.messages[-8:]
        ]
        evidence_context = self.context_builder.build_evidence_context(
            persona_id=persona_id,
            user_message=request.user_message,
            state=current_state,
            top_k=4,
        )
        retrieval = evidence_context.retrieval

        decision_input = TurnDecisionInput(
            persona=persona_v2,
            current_state=current_state,
            scenario=request.scenario,
            goal=request.goal,
            outcome=request.outcome,
            recent_turns=recent_turns,
            relevant_evidence=list(evidence_context.decision_evidence),
            user_message=request.user_message,
        )
        decision_fallback_used = False
        try:
            decision_result = await self.decision_engine.run(decision_input)
        except Exception:
            decision_fallback_used = True
            decision_result = _fallback_decision_result(current_state)
            logger.exception(
                "decision_engine_failed_using_safe_fallback",
                extra={"persona_id": persona_id, "session_id": session_id},
            )
        response_policy = decision_result.decision.response_policy
        generation_input: ResponseGenerationInput | None = None
        generator_retry_count = 0
        generator_fallback_used = False
        if response_policy.action in SILENT_ACTIONS:
            generated = GeneratedResponse(
                response_text="",
                response_action=response_policy.action,
            )
        else:
            generation_input = ResponseGenerationInput(
                persona=persona_v2,
                current_state=decision_result.updated_state,
                response_policy=response_policy,
                recent_turns=recent_turns,
                user_message=request.user_message,
                relevant_linguistic_evidence=list(evidence_context.linguistic_evidence),
            )
            (
                generated,
                generator_retry_count,
                generator_fallback_used,
            ) = await self._generate_with_recovery(
                generation_input,
                persona_id=persona_id,
                session_id=session_id,
            )

        if decision_fallback_used:
            trigger = EvaluatorTriggerResult(
                triggered=False,
                reasons=["decision_fallback_skips_evaluator"],
            )
        else:
            trigger = self.consistency_evaluator.should_run(
                persona=persona_v2,
                previous_state=current_state,
                decision_result=decision_result,
                generated=generated,
                relevant_evidence=list(evidence_context.decision_evidence),
            )
        evaluation_meta = SessionEvaluationMeta(
            evaluated=False,
            trigger_reasons=trigger.reasons,
        )
        if trigger.triggered:
            evaluation_meta.evaluated = True
            evaluation_input = ConsistencyEvaluationInput(
                persona=persona_v2,
                previous_state=current_state,
                updated_state=decision_result.updated_state,
                response_policy=response_policy,
                generated_response=generated,
                recent_turns=recent_turns,
                user_message=request.user_message,
                relevant_evidence=list(evidence_context.decision_evidence),
                trigger_reasons=trigger.reasons,
            )
            try:
                evaluation = await self.consistency_evaluator.evaluate(evaluation_input)
                evaluation_meta.result = evaluation
                if not evaluation.passed and generation_input is not None:
                    evaluation_meta.retry_count = 1
                    retry_input = generation_input.model_copy(
                        deep=True,
                        update={
                            "consistency_feedback": evaluation.retry_feedback(),
                            "generation_attempt": 2,
                        },
                    )
                    try:
                        generated = await self.response_generator.run(retry_input)
                    except Exception:
                        logger.exception(
                            "consistency_retry_failed_using_initial_response",
                            extra={"persona_id": persona_id, "session_id": session_id},
                        )
            except Exception:
                evaluation_meta.evaluator_failed = True
                logger.exception(
                    "consistency_evaluator_failed_using_initial_response",
                    extra={"persona_id": persona_id, "session_id": session_id},
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
            simulation_state=decision_result.updated_state,
            evidence_meta=SessionEvidenceMeta(
                retrieval_mode=retrieval.retrieval_mode,
                evidence_ids=[item.evidence_id for item in retrieval.items],
                episode_ids=[item.episode_id for item in retrieval.items],
                relevance_scores=[item.relevance_score for item in retrieval.items],
            ),
            evaluation_meta=evaluation_meta,
            runtime_meta=SessionRuntimeMeta(
                decision_fallback_used=decision_fallback_used,
                generator_retry_count=generator_retry_count,
                generator_fallback_used=generator_fallback_used,
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
        return response

    async def _generate_with_recovery(
        self,
        generation_input: ResponseGenerationInput,
        *,
        persona_id: str,
        session_id: str,
    ) -> tuple[GeneratedResponse, int, bool]:
        try:
            return await self.response_generator.run(generation_input), 0, False
        except Exception:
            logger.exception(
                "response_generator_failed_retrying_once",
                extra={"persona_id": persona_id, "session_id": session_id},
            )

        retry_input = generation_input.model_copy(
            deep=True,
            update={
                "generation_attempt": 2,
                "consistency_feedback": ["保持原 Response Policy，重新生成合法且简洁的回复。"],
            },
        )
        try:
            return await self.response_generator.run(retry_input), 1, False
        except Exception:
            logger.exception(
                "response_generator_retry_failed_using_deterministic_fallback",
                extra={"persona_id": persona_id, "session_id": session_id},
            )
            return build_fallback_response(generation_input.response_policy), 1, True

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
                evaluator_passed=(
                    evaluation.result.passed
                    if evaluation and evaluation.result
                    else None
                ),
                decision_fallback_used=bool(
                    response.runtime_meta and response.runtime_meta.decision_fallback_used
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


def _fallback_decision_result(state: SimulationState) -> TurnDecisionResult:
    zero_delta = SimulationStateDelta(
        trust=0,
        respect=0,
        warmth=0,
        patience=0,
        psychological_safety=0,
        willingness_to_engage=0,
        irritation=0,
        hurt=0,
        anxiety=0,
        defensiveness=0,
        fatigue=0,
        conflict_level=0,
        topic_resolution=0,
        boundary_pressure=0,
    )
    return TurnDecisionResult(
        decision=TurnDecisionOutput(
            turn_analysis=TurnAnalysis(
                intent="decision_engine_fallback",
                behavior_signals=BehaviorSignals(
                    politeness=0.5,
                    clarity=0.5,
                    accountability=0.5,
                    pressure=0.0,
                    blame=0.0,
                    vulnerability=0.0,
                    boundary_violation=0.0,
                    honesty_signal=0.5,
                ),
                detected_events=["decision_engine_fallback"],
            ),
            state_delta=zero_delta,
            response_policy=ResponsePolicy(
                action="REPLY_NORMAL",
                content_goals=["对用户当前表达作出简短、中性的回应"],
                tone="neutral",
                reply_length="short",
                must_avoid=["升级冲突", "虚构事实"],
            ),
            confidence=0.0,
        ),
        updated_state=state.model_copy(deep=True),
    )


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
