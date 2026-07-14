from __future__ import annotations

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ScenarioKey


MemoryCategory = Literal[
    "user_dialogue_pattern",
    "target_sensitive_point",
    "focus_issue",
    "key_info_repetition_risk",
    "resolved_point",
    "important_event",
]

MemoryConfidence = Literal["low", "medium", "high"]
MemoryStatus = Literal["active", "resolved", "forgotten"]


class MemoryEvidence(BaseModel):
    """
    记忆证据。

    目的：
    - 让后续报告能引用“第几轮、谁说了什么”；
    - 避免 Memory 变成没有依据的泛泛总结。
    """

    model_config = ConfigDict(extra="forbid")

    turn_index: int = Field(ge=1, description="证据来自第几轮")
    role: Literal["user", "target", "system"] = Field(description="证据来源角色")
    quote: str = Field(description="相关原话或简短证据")


class MemoryItem(BaseModel):
    """
    结构化记忆单元。

    记忆对象包括：
    - 用户对话模式；
    - 目标人物敏感点；
    - 当前对话聚焦问题；
    - 关键信息重复风险；
    - 已解决问题；
    - 重要事件。
    """

    model_config = ConfigDict(extra="forbid")

    memory_id: str = Field(description="记忆唯一 ID")
    category: MemoryCategory = Field(description="记忆类型")
    content: str = Field(description="记忆内容")
    importance: int = Field(ge=1, le=5, description="重要程度")
    confidence: MemoryConfidence = Field(description="置信度")
    status: MemoryStatus = Field(default="active", description="记忆状态")

    evidence: List[MemoryEvidence] = Field(
        default_factory=list,
        description="支持这条记忆的证据",
    )

    tags: List[str] = Field(
        default_factory=list,
        description="用于 Search 的标签",
    )

    first_seen_turn: int = Field(default=1, ge=1, description="首次出现轮次")
    last_seen_turn: int = Field(default=1, ge=1, description="最近出现轮次")
    seen_count: int = Field(default=1, ge=1, description="出现次数")


class SessionMemory(BaseModel):
    """
    当前一次模拟会话的短期记忆。

    注意：
    - 这是 session-level memory；
    - 不是长期用户记忆；
    - 不应该保存真实人物的敏感隐私；
    - 不应该把模拟推断说成现实事实。
    """

    model_config = ConfigDict(extra="forbid")

    # ===== 兼容旧版字段 =====
    conversation_summary: str = Field(description="当前对话摘要")
    user_strategy_pattern: List[str] = Field(description="用户当前表现出的表达模式")
    target_sensitive_points: List[str] = Field(description="目标人物当前敏感点或关注点")
    resolved_points: List[str] = Field(description="已经解决或已经说明清楚的问题")
    unresolved_points: List[str] = Field(description="仍未解决或仍需补充的问题")
    important_events: List[str] = Field(description="本次会话中的重要事件")
    next_suggested_focus: str = Field(description="下一轮沟通最应该关注的重点")

    # ===== 新版结构化字段 =====
    memory_version: str = Field(default="v2", description="Memory schema 版本")
    memory_items: List[MemoryItem] = Field(
        default_factory=list,
        description="结构化记忆单元",
    )
    active_focus_issues: List[str] = Field(
        default_factory=list,
        description="当前最需要处理的聚焦问题",
    )
    key_info_repetition_risks: List[str] = Field(
        default_factory=list,
        description="关键信息重复、遗漏或反复解释失败的风险",
    )
    forgotten_items: List[str] = Field(
        default_factory=list,
        description="被 forget 机制移除或降权的记忆摘要",
    )
    last_turn_index: int = Field(default=0, ge=0, description="Memory 已处理到的轮次")


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
    MemoryAgent 的输出。

    注意：
    第一阶段 MemoryAgent 内部会用 MemoryExtractor 生成候选项，
    再由 MemoryManager 规则化合并成这个响应。
    """

    model_config = ConfigDict(extra="forbid")

    memory: SessionMemory
    memory_reason: str = Field(description="本轮为什么这样更新会话记忆")
    new_facts: List[str] = Field(description="本轮新增的重要事实或关键信息")
    next_focus: str = Field(description="下一轮沟通建议关注点")