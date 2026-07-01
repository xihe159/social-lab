# social-lab/backend/app/schemas/safety.py
# 2026/06/30

from __future__ import annotations

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ScenarioKey


SafetyContext = Literal["persona_create", "session_message", "report"]
SafetyRiskLevel = Literal["none", "low", "medium", "high"]
SafetyAction = Literal["allow", "warn", "block", "rewrite"]


class SafetyCheckRequest(BaseModel):
    """
    SafetyAgent 的内部输入。

    注意：
    这里故意使用 Any / List[Any]，避免 safety.py 与 session.py、persona.py、memory.py
    形成循环导入。SafetyAgent 只需要读取内容并判断风险，不需要强类型依赖。
    """

    model_config = ConfigDict(extra="forbid")

    context: SafetyContext = Field(description="安全检查发生的业务上下文")
    scenario: ScenarioKey
    goal: str = Field(description="用户沟通目标")
    outcome: str = Field(default="", description="用户期待结果")

    role: str = Field(default="", description="目标人物身份，仅 persona_create 场景使用")
    relation: str = Field(default="", description="双方关系，仅 persona_create 场景使用")
    habit: str = Field(default="", description="目标人物习惯或背景，仅 persona_create 场景使用")
    chatLog: str = Field(default="", description="外部导入聊天记录，仅 persona_create 场景使用")

    persona: Optional[Any] = Field(default=None, description="目标人物画像")
    messages: List[Any] = Field(default_factory=list, description="已有对话历史")
    user_message: str = Field(default="", description="用户本轮最新输入")
    current_memory: Optional[Any] = Field(default=None, description="当前会话短期记忆")


class SafetyCheckResponse(BaseModel):
    """
    SafetyAgent 的结构化输出。

    注意：
    这是 LLM structured output 使用的模型，因此字段不要设置默认值。
    """

    model_config = ConfigDict(extra="forbid")

    allowed: bool = Field(description="是否允许继续执行后续 Agent")
    risk_level: SafetyRiskLevel = Field(description="风险等级")
    action: SafetyAction = Field(description="建议执行动作")
    risk_types: List[str] = Field(description="风险类型列表，例如 privacy/manipulation/harassment/high_stakes/self_harm/violence")
    user_notice: str = Field(description="需要展示给用户的安全提示；无风险时返回空字符串")
    safe_rewrite_hint: str = Field(description="将用户请求改写成安全练习目标的建议；无风险时返回空字符串")
    should_redact: bool = Field(description="是否建议对输入中的隐私信息做脱敏")
    redacted_fields: List[str] = Field(description="建议脱敏的字段或内容类型；无则返回空数组")
