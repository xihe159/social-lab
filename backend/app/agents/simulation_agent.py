from __future__ import annotations

from app.agents.prompts import SIMULATION_SYSTEM_PROMPT, build_simulation_user_prompt
from app.llm.client import generate_structured
from app.schemas.common import RelationshipState
from app.schemas.session import (
    ChatMessage,
    SessionMessageRequest,
    SessionMessageResponse,
    SimulationReply,
    StateDelta,
)


class SimulationAgentV1:
    """
    SimulationAgent 负责在一次模拟会话中扮演目标人物进行回复。

    设计原则：
    1. Agent 层只负责业务流程，不直接接触 OpenAI / Qwen SDK。
    2. LLM 调用统一交给 app.llm.client.generate_structured。
    3. LLM 只生成 SimulationReply；Agent 负责组装 SessionMessageResponse。
    4. 单轮关系状态变化必须经过业务级 post_process 修正。
    """

    async def run(self, request: SessionMessageRequest) -> SessionMessageResponse:
        """
        根据当前 Persona、历史消息和用户最新发言，生成目标人物回复。

        Args:
            request: 单轮模拟对话请求。

        Returns:
            SessionMessageResponse: 目标人物回复、结构化模拟分析、更新后的关系状态。
        """

        payload = request.model_dump()

        simulation = await generate_structured(
            system_prompt=SIMULATION_SYSTEM_PROMPT,
            user_prompt=build_simulation_user_prompt(payload),
            output_model=SimulationReply,
            temperature=0.55,
        )

        return self.post_process(simulation=simulation, request=request)

    def post_process(
        self,
        *,
        simulation: SimulationReply,
        request: SessionMessageRequest,
    ) -> SessionMessageResponse:
        """
        对 LLM 已经通过 Pydantic 校验的 SimulationReply 做业务级修正。

        Pydantic 负责结构合法性，post_process 负责业务合理性，例如：
        - 目标人物回复不能为空；
        - 单轮 state_delta 不应过大；
        - 风险标签不应无限增长；
        - updated_state 必须基于当前 persona.state 计算。
        """

        self._normalize_text_fields(simulation, request)
        self._normalize_state_delta(simulation.state_delta)
        self._normalize_risk_flags(simulation)

        updated_state = apply_state_delta(
            state=request.persona.state,
            delta=simulation.state_delta,
        )

        return SessionMessageResponse(
            target_message=ChatMessage(role="target", content=simulation.reply),
            simulation=simulation,
            updated_state=updated_state,
        )

    def _normalize_text_fields(
        self,
        simulation: SimulationReply,
        request: SessionMessageRequest,
    ) -> None:
        simulation.reply = self._clean_text(
            simulation.reply,
            default=self._default_reply(request),
        )
        simulation.reply = self._truncate(simulation.reply, max_length=500)

        simulation.attitude = self._clean_text(
            simulation.attitude,
            default="保持谨慎，愿意继续听用户说明。",
        )
        simulation.emotion = self._clean_text(
            simulation.emotion,
            default="中性偏谨慎",
        )
        simulation.perceived_user_tone = self._clean_text(
            simulation.perceived_user_tone,
            default="语气较为直接，需要结合上下文继续判断。",
        )

    def _normalize_state_delta(self, delta: StateDelta) -> None:
        """
        单轮对话只允许小幅改变关系状态。
        即使 schema 已经限制为 -10 到 10，这里仍保留二次 clamp，方便后续业务规则继续扩展。
        """

        delta.trust = self._clamp(delta.trust, -10, 10)
        delta.respect = self._clamp(delta.respect, -10, 10)
        delta.familiarity = self._clamp(delta.familiarity, -10, 10)
        delta.affinity = self._clamp(delta.affinity, -10, 10)
        delta.authority = self._clamp(delta.authority, -10, 10)
        delta.emotional = self._clamp(delta.emotional, -10, 10)

    def _normalize_risk_flags(self, simulation: SimulationReply) -> None:
        cleaned: list[str] = []
        for item in simulation.risk_flags:
            item = item.strip()
            if not item:
                continue
            if item not in cleaned:
                cleaned.append(self._truncate(item, max_length=80))

        simulation.risk_flags = cleaned[:5]

    def _default_reply(self, request: SessionMessageRequest) -> str:
        if request.scenario == "advisor":
            return "你先把目前的具体情况、已经做过的尝试和接下来的计划说清楚，我再判断怎么处理。"
        if request.scenario == "work":
            return "你先把背景、影响范围和你希望我配合的事项说清楚。"
        if request.scenario == "social":
            return "嗯，我在听。你可以具体说说你想表达什么。"
        return "你可以再具体说明一下。"

    @staticmethod
    def _clean_text(value: str, *, default: str) -> str:
        value = value.strip() if isinstance(value, str) else ""
        return value or default

    @staticmethod
    def _truncate(value: str, *, max_length: int) -> str:
        value = value.strip()
        if len(value) <= max_length:
            return value
        return value[: max_length - 1].rstrip() + "…"

    @staticmethod
    def _clamp(value: int, low: int, high: int) -> int:
        return max(low, min(high, int(value)))


def apply_state_delta(
    *,
    state: RelationshipState,
    delta: StateDelta,
) -> RelationshipState:
    """
    根据本轮对话增量计算新的 RelationshipState。

    注意：
    - trust/respect/familiarity/affinity/authority 范围是 0 到 100；
    - emotional 范围是 -100 到 100；
    - 这里返回新对象，不直接修改原 persona.state，避免副作用。
    """

    def clamp(value: int, low: int, high: int) -> int:
        return max(low, min(high, int(value)))

    return RelationshipState(
        trust=clamp(state.trust + delta.trust, 0, 100),
        respect=clamp(state.respect + delta.respect, 0, 100),
        familiarity=clamp(state.familiarity + delta.familiarity, 0, 100),
        affinity=clamp(state.affinity + delta.affinity, 0, 100),
        authority=clamp(state.authority + delta.authority, 0, 100),
        emotional=clamp(state.emotional + delta.emotional, -100, 100),
    )


# Backwards-compatible public name. Phase 0 keeps every existing import and
# caller working while the orchestrator moves to the versioned factory.
SimulationAgent = SimulationAgentV1
