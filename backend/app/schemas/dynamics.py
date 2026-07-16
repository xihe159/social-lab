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
        description=(
            "当前节奏健康度。越高表示推进速度越合适。"
            "注意：它不是推进速度本身，过快和停滞都会降低该分数。"
        ),
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


class ConversationDynamicsDelta(BaseModel):
    """
    本轮对话对动态指标造成的变化量。

    注意：
    - 正数表示该指标上升；
    - 负数表示该指标下降；
    - pressure_level 上升通常是负面信号；
    - pace_score 上升表示节奏更健康，不表示推进更快；
    - 单轮变化应保持保守，避免一轮话导致状态剧烈波动。
    """

    model_config = ConfigDict(extra="forbid")

    atmosphere_score: int = Field(ge=-15, le=15)
    pace_score: int = Field(ge=-15, le=15)
    pressure_level: int = Field(ge=-15, le=15)
    clarity_score: int = Field(ge=-15, le=15)
    responsiveness_score: int = Field(ge=-15, le=15)
    progress_score: int = Field(ge=-15, le=15)
    repairability_score: int = Field(ge=-15, le=15)
    boundary_score: int = Field(ge=-15, le=15)


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


class ConversationDynamicsTrend(BaseModel):
    """
    多轮对话后的趋势总结。

    主要给 ReportAgent / AnalysisAgent 使用，
    用来解释为什么成功率上升或下降。
    """

    model_config = ConfigDict(extra="forbid")

    start_turn: int = Field(ge=1, description="趋势起始轮次")
    end_turn: int = Field(ge=1, description="趋势结束轮次")

    atmosphere_trend: Literal["improving", "stable", "worsening"] = Field(
        description="对话氛围趋势"
    )
    pace_trend: Literal["improving", "stable", "worsening"] = Field(
        description="节奏健康度趋势"
    )
    pressure_trend: Literal["increasing", "stable", "decreasing"] = Field(
        description="压力水平趋势"
    )
    clarity_trend: Literal["improving", "stable", "worsening"] = Field(
        description="表达清晰度趋势"
    )
    progress_trend: Literal["improving", "stable", "worsening"] = Field(
        description="目标推进趋势"
    )

    main_dynamic_issue: str = Field(description="当前最主要的氛围或节奏问题")
    report_summary: str = Field(description="写入复盘报告的趋势摘要")


class ConversationDynamicsUpdate(BaseModel):
    """
    StateAgent 对本轮动态指标的完整输出。

    这个模型后续可以嵌入 StateEvaluationResponse 中。
    """

    model_config = ConfigDict(extra="forbid")

    dynamics_delta: ConversationDynamicsDelta
    updated_dynamics: ConversationDynamics
    control_suggestions: list[str] = Field(
        default_factory=list,
        description="下一轮控制对话氛围和节奏的建议",
    )

