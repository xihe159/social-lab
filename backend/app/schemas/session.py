from typing import List, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.schemas.common import RelationshipState, ScenarioKey
from app.schemas.persona import Persona


class ChatMessage(BaseModel):
    """
    一条模拟对话消息。

    role:
    - user: 真实用户
    - target: 被模拟的目标人物
    """

    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "target"] = Field(description="消息发送者角色")
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
    emotional: int = Field(ge=-10, le=10, description="情绪稳定度变化，负数代表更紧张或更敏感")


class SessionMessageRequest(BaseModel):
    """
    用户发送一条消息后，请求 Target/Simulation Agent 生成目标人物回复。
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scenario: ScenarioKey
    goal: str = Field(
        description="用户想通过本次沟通达成的目标",
        validation_alias=AliasChoices("goal", "user_goal"),
        serialization_alias="goal",
    )
    outcome: str = Field(default="", description="用户期待的理想结果")
    persona: Persona
    messages: List[ChatMessage] = Field(default_factory=list, description="已有对话历史")
    user_message: str = Field(description="用户最新输入的消息")

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
    """

    model_config = ConfigDict(extra="forbid")

    reply: str = Field(description="目标人物的自然语言回复")
    attitude: str = Field(description="目标人物对用户当前表达的态度")
    emotion: str = Field(description="目标人物当前情绪")
    perceived_user_tone: str = Field(description="目标人物感受到的用户语气")
    state_delta: StateDelta
    risk_flags: List[str] = Field(description="本轮沟通风险点；如果没有风险，返回空数组")


class SessionMessageResponse(BaseModel):
    """
    单轮模拟回复接口返回。
    """

    model_config = ConfigDict(extra="forbid")

    target_message: ChatMessage
    simulation: SimulationReply
    updated_state: RelationshipState
