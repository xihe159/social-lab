from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ScenarioKey


class SessionMemory(BaseModel):
    """
    当前一次模拟会话的短期记忆。

    注意：
    这是 session-level memory，不是长期用户记忆。
    """

    model_config = ConfigDict(extra="forbid")

    conversation_summary: str = Field(description="当前对话摘要")
    user_strategy_pattern: List[str] = Field(description="用户当前表现出的表达模式")
    target_sensitive_points: List[str] = Field(description="目标人物当前敏感点或关注点")
    resolved_points: List[str] = Field(description="已经解决或已经说明清楚的问题")
    unresolved_points: List[str] = Field(description="仍未解决或仍需补充的问题")
    important_events: List[str] = Field(description="本次会话中的重要事件")
    next_suggested_focus: str = Field(description="下一轮沟通最应该关注的重点")


class MemoryUpdateRequest(BaseModel):
    """
    MemoryAgent 的内部输入。

    这里故意不导入 ChatMessage / StateDelta，
    避免 memory.py 与 session.py 互相导入导致循环依赖。
    """

    model_config = ConfigDict(extra="forbid")

    scenario: ScenarioKey
    goal: str
    outcome: str = ""
    persona: Any
    messages: List[Any] = Field(default_factory=list)
    user_message: str
    target_reply: str
    state_delta: Any
    risk_flags: List[str]
    current_memory: Optional[SessionMemory] = None


class MemoryUpdateResponse(BaseModel):
    """
    MemoryAgent 的结构化输出。

    注意：
    为了兼容 strict structured output，输出字段不要设置默认值。
    """

    model_config = ConfigDict(extra="forbid")

    memory: SessionMemory
    memory_reason: str = Field(description="本轮为什么这样更新会话记忆")
    new_facts: List[str] = Field(description="本轮新增的重要事实或关键信息")
    next_focus: str = Field(description="下一轮沟通建议关注点")
