# social-lab/backend/app/services/session_orchestrator.py
# 2026/07/16

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from uuid import uuid4

from app.agents.memory_agent import MemoryAgent
from app.agents.simulation_agent import apply_state_delta
from app.agents.simulation_agent_factory import create_simulation_agent
from app.agents.state_agent import StateAgent
from app.agents.safety_agent import SafetyAgent

from app.llm.client import LLMClientError

from app.schemas.memory import MemoryUpdateRequest
from app.schemas.session import (
    ChatMessage,
    SessionMessageRequest,
    SessionMessageResponse,
    SimulationReply,
    StateDelta,
)
from app.schemas.state import StateEvaluateRequest, StateEvaluationResponse
from app.schemas.safety import SafetyCheckRequest, SafetyCheckResponse


logger = logging.getLogger(__name__)


class SessionOrchestrator:
    """
    SessionOrchestrator 负责单轮模拟对话的 Agent 编排。

    当前流程：
    1. SafetyAgent：检查用户输入是否存在隐私、操控、骚扰、威胁等风险；
    2. SimulationAgent：生成目标人物回复；
    3. StateAgent：重新评估关系状态变化，并更新对话氛围与节奏动态指标；
    4. MemoryAgent：更新当前会话短期记忆。

    设计原则：
    - SafetyAgent 高风险 block 时，不继续调用后续 Agent；
    - SimulationAgent 是主流程，失败才让接口失败；
    - StateAgent 是增强模块，失败时回退到 SimulationAgent 的状态变化；
    - MemoryAgent 是增强模块，失败时回退到上一轮 memory。
    """

    def __init__(self, simulation_agent_version: str | None = None):
        self.safety_agent = SafetyAgent()
        (
            self.simulation_agent_version,
            self.simulation_agent,
        ) = create_simulation_agent(simulation_agent_version)
        self.state_agent = StateAgent()
        self.memory_agent = MemoryAgent()

        logger.info(
            "session_orchestrator_initialized",
            extra={
                "service": "SessionOrchestrator",
                "agents": [
                    "SafetyAgent",
                    "StrategyAgentV2(active inside SimulationAgentV2)",
                    "SimulationAgent",
                    "EvaluationAgentV2(bounded feedback inside SimulationAgentV2)",
                    "StateAgent",
                    "MemoryAgent",
                ],
                "simulation_agent_version": self.simulation_agent_version,
            },
        )

    async def handle_message(
        self,
        request: SessionMessageRequest,
        *,
        defer_background: Callable[..., None] | None = None,
    ) -> SessionMessageResponse:
        """
        处理一轮用户消息，并返回目标人物回复、状态变化、动态指标、记忆更新和安全检查结果。
        """
        trace_id = uuid4().hex[:8]
        started_at = time.perf_counter()

        logger.info(
            "session_message_started",
            extra={
                "trace_id": trace_id,
                "scenario": request.scenario,
                "message_count": len(request.messages),
                "has_memory": request.memory is not None,
                "has_current_dynamics": request.current_dynamics is not None,
                "user_message_length": len(request.user_message),
                "goal_length": len(request.goal),
                "outcome_length": len(request.outcome or ""),
            },
        )

        safety_result = await self._run_safety_agent(
            trace_id=trace_id,
            request=request,
        )

        if self._should_block(safety_result):
            logger.warning(
                "session_message_blocked",
                extra={
                    "trace_id": trace_id,
                    "agent": "SafetyAgent",
                    "allowed": safety_result.allowed,
                    "action": safety_result.action,
                    "risk_level": safety_result.risk_level,
                    "risk_types": safety_result.risk_types,
                    "should_redact": safety_result.should_redact,
                    "redacted_fields": safety_result.redacted_fields,
                },
            )

            blocked_response = self._build_blocked_response(
                request=request,
                safety_result=safety_result,
            )

            total_duration_ms = self._elapsed_ms(started_at)

            logger.info(
                "session_message_finished",
                extra={
                    "trace_id": trace_id,
                    "status": "blocked",
                    "duration_ms": total_duration_ms,
                    "scenario": request.scenario,
                    "final_risk_flags": blocked_response.simulation.risk_flags,
                    "has_updated_memory": blocked_response.updated_memory is not None,
                    "has_state_metrics": blocked_response.state_metrics is not None,
                },
            )

            return blocked_response

        simulation_response = await self._run_simulation_agent(
            trace_id=trace_id,
            request=request,
            safety_result=safety_result,
            defer_background=defer_background,
        )

        # 先保留 SimulationAgent 的初始状态判断，作为 StateAgent 失败时的兜底。
        state_delta = simulation_response.simulation.state_delta
        risk_flags = simulation_response.simulation.risk_flags

        if self.simulation_agent_version == "v1":
            state_delta, risk_flags = await self._run_state_agent_with_fallback(
                trace_id=trace_id,
                request=request,
                simulation_response=simulation_response,
                fallback_state_delta=state_delta,
                fallback_risk_flags=risk_flags,
                safety_result=safety_result,
            )
        else:
            logger.info(
                "agent_skipped",
                extra={
                    "trace_id": trace_id,
                    "agent": "StateAgent",
                    "reason": "v2_strategy_policy_adapter_already_updated_state",
                },
            )

        simulation_response.updated_memory = await self._run_memory_agent_with_fallback(
            trace_id=trace_id,
            request=request,
            simulation_response=simulation_response,
            state_delta=state_delta,
            risk_flags=risk_flags,
        )

        total_duration_ms = self._elapsed_ms(started_at)

        logger.info(
            "session_message_finished",
            extra={
                "trace_id": trace_id,
                "status": "success",
                "duration_ms": total_duration_ms,
                "scenario": request.scenario,
                "final_risk_flags": simulation_response.simulation.risk_flags,
                "reply_length": len(simulation_response.target_message.content),
                "has_updated_memory": simulation_response.updated_memory is not None,
                "has_state_metrics": simulation_response.state_metrics is not None,
                "rhythm_label": simulation_response.rhythm_label,
                "atmosphere_label": simulation_response.atmosphere_label,
                "recommended_next_move": simulation_response.recommended_next_move,
            },
        )

        return simulation_response

    async def _run_safety_agent(
        self,
        *,
        trace_id: str,
        request: SessionMessageRequest,
    ) -> SafetyCheckResponse:
        agent_started_at = time.perf_counter()

        logger.info(
            "agent_started",
            extra={
                "trace_id": trace_id,
                "agent": "SafetyAgent",
                "context": "session_message",
                "scenario": request.scenario,
                "message_count": len(request.messages),
                "has_memory": request.memory is not None,
                "user_message_length": len(request.user_message),
            },
        )

        safety_result = await self.safety_agent.run(
            SafetyCheckRequest(
                context="session_message",
                scenario=request.scenario,
                goal=request.goal,
                outcome=request.outcome,
                persona=request.persona,
                messages=request.messages,
                user_message=request.user_message,
                current_memory=request.memory,
            )
        )

        logger.info(
            "agent_finished",
            extra={
                "trace_id": trace_id,
                "agent": "SafetyAgent",
                "duration_ms": self._elapsed_ms(agent_started_at),
                "allowed": safety_result.allowed,
                "action": safety_result.action,
                "risk_level": safety_result.risk_level,
                "risk_types": safety_result.risk_types,
                "should_redact": safety_result.should_redact,
                "redacted_fields": safety_result.redacted_fields,
                "has_user_notice": bool(safety_result.user_notice.strip()),
                "has_safe_rewrite_hint": bool(
                    safety_result.safe_rewrite_hint.strip()
                ),
            },
        )

        return safety_result

    async def _run_simulation_agent(
        self,
        *,
        trace_id: str,
        request: SessionMessageRequest,
        safety_result: SafetyCheckResponse,
        defer_background: Callable[..., None] | None = None,
    ) -> SessionMessageResponse:
        agent_started_at = time.perf_counter()

        logger.info(
            "agent_started",
            extra={
                "trace_id": trace_id,
                "agent": "SimulationAgent",
                "simulation_agent_version": self.simulation_agent_version,
                "scenario": request.scenario,
                "message_count": len(request.messages),
                "has_memory": request.memory is not None,
                "has_current_dynamics": request.current_dynamics is not None,
            },
        )

        if self.simulation_agent_version == "v2":
            simulation_response = await self.simulation_agent.run(
                request,
                defer_background=defer_background,
            )
        else:
            simulation_response = await self.simulation_agent.run(request)
        evaluation_meta = simulation_response.evaluation_meta
        runtime_meta = simulation_response.runtime_meta
        strategy_meta = simulation_response.strategy_meta

        # 把 SafetyAgent 的检查结果合并进主响应。
        simulation_response.safety = safety_result

        # 如果 SafetyAgent 给出 warn/rewrite，合并到 risk_flags 中。
        self._append_safety_warning_if_needed(
            risk_flags=simulation_response.simulation.risk_flags,
            safety_result=safety_result,
        )

        logger.info(
            "agent_finished",
            extra={
                "trace_id": trace_id,
                "agent": "SimulationAgent",
                "simulation_agent_version": self.simulation_agent_version,
                "duration_ms": self._elapsed_ms(agent_started_at),
                "reply_length": len(simulation_response.target_message.content),
                "attitude": simulation_response.simulation.attitude,
                "emotion": simulation_response.simulation.emotion,
                "perceived_user_tone": (
                    simulation_response.simulation.perceived_user_tone
                ),
                "state_delta": simulation_response.simulation.state_delta.model_dump(),
                "risk_flags": simulation_response.simulation.risk_flags,
                "updated_state": simulation_response.updated_state.model_dump(),
                "simulation_evaluated": bool(
                    evaluation_meta and evaluation_meta.evaluated
                ),
                "initial_evaluation_score": (
                    evaluation_meta.initial_score if evaluation_meta else None
                ),
                "final_evaluation_score": (
                    evaluation_meta.final_score if evaluation_meta else None
                ),
                "evaluation_score_delta": (
                    evaluation_meta.score_delta if evaluation_meta else None
                ),
                "evaluation_verdict": (
                    evaluation_meta.final_verdict.value
                    if evaluation_meta and evaluation_meta.final_verdict
                    else None
                ),
                "failure_attribution": (
                    evaluation_meta.final_failure_attribution.value
                    if evaluation_meta
                    and evaluation_meta.final_failure_attribution
                    else None
                ),
                "feedback_action": (
                    evaluation_meta.feedback_action.value
                    if evaluation_meta
                    else "none"
                ),
                "feedback_retry_count": (
                    evaluation_meta.retry_count if evaluation_meta else 0
                ),
                "evaluation_agent_failed": bool(
                    evaluation_meta and evaluation_meta.evaluator_failed
                ),
                "final_evaluation_failed": bool(
                    evaluation_meta and evaluation_meta.final_evaluator_failed
                ),
                "decision_fallback_used": bool(
                    runtime_meta and runtime_meta.decision_fallback_used
                ),
                "strategy_policy_id": (
                    strategy_meta.policy_id if strategy_meta else None
                ),
                "strategy_action": (
                    strategy_meta.strategy_action if strategy_meta else None
                ),
                "strategy_confidence": (
                    strategy_meta.confidence if strategy_meta else None
                ),
                "strategy_fallback_used": bool(
                    runtime_meta and runtime_meta.strategy_fallback_used
                ),
                "generator_retry_count": (
                    runtime_meta.generator_retry_count if runtime_meta else 0
                ),
                "generator_fallback_used": bool(
                    runtime_meta and runtime_meta.generator_fallback_used
                ),
                "evaluation_call_count": (
                    runtime_meta.evaluation_call_count if runtime_meta else 0
                ),
                "evaluation_execution_mode": (
                    evaluation_meta.execution_mode if evaluation_meta else "not_run"
                ),
                "evaluation_background_scheduled": bool(
                    evaluation_meta and evaluation_meta.background_scheduled
                ),
                "evaluation_critical_reasons": (
                    evaluation_meta.critical_reasons if evaluation_meta else []
                ),
                "strategy_replan_count": (
                    runtime_meta.strategy_replan_count if runtime_meta else 0
                ),
                "simulation_revision_count": (
                    runtime_meta.simulation_revision_count if runtime_meta else 0
                ),
                "rejected_candidate_discarded": bool(
                    runtime_meta and runtime_meta.rejected_candidate_discarded
                ),
            },
        )

        return simulation_response

    async def _run_state_agent_with_fallback(
        self,
        *,
        trace_id: str,
        request: SessionMessageRequest,
        simulation_response: SessionMessageResponse,
        fallback_state_delta: StateDelta,
        fallback_risk_flags: list[str],
        safety_result: SafetyCheckResponse,
    ) -> tuple[StateDelta, list[str]]:
        agent_started_at = time.perf_counter()

        logger.info(
            "agent_started",
            extra={
                "trace_id": trace_id,
                "agent": "StateAgent",
                "scenario": request.scenario,
                "fallback": "simulation_agent_state_delta",
                "has_current_dynamics": request.current_dynamics is not None,
            },
        )

        try:
            state_request = StateEvaluateRequest(
                scenario=request.scenario,
                goal=request.goal,
                outcome=request.outcome,
                persona=request.persona,
                messages=request.messages,
                user_message=request.user_message,
                target_reply=simulation_response.target_message.content,
                current_state=request.persona.state,
                simulation_attitude=simulation_response.simulation.attitude,
                simulation_emotion=simulation_response.simulation.emotion,
                perceived_user_tone=(
                    simulation_response.simulation.perceived_user_tone
                ),
                current_dynamics=request.current_dynamics,
            )

            state_evaluation = await self.state_agent.run(state_request)

            # StateAgent 成功后，用 StateAgent 的结果覆盖 SimulationAgent 的初始判断。
            state_delta = state_evaluation.state_delta
            risk_flags = state_evaluation.risk_flags

            self._append_safety_warning_if_needed(
                risk_flags=risk_flags,
                safety_result=safety_result,
            )

            simulation_response.simulation.state_delta = state_delta
            simulation_response.simulation.risk_flags = risk_flags
            simulation_response.updated_state = apply_state_delta(
                state=request.persona.state,
                delta=state_delta,
            )

            # 新增：把对话氛围与节奏动态指标写回 SessionMessageResponse。
            self._attach_dynamics_to_response(
                simulation_response=simulation_response,
                state_evaluation=state_evaluation,
            )

            dynamics_update = state_evaluation.dynamics_update
            updated_dynamics = dynamics_update.updated_dynamics

            logger.info(
                "agent_finished",
                extra={
                    "trace_id": trace_id,
                    "agent": "StateAgent",
                    "duration_ms": self._elapsed_ms(agent_started_at),
                    "status": "success",
                    "state_delta": state_delta.model_dump(),
                    "risk_flags": risk_flags,
                    "updated_state": simulation_response.updated_state.model_dump(),
                    "dynamics_delta": dynamics_update.dynamics_delta.model_dump(),
                    "updated_dynamics": updated_dynamics.model_dump(),
                    "rhythm_label": updated_dynamics.rhythm_label,
                    "atmosphere_label": updated_dynamics.atmosphere_label,
                    "recommended_next_move": updated_dynamics.recommended_next_move,
                    "control_suggestion_count": len(
                        dynamics_update.control_suggestions
                    ),
                },
            )

            return state_delta, risk_flags

        except LLMClientError:
            logger.exception(
                "agent_llm_failed_fallback",
                extra={
                    "trace_id": trace_id,
                    "agent": "StateAgent",
                    "duration_ms": self._elapsed_ms(agent_started_at),
                    "fallback": "use_simulation_agent_state_delta",
                },
            )

            return fallback_state_delta, fallback_risk_flags

        except Exception:
            logger.exception(
                "agent_unexpected_failed_fallback",
                extra={
                    "trace_id": trace_id,
                    "agent": "StateAgent",
                    "duration_ms": self._elapsed_ms(agent_started_at),
                    "fallback": "use_simulation_agent_state_delta",
                },
            )

            return fallback_state_delta, fallback_risk_flags

    async def _run_memory_agent_with_fallback(
        self,
        *,
        trace_id: str,
        request: SessionMessageRequest,
        simulation_response: SessionMessageResponse,
        state_delta: StateDelta,
        risk_flags: list[str],
    ):
        agent_started_at = time.perf_counter()

        logger.info(
            "agent_started",
            extra={
                "trace_id": trace_id,
                "agent": "MemoryAgent",
                "scenario": request.scenario,
                "has_previous_memory": request.memory is not None,
                "risk_flag_count": len(risk_flags),
                "has_state_metrics": simulation_response.state_metrics is not None,
            },
        )

        try:
            memory_request = MemoryUpdateRequest(
                scenario=request.scenario,
                goal=request.goal,
                outcome=request.outcome,
                persona=request.persona,
                messages=request.messages,
                user_message=request.user_message,
                target_reply=simulation_response.target_message.content,
                state_delta=state_delta,
                risk_flags=risk_flags,
                current_memory=request.memory,
            )

            memory_response = await self.memory_agent.run(memory_request)

            memory_reason = getattr(memory_response, "memory_reason", "")
            new_facts = getattr(memory_response, "new_facts", [])
            next_focus = getattr(memory_response, "next_focus", "")

            logger.info(
                "agent_finished",
                extra={
                    "trace_id": trace_id,
                    "agent": "MemoryAgent",
                    "duration_ms": self._elapsed_ms(agent_started_at),
                    "status": "success",
                    "has_memory": memory_response.memory is not None,
                    "conversation_summary_length": len(
                        memory_response.memory.conversation_summary
                    ),
                    "user_strategy_pattern_count": len(
                        memory_response.memory.user_strategy_pattern
                    ),
                    "target_sensitive_point_count": len(
                        memory_response.memory.target_sensitive_points
                    ),
                    "resolved_point_count": len(
                        memory_response.memory.resolved_points
                    ),
                    "unresolved_point_count": len(
                        memory_response.memory.unresolved_points
                    ),
                    "important_event_count": len(
                        memory_response.memory.important_events
                    ),
                    "has_memory_reason": bool(str(memory_reason).strip()),
                    "new_fact_count": len(new_facts),
                    "has_next_focus": bool(str(next_focus).strip()),
                },
            )

            return memory_response.memory

        except LLMClientError:
            logger.exception(
                "agent_llm_failed_fallback",
                extra={
                    "trace_id": trace_id,
                    "agent": "MemoryAgent",
                    "duration_ms": self._elapsed_ms(agent_started_at),
                    "fallback": "use_previous_memory",
                },
            )

            return request.memory

        except Exception:
            logger.exception(
                "agent_unexpected_failed_fallback",
                extra={
                    "trace_id": trace_id,
                    "agent": "MemoryAgent",
                    "duration_ms": self._elapsed_ms(agent_started_at),
                    "fallback": "use_previous_memory",
                },
            )

            return request.memory

    def _attach_dynamics_to_response(
        self,
        *,
        simulation_response: SessionMessageResponse,
        state_evaluation: StateEvaluationResponse,
    ) -> None:
        """
        把 StateAgent 输出的 dynamics_update 展开到 SessionMessageResponse。

        前端可以：
        1. 直接展示 state_metrics；
        2. 下一轮把 state_metrics 作为 current_dynamics 传回；
        3. 生成报告时累积 state_timeline。
        """

        dynamics_update = state_evaluation.dynamics_update
        updated_dynamics = dynamics_update.updated_dynamics

        simulation_response.dynamics_update = dynamics_update
        simulation_response.state_metrics = updated_dynamics

        simulation_response.rhythm_label = updated_dynamics.rhythm_label
        simulation_response.atmosphere_label = updated_dynamics.atmosphere_label
        simulation_response.recommended_next_move = (
            updated_dynamics.recommended_next_move
        )
        simulation_response.control_suggestions = (
            dynamics_update.control_suggestions or []
        )

    def _should_block(self, safety_result: SafetyCheckResponse) -> bool:
        return (
            not safety_result.allowed
            or safety_result.action == "block"
            or safety_result.risk_level == "high"
        )

    def _append_safety_warning_if_needed(
        self,
        *,
        risk_flags: list[str],
        safety_result: SafetyCheckResponse,
    ) -> None:
        """
        将 SafetyAgent 的 warn/rewrite 提醒合并进 risk_flags。
        """
        if safety_result.action not in ("warn", "rewrite"):
            return

        warning = safety_result.user_notice.strip()

        if warning and warning not in risk_flags:
            risk_flags.append(warning)

    def _build_blocked_response(
        self,
        *,
        request: SessionMessageRequest,
        safety_result: SafetyCheckResponse,
    ) -> SessionMessageResponse:
        zero_delta = StateDelta(
            trust=0,
            respect=0,
            familiarity=0,
            affinity=0,
            authority=0,
            emotional=0,
        )

        notice = safety_result.user_notice.strip() or "当前输入包含安全风险，已停止继续模拟。"

        safe_rewrite_hint = safety_result.safe_rewrite_hint.strip()
        if safe_rewrite_hint:
            notice = f"{notice}\n\n安全改写建议：{safe_rewrite_hint}"

        target_message = ChatMessage(role="target", content=notice)

        return SessionMessageResponse(
            target_message=target_message,
            simulation=SimulationReply(
                reply=notice,
                attitude="安全拦截",
                emotion="中立",
                perceived_user_tone="存在安全风险",
                state_delta=zero_delta,
                risk_flags=safety_result.risk_types,
            ),
            updated_state=request.persona.state,
            updated_memory=request.memory,
            safety=safety_result,
            state_metrics=request.current_dynamics,
            rhythm_label=(
                request.current_dynamics.rhythm_label
                if request.current_dynamics
                else None
            ),
            atmosphere_label=(
                request.current_dynamics.atmosphere_label
                if request.current_dynamics
                else None
            ),
            recommended_next_move="pause",
            control_suggestions=[
                "当前输入触发安全风险，建议先暂停推进，改用更安全、非施压的表达。"
            ],
        )

    @staticmethod
    def _elapsed_ms(started_at: float) -> int:
        return int((time.perf_counter() - started_at) * 1000)
