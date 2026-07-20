from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import RelationshipState, ScenarioKey
from app.schemas.dynamics import ConversationDynamics, ConversationDynamicsUpdate
from app.schemas.evaluation import SessionEvaluationMeta
from app.schemas.evidence_retrieval import SessionEvidenceMeta
from app.schemas.memory import SessionMemory
from app.schemas.persona import Persona
from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.safety import SafetyCheckResponse
from app.schemas.simulation_adjustment import SessionAdjustmentMeta
from app.schemas.simulation_decision import ResponseAction
from app.schemas.simulation_state import SimulationState
from app.schemas.simulation_turn import SessionRuntimeMeta
from app.schemas.strategy import TargetResponsePolicy


class ChatMessage(BaseModel):
    """
    一条模拟对话消息。

    role:
    - user: 真实用户
    - target: 被模拟的目标人物
    - system: 系统状态消息
    """

    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "target", "system"] = Field(
        description="消息发送者角色"
    )
    content: str = Field(description="消息正文")


class StateDelta(BaseModel):
    """
    单轮对话导致的关系状态变化。

    注意：
    - 这里是增量，不是最终状态；
    - 取值范围故意限制较小，避免模型在单轮回复中大幅改变关系。
    """

    model_config = ConfigDict(extra="forbid")

    trust: int = Field(ge=-10, le=10, description="信任程度变化")
    respect: int = Field(ge=-10, le=10, description="尊重程度变化")
    familiarity: int = Field(ge=-10, le=10, description="熟悉程度变化")
    affinity: int = Field(ge=-10, le=10, description="亲近程度变化")
    authority: int = Field(
        ge=-10,
        le=10,
        description="权力距离或权威感变化",
    )
    emotional: int = Field(
        ge=-10,
        le=10,
        description="情绪稳定度变化，负数代表更紧张或更敏感",
    )


class SessionMessageRequest(BaseModel):
    """
    用户发送一条消息后，请求 SimulationAgent 生成目标人物回复。

    Dynamics 使用方式：
    - 首轮 current_dynamics 可以为空；
    - 后续轮次应将上一轮 dynamics_update.updated_dynamics 原样回传；
    - 后端据此形成连续的氛围、节奏和压力变化。
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
        description=(
            "上一轮 StateAgent 输出的 updated_dynamics。"
            "首次对话可以为空；后续轮次应原样回传。"
        ),
    )

    persona_id: Optional[str] = Field(
        default=None,
        description="V2 匿名人物标识",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="V2 匿名模拟会话标识",
    )
    simulation_state: Optional[SimulationState] = Field(
        default=None,
        description="上一轮返回的 V2 动态状态；首次对话为空",
    )
    response_policy: Optional[TargetResponsePolicy] = Field(
        default=None,
        description="可选的 Strategy V2 Policy；为空时由主链路内部生成",
    )

    @model_validator(mode="after")
    def validate_v2_context(self) -> "SessionMessageRequest":
        if self.simulation_state is None:
            return self

        if (
            self.persona_id
            and self.simulation_state.persona_id != self.persona_id
        ):
            raise ValueError(
                "simulation_state.persona_id must match persona_id"
            )

        if (
            self.session_id
            and self.simulation_state.session_id != self.session_id
        ):
            raise ValueError(
                "simulation_state.session_id must match session_id"
            )

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
    字段不要设置默认值，否则部分 strict JSON Schema 服务会要求报错。
    """

    model_config = ConfigDict(extra="forbid")

    reply: str = Field(description="目标人物的自然语言回复")
    attitude: str = Field(description="目标人物对用户当前表达的态度")
    emotion: str = Field(description="目标人物当前情绪")
    perceived_user_tone: str = Field(description="目标人物感受到的用户语气")
    state_delta: StateDelta
    risk_flags: List[str] = Field(
        description="本轮沟通风险点；如果没有风险，返回空数组"
    )


class SessionActionResponse(BaseModel):
    """V2 可见行为结果，包括正式的不回复状态。"""

    model_config = ConfigDict(extra="forbid")

    action: ResponseAction
    text: str = Field(description="目标人物可见回复；不回复 Action 时为空字符串")
    status_text: str = Field(description="前端状态说明；普通回复时为空字符串")
    conversation_ended: bool = False


class SessionStrategyMeta(BaseModel):
    """向内部 V2 流程暴露的安全 Strategy Policy 元数据。"""

    model_config = ConfigDict(extra="forbid")

    policy_id: str
    strategy_action: str
    simulation_action: ResponseAction
    confidence: float = Field(ge=0.0, le=1.0)
    persona_evidence_refs: List[str] = Field(default_factory=list)
    memory_evidence_refs: List[str] = Field(default_factory=list)
    prompt_version: str
    fallback_used: bool = False


class SessionMessageResponse(BaseModel):
    """
    单轮模拟回复接口返回。

    updated_memory:
    - MemoryAgent 成功时返回新的会话记忆；
    - MemoryAgent 失败或尚未启用时可以为 None。

    dynamics_update:
    - V1 与 V2 均由 StateAgent 生成；
    - V2 的关系状态仍由 SimulationAgent V2 决策链控制。
    """

    model_config = ConfigDict(extra="forbid")

    target_message: ChatMessage
    simulation: SimulationReply
    updated_state: RelationshipState

    dynamics_update: Optional[ConversationDynamicsUpdate] = Field(
        default=None,
        description="本轮动态增量、更新后的动态状态及内部控制提示",
    )

    response: Optional[SessionActionResponse] = Field(
        default=None,
        description="V2 行为响应；V1 为空并继续使用 target_message",
    )
    strategy_meta: Optional[SessionStrategyMeta] = Field(
        default=None,
        description="V2 本轮唯一 Strategy Policy 元数据；V1 为空",
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
    adjustment_meta: Optional[SessionAdjustmentMeta] = Field(
        default=None,
        description="V2 会话级短期自适应元数据；不包含修正文本或 Persona 内容",
    )
    runtime_meta: Optional[SessionRuntimeMeta] = Field(
        default=None,
        description="V2 失败恢复元数据",
    )
