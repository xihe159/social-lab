# social-lab/backend/app/schemas/strategy.py
# 2026/07/01
#
# 修改内容：
# 1. 新增 StrategyCandidateMessage，匹配 strategy_agent.py 中的导入。
# 2. 保留 StrategyAlternativeMessage 作为兼容别名，避免旧 __init__.py 或旧代码导入失败。
# 3. 不导入 app.schemas.session / memory / safety，避免循环引用。
# 4. StrategyAdviceResponse 是 LLM structured output，输出字段不设置默认值。

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ScenarioKey


class StrategyAdviceRequest(BaseModel):
    """
    StrategyAgent 的请求体。

    用于根据当前场景、人物画像、对话历史、关系状态和会话记忆，
    生成下一轮沟通策略。
    """

    model_config = ConfigDict(extra="forbid")

    scenario: ScenarioKey
    goal: str = Field(description="用户本次沟通目标")
    outcome: str = Field(default="", description="用户期待的理想结果")

    persona: Any = Field(description="当前目标人物画像")
    messages: List[Any] = Field(default_factory=list, description="已有对话历史")

    current_state: Optional[Any] = Field(
        default=None,
        description="当前关系状态，可以是 RelationshipState 的字典形式",
    )
    memory: Optional[Any] = Field(
        default=None,
        description="当前会话短期记忆，可以为空",
    )

    last_user_message: str = Field(default="", description="最近一轮用户发言")
    last_target_reply: str = Field(default="", description="最近一轮目标人物回复")

    risk_flags: List[str] = Field(
        default_factory=list,
        description="最近一轮沟通风险点；请求体字段可以有默认值",
    )
    safety: Optional[Any] = Field(
        default=None,
        description="最近一轮 SafetyAgent 输出，可以为空",
    )


class StrategyCandidateMessage(BaseModel):
    """
    StrategyAgent 输出中的候选话术。

    注意：
    这是 LLM structured output 的嵌套模型，不要给字段设置默认值。
    """

    model_config = ConfigDict(extra="forbid")

    label: str = Field(description="候选话术标签，例如：稳妥版、直接版、缓和版")
    message: str = Field(description="候选话术内容")
    use_when: str = Field(description="适合在什么情况下使用")


# 兼容旧命名：
# 如果其他文件还在导入 StrategyAlternativeMessage，也不会报错。
StrategyAlternativeMessage = StrategyCandidateMessage


class StrategyAdviceResponse(BaseModel):
    """
    StrategyAgent 的结构化输出。

    注意：
    这是 LLM structured output，字段不要设置默认值。
    """

    model_config = ConfigDict(extra="forbid")

    next_move: str = Field(description="下一轮沟通的核心动作")
    recommended_tone: str = Field(description="推荐语气")
    avoid: List[str] = Field(description="下一轮应该避免的表达方式或风险动作")
    focus_points: List[str] = Field(description="下一轮应该补充或强调的重点")
    candidate_message: str = Field(description="最推荐的一句可直接使用的话术")
    alternative_messages: List[StrategyCandidateMessage] = Field(
        description="其他可选话术版本"
    )
    reason: str = Field(description="为什么推荐这个策略")
    risk_reminders: List[str] = Field(description="下一轮沟通需要注意的风险提醒")