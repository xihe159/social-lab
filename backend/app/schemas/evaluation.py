# social-lab/backend/app/schemas/evaluation.py
# 2026/07/01
#
# 新增内容：
# 1. 定义 EvaluationAgent 的请求体 EvaluationRequest
# 2. 定义单项评分模型 EvaluationScoreItem
# 3. 定义 EvaluationAgent 的响应体 EvaluationResponse
#
# 设计说明：
# - EvaluationAgent 是“模拟质量评估器”，建议先作为独立接口使用。
# - 本文件故意不导入 app.schemas.session / app.schemas.memory / app.schemas.safety，避免循环引用。
# - 对 persona、messages、memory、simulation 等复杂对象使用 Any 承接。
# - Response 是 LLM structured output，需要严格 ConfigDict(extra="forbid")。
# - 输出字段不要设置默认值，避免 strict JSON Schema 报 required/default 相关错误。

from __future__ import annotations

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ScenarioKey


EvaluationMode = Literal[
    "single_turn",
    "whole_session",
]


class EvaluationRequest(BaseModel):
    """
    EvaluationAgent 的请求体。

    mode:
    - single_turn: 评估最近一轮模拟回复质量
    - whole_session: 评估整段模拟会话质量

    注意：为避免循环引用，本模型不直接导入 ChatMessage、SessionMemory、SafetyCheckResponse 等类型。
    """

    model_config = ConfigDict(extra="forbid")

    mode: EvaluationMode = Field(description="评估模式：single_turn 或 whole_session")
    scenario: ScenarioKey
    goal: str = Field(description="用户本次沟通目标")
    outcome: str = Field(default="", description="用户期待的理想结果")

    persona: Any = Field(description="当前目标人物画像")
    messages: List[Any] = Field(default_factory=list, description="已有对话历史")

    current_state: Optional[Any] = Field(
        default=None,
        description="当前关系状态；可以是 RelationshipState 的字典形式",
    )
    memory: Optional[Any] = Field(
        default=None,
        description="当前会话短期记忆；可以为空",
    )
    simulation: Optional[Any] = Field(
        default=None,
        description="最近一轮 SimulationAgent 的结构化输出；single_turn 模式建议提供",
    )
    target_message: Optional[Any] = Field(
        default=None,
        description="最近一轮目标人物回复；single_turn 模式建议提供",
    )
    safety: Optional[Any] = Field(
        default=None,
        description="最近一轮 SafetyAgent 输出；可以为空",
    )

    user_message: str = Field(
        default="",
        description="最近一轮用户发言；whole_session 模式可以为空",
    )
    target_reply: str = Field(
        default="",
        description="最近一轮目标人物回复文本；whole_session 模式可以为空",
    )


class EvaluationScoreItem(BaseModel):
    """
    单个评价维度的评分和解释。
    """

    model_config = ConfigDict(extra="forbid")

    score: int = Field(ge=0, le=100, description="该维度评分，0 到 100")
    reason: str = Field(description="该评分的原因")
    evidence: List[str] = Field(description="来自 persona、对话或状态的证据")


class EvaluationResponse(BaseModel):
    """
    EvaluationAgent 的结构化输出。

    注意：所有字段都不要设置默认值。
    """

    model_config = ConfigDict(extra="forbid")

    persona_consistency: EvaluationScoreItem = Field(description="目标人物回复是否符合 persona 画像")
    relationship_consistency: EvaluationScoreItem = Field(description="回复是否符合当前关系状态")
    role_play_quality: EvaluationScoreItem = Field(description="是否保持目标人物角色，没有跳出角色或变成教练")
    realism: EvaluationScoreItem = Field(description="对话是否像真实社交场景中的自然回应")
    responsiveness: EvaluationScoreItem = Field(description="目标人物是否准确回应用户本轮发言")
    safety_score: EvaluationScoreItem = Field(description="输出是否避免隐私、操控、骚扰、威胁等安全风险")
    pedagogical_value: EvaluationScoreItem = Field(description="本轮模拟对用户训练沟通能力是否有帮助")
    overall_score: int = Field(ge=0, le=100, description="综合质量评分")
    major_problems: List[str] = Field(description="主要问题列表")
    suggested_fixes: List[str] = Field(description="建议如何修复 SimulationAgent 或 prompt")
    debug_notes: List[str] = Field(description="面向开发者的调试备注")
