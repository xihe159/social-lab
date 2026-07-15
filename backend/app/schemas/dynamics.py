from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RhythmLabel = Literal[
    "too_fast",
    "slightly_fast",
    "balanced",
    "slightly_slow",
    "stalled",
]

AtmosphereLabel = Literal[
    "safe",
    "warm",
    "neutral",
    "tense",
    "defensive",
    "blocked",
]

RecommendedNextMove = Literal[
    "advance",
    "clarify",
    "slow_down",
    "repair",
    "set_boundary",
    "pause",
]


class ConversationDynamics(BaseModel):
    """
    单轮对话后的动态指标。

    注意：
    这些指标只描述当前模拟会话中的对话状态，
    不是对真实人物或真实关系的绝对判断。
    """

    model_config = ConfigDict(extra="forbid")

    atmosphere_score: int = Field(
        ge=0,
        le=100,
        description="当前对话氛围分。越高表示越安全、开放、可继续沟通。",
    )
    pace_score: int = Field(
        ge=0,
        le=100,
        description="当前对话节奏分。越高表示推进速度越合适。",
    )
    pressure_level: int = Field(
        ge=0,
        le=100,
        description="当前压力水平。越高表示对方越可能感到被催促、被要求或被迫表态。",
    )
    clarity_score: int = Field(
        ge=0,
        le=100,
        description="用户本轮表达清晰度。越高表示背景、请求、时间、方案越具体。",
    )
    responsiveness_score: int = Field(
        ge=0,
        le=100,
        description="用户回应目标人物顾虑的程度。越高表示越能接住对方反馈。",
    )
    progress_score: int = Field(
        ge=0,
        le=100,
        description="沟通目标推进度。越高表示本轮更接近用户目标。",
    )
    repairability_score: int = Field(
        ge=0,
        le=100,
        description="后续修复空间。越高表示仍然容易继续沟通或修复关系。",
    )
    boundary_score: int = Field(
        ge=0,
        le=100,
        description="边界健康度。越高表示表达既有边界又不过度施压。",
    )

    rhythm_label: RhythmLabel = Field(description="当前对话节奏标签")
    atmosphere_label: AtmosphereLabel = Field(description="当前对话氛围标签")
    recommended_next_move: RecommendedNextMove = Field(description="下一轮建议动作")
    dynamics_reason: str = Field(description="这些动态指标的主要判断依据")


class ConversationDynamicsSnapshot(BaseModel):
    """
    写入 Memory 的动态指标快照。

    用于后续报告生成“对话氛围与节奏趋势”。
    """

    model_config = ConfigDict(extra="forbid")

    turn_index: int = Field(ge=1, description="第几轮对话")
    atmosphere_score: int = Field(ge=0, le=100)
    pace_score: int = Field(ge=0, le=100)
    pressure_level: int = Field(ge=0, le=100)
    clarity_score: int = Field(ge=0, le=100)
    responsiveness_score: int = Field(ge=0, le=100)
    progress_score: int = Field(ge=0, le=100)
    repairability_score: int = Field(ge=0, le=100)
    boundary_score: int = Field(ge=0, le=100)

    rhythm_label: RhythmLabel
    atmosphere_label: AtmosphereLabel
    recommended_next_move: RecommendedNextMove
    reason: str


