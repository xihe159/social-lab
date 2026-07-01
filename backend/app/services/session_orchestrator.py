# social-lab/backend/app/services/session_orchestrator.py
# 2026/06/30

from __future__ import annotations

from app.agents.memory_agent import MemoryAgent
from app.agents.simulation_agent import SimulationAgent, apply_state_delta
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
from app.schemas.state import StateEvaluateRequest
from app.schemas.safety import SafetyCheckRequest, SafetyCheckResponse

class SessionOrchestrator:
    """
    SessionOrchestrator 负责单轮模拟对话的 Agent 编排。

    当前流程：
    1. SafetyAgent：检查用户输入是否存在隐私、操控、骚扰、威胁等风险
    2. SimulationAgent：生成目标人物回复
    3. StateAgent：重新评估关系状态变化
    4. MemoryAgent：更新当前会话短期记忆

    设计原则：
    - SafetyAgent 高风险 block 时，不继续调用后续 Agent
    - SimulationAgent 是主流程，失败才让接口失败
    - StateAgent 是增强模块，失败时回退到 SimulationAgent 的状态变化
    - MemoryAgent 是增强模块，失败时回退到上一轮 memory
    """

    def __init__(self):
        self.safety_agent = SafetyAgent()
        self.simulation_agent = SimulationAgent()
        self.state_agent = StateAgent()
        self.memory_agent = MemoryAgent()

    async def handle_message(
        self,
        request: SessionMessageRequest,
    ) -> SessionMessageResponse:
        print("[SessionOrchestrator] Start SafetyAgent")

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

        print("[SessionOrchestrator] SafetyAgent result:", safety_result.model_dump())

        if self._should_block(safety_result):
            print("[SessionOrchestrator] SafetyAgent blocked this message")
            return self._build_blocked_response(
                request=request,
                safety_result=safety_result,
            )

        print("[SessionOrchestrator] Start SimulationAgent")

        simulation_response = await self.simulation_agent.run(request)
        simulation_response.safety = safety_result

        self._append_safety_warning_if_needed(
            risk_flags=simulation_response.simulation.risk_flags,
            safety_result=safety_result,
        )

        print("[SessionOrchestrator] SimulationAgent success")
        print("[SessionOrchestrator] Start StateAgent")

        # 先保留 SimulationAgent 的初始状态判断，作为 StateAgent 失败时的兜底。
        state_delta = simulation_response.simulation.state_delta
        risk_flags = simulation_response.simulation.risk_flags

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
                perceived_user_tone=simulation_response.simulation.perceived_user_tone,
            )

            state_evaluation = await self.state_agent.run(state_request)

            print("[SessionOrchestrator] StateAgent success")
            print(
                "[SessionOrchestrator] StateAgent evaluation:",
                state_evaluation.model_dump(),
            )

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

        except LLMClientError as exc:
            print(
                "[SessionOrchestrator] StateAgent LLM failed, "
                "fallback to SimulationAgent result"
            )
            print("[SessionOrchestrator] StateAgent LLM error:", str(exc))

        except Exception as exc:
            print(
                "[SessionOrchestrator] StateAgent unexpected failed, "
                "fallback to SimulationAgent result"
            )
            print("[SessionOrchestrator] StateAgent error type:", exc.__class__.__name__)
            print("[SessionOrchestrator] StateAgent error:", repr(exc))

        print("[SessionOrchestrator] Start MemoryAgent")

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

            print("[SessionOrchestrator] MemoryAgent success")
            print(
                "[SessionOrchestrator] MemoryAgent memory:",
                memory_response.memory.model_dump(),
            )

            # 这里使用 getattr，避免 memory_reason / new_facts / next_focus
            # 在 schema 尚未同步时再次触发 AttributeError。
            memory_reason = getattr(memory_response, "memory_reason", "")
            if memory_reason:
                print("[SessionOrchestrator] MemoryAgent reason:", memory_reason)

            simulation_response.updated_memory = memory_response.memory

        except LLMClientError as exc:
            print(
                "[SessionOrchestrator] MemoryAgent LLM failed, "
                "fallback to previous memory"
            )
            print("[SessionOrchestrator] MemoryAgent LLM error:", str(exc))
            simulation_response.updated_memory = request.memory

        except Exception as exc:
            print(
                "[SessionOrchestrator] MemoryAgent unexpected failed, "
                "fallback to previous memory"
            )
            print("[SessionOrchestrator] MemoryAgent error type:", exc.__class__.__name__)
            print("[SessionOrchestrator] MemoryAgent error:", repr(exc))
            simulation_response.updated_memory = request.memory

        return simulation_response

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
        """将 SafetyAgent 的 warn/rewrite 提醒合并进 risk_flags。"""
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
        )
