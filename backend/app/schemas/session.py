from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import RelationshipState, ScenarioKey
from app.schemas.persona import Persona
from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.memory import SessionMemory
from app.schemas.safety import SafetyCheckResponse
from app.schemas.simulation_decision import ResponseAction
from app.schemas.simulation_state import SimulationState
from app.schemas.evidence_retrieval import SessionEvidenceMeta
from app.schemas.consistency_evaluation import SessionEvaluationMeta
from app.schemas.simulation_turn import SessionRuntimeMeta
from app.schemas.dynamics import (
    AtmosphereLabel,
    ConversationDynamics,
    ConversationDynamicsUpdate,
    RecommendedNextMove,
    RhythmLabel,
)


class ChatMessage(BaseModel):
    """
    一条模拟对话消息。

    role:
    - user: 真实用户
    - target: 被模拟的目标人物
    - system: 系统消息，通常用于内部调试或兼容
    """

    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "target", "system"] = Field(description="消息发送者角色")
    content: str = Field(description="消息正文")


class StateDelta(BaseModel):
    """
    单轮对话导致的关系状态变化。

    注意：
    这里是增量，不是最终状态。
    取值范围故意限制较小，避免模型在单轮回复中大幅改变关系。
    """

    model_config = ConfigDict(extra="forbid")

    trust: int = Field(ge=-10, le=10, description="信任程度变化")
    respect: int = Field(ge=-10, le=10, description="尊重程度变化")
    familiarity: int = Field(ge=-10, le=10, description="熟悉程度变化")
    affinity: int = Field(ge=-10, le=10, description="亲近程度变化")
    authority: int = Field(ge=-10, le=10, description="权力距离或权威感变化")
    emotional: int = Field(
        ge=-10,
        le=10,
        description="情绪稳定度变化，负数代表更紧张或更敏感",
    )


class SessionMessageRequest(BaseModel):
    """
    用户发送一条消息后，请求 Target / Simulation Agent 生成目标人物回复。

    memory:
    - 可选字段，用于保存当前会话的短期记忆。
    - 前端暂时不传也可以正常运行。
    - 后续前端可以把上一次返回的 updated_memory 再传回来，
      让 MemoryAgent 在多轮对话中持续更新会话摘要。

    current_dynamics:
    - 可选字段，用于保存上一轮对话后的氛围与节奏指标。
    - 前端第一轮可以不传。
    - 后续前端可以把上一轮返回的 state_metrics 再传回来，
      让 StateAgent 实现动态指标连续更新。
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scenario: ScenarioKey

    goal: str = Field(
        description="用户想通过本次沟通达成的目标",
        validation_alias=AliasChoices("goal", "user_goal"),
        serialization_alias="goal",
    )

    outcome: str = Field(default="", description="用户期待的理想结果")

    role: str = Field(default="", description="目标人物身份；V2 人物转换使用")
    relation: str = Field(default="", description="双方关系；V2 人物转换使用")

    persona: Persona

    persona_v2: Optional[PersonaModelV2] = Field(
        default=None,
        description="画像生成阶段编译的 V2 人物；为空时兼容旧画像转换",
    )

    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="已有对话历史",
    )

    user_message: str = Field(description="用户最新输入的消息")

    memory: Optional[SessionMemory] = Field(
        default=None,
        description="当前会话短期记忆；首次对话可以为空",
    )

    current_dynamics: Optional[ConversationDynamics] = Field(
        default=None,
        description="上一轮对话后的氛围与节奏指标；首次对话可以为空",
        validation_alias=AliasChoices(
            "current_dynamics",
            "state_metrics",
            "dynamics",
        ),
        serialization_alias="current_dynamics",
    )

    persona_id: Optional[str] = Field(default=None, description="V2 匿名人物标识")
    session_id: Optional[str] = Field(default=None, description="V2 匿名模拟会话标识")

    simulation_state: Optional[SimulationState] = Field(
        default=None,
        description="上一轮返回的 V2 动态状态；首次对话为空",
    )

    @model_validator(mode="after")
    def validate_v2_context(self) -> "SessionMessageRequest":
        if self.simulation_state is None:
            return self

        if self.persona_id and self.simulation_state.persona_id != self.persona_id:
            raise ValueError("simulation_state.persona_id must match persona_id")

        if self.session_id and self.simulation_state.session_id != self.session_id:
            raise ValueError("simulation_state.session_id must match session_id")

        return self

    @property
    def user_goal(self) -> str:
        """
        临时兼容旧 Agent 代码中的 request.user_goal。
        后续建议统一改为 request.goal。
        """

        return self.goal


class SimulationReply(BaseModel):
    """
    SimulationAgent 的结构化输出。

    注意：
    这是 LLM structured output 的输出模型之一。
    字段不要设置默认值，否则部分 strict JSON Schema 服务会报错。
    """

    model_config = ConfigDict(extra="forbid")

    reply: str = Field(description="目标人物的自然语言回复")
    attitude: str = Field(description="目标人物对用户当前表达的态度")
    emotion: str = Field(description="目标人物当前情绪")
    perceived_user_tone: str = Field(description="目标人物感受到的用户语气")
    state_delta: StateDelta
    risk_flags: List[str] = Field(description="本轮沟通风险点；如果没有风险，返回空数组")


class SessionActionResponse(BaseModel):
    """
    V2 visible behavior result, including formal no-reply states.
    """

    model_config = ConfigDict(extra="forbid")

    action: ResponseAction
    text: str = Field(description="目标人物可见回复；不回复 Action 时为空字符串")
    status_text: str = Field(description="前端状态说明；普通回复时为空字符串")
    conversation_ended: bool = False


class SessionMessageResponse(BaseModel):
    """
    单轮模拟回复接口返回。

    updated_memory:
    - MemoryAgent 成功时返回新的会话记忆。
    - MemoryAgent 失败或尚未启用时可以为 None。
    - 前端可以先忽略该字段，不影响 target_message / simulation / updated_state 的展示。

    dynamics_update:
    - StateAgent 成功时返回完整的动态指标更新结果。
    - 包括 dynamics_delta、updated_dynamics 和 control_suggestions。
    - 如果 StateAgent 失败，可以为 None。

    state_metrics:
    - dynamics_update.updated_dynamics 的便捷展开字段。
    - 前端下一轮可以把它作为 current_dynamics 传回后端。
    """

    model_config = ConfigDict(extra="forbid")

    target_message: ChatMessage
    simulation: SimulationReply
    updated_state: RelationshipState

    response: Optional[SessionActionResponse] = Field(
        default=None,
        description="V2 行为响应；V1 为空并继续使用 target_message",
    )

    updated_memory: Optional[SessionMemory] = Field(
        default=None,
        description="更新后的当前会话短期记忆",
    )

    safety: Optional[SafetyCheckResponse] = Field(
        default=None,
        description="本轮安全检查结果；无风险或未执行时可以为空",
    )

    simulation_state: Optional[SimulationState] = Field(
        default=None,
        description="V2 动态状态；V1 响应为空",
    )

    evidence_meta: Optional[SessionEvidenceMeta] = Field(
        default=None,
        description="V2 本轮证据检索元数据；不包含原始聊天正文",
    )

    evaluation_meta: Optional[SessionEvaluationMeta] = Field(
        default=None,
        description="V2 一致性评估元数据；正常未触发回合标记 evaluated=false",
    )

    runtime_meta: Optional[SessionRuntimeMeta] = Field(
        default=None,
        description="V2 失败恢复元数据",
    )

    dynamics_update: Optional[ConversationDynamicsUpdate] = Field(
        default=None,
        description="本轮对话氛围与节奏指标的完整更新结果",
    )

    state_metrics: Optional[ConversationDynamics] = Field(
        default=None,
        description="本轮更新后的对话氛围与节奏指标；前端可在下一轮作为 current_dynamics 传回",
    )

    rhythm_label: Optional[RhythmLabel] = Field(
        default=None,
        description="当前对话节奏标签",
    )

    atmosphere_label: Optional[AtmosphereLabel] = Field(
        default=None,
        description="当前对话氛围标签",
    )

    recommended_next_move: Optional[RecommendedNextMove] = Field(
        default=None,
        description="下一轮建议动作",
    )

    control_suggestions: List[str] = Field(
        default_factory=list,
        description="下一轮控制氛围和节奏的建议",
    )

