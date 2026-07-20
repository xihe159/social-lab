from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import RelationshipState, ScenarioKey
from app.schemas.dynamics import ConversationDynamics, ConversationDynamicsUpdate
from app.schemas.persona import Persona
from app.schemas.session import ChatMessage, StateDelta


class StateEvaluateRequest(BaseModel):
    """
    StateAgent 输入：关系状态 + 当前对话动态。
    """

    model_config = ConfigDict(extra="forbid")

    scenario: ScenarioKey
    goal: str
    outcome: str
    persona: Persona
    messages: list[ChatMessage]
    user_message: str
    target_reply: str
    current_state: RelationshipState
    simulation_attitude: str
    simulation_emotion: str
    perceived_user_tone: str

    current_dynamics: ConversationDynamics | None = Field(
        default=None,
        description="本轮之前的对话动态；首次对话可为空",
    )


class StateEvaluationResponse(BaseModel):
    """
    LLM structured output。

    所有字段必须存在；没有信号或风险时返回空数组。
    """

    model_config = ConfigDict(extra="forbid")

    state_delta: StateDelta
    state_reason: str
    positive_signals: list[str]
    negative_signals: list[str]
    risk_flags: list[str]
    dynamics_update: ConversationDynamicsUpdate
