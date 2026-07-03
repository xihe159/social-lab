from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import RelationshipState, ScenarioKey
from app.schemas.persona import Persona
from app.schemas.session import ChatMessage, StateDelta


class StateEvaluateRequest(BaseModel):
    """
    StateAgent 的输入结构。

    用于评估“用户最新发言 + 目标人物回复”对关系状态造成的影响。
    该结构不直接暴露给前端，通常由 SessionOrchestrator 在后端内部构造。
    """

    model_config = ConfigDict(extra="forbid")

    scenario: ScenarioKey = Field(description="沟通场景：advisor / work / social")
    goal: str = Field(description="用户本次沟通目标")
    outcome: str = Field(description="用户期待的理想结果")
    persona: Persona = Field(description="当前目标人物画像")
    messages: List[ChatMessage] = Field(description="本轮之前的历史对话")
    user_message: str = Field(description="用户最新发言")
    target_reply: str = Field(description="SimulationAgent 生成的目标人物回复")
    current_state: RelationshipState = Field(description="本轮发言前的关系状态")
    simulation_attitude: str = Field(description="SimulationAgent 判断的目标人物态度")
    simulation_emotion: str = Field(description="SimulationAgent 判断的目标人物情绪")
    perceived_user_tone: str = Field(description="目标人物感受到的用户语气")


class StateEvaluationResponse(BaseModel):
    """
    StateAgent 的结构化输出。

    注意：这是 LLM structured output 的输出模型。
    为了满足 strict JSON Schema，字段不要设置默认值。
    如果没有风险或信号，LLM 应返回空数组，而不是省略字段。
    """

    model_config = ConfigDict(extra="forbid")

    state_delta: StateDelta
    state_reason: str = Field(description="关系状态变化的主要原因")
    positive_signals: List[str] = Field(description="用户本轮表达中的积极信号；没有则返回空数组")
    negative_signals: List[str] = Field(description="用户本轮表达中的消极信号；没有则返回空数组")
    risk_flags: List[str] = Field(description="本轮沟通风险；没有明显风险则返回空数组")
