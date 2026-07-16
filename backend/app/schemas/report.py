from __future__ import annotations

from typing import List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.schemas.common import ScenarioKey
from app.schemas.dynamics import (
    AtmosphereLabel,
    ConversationDynamics,
    RecommendedNextMove,
    RhythmLabel,
)
from app.schemas.persona import Persona
from app.schemas.session import ChatMessage


class ReportStateTimelineItem(BaseModel):
    """
    报告生成时使用的单轮对话动态指标快照。

    由前端在每轮 /api/session/message 返回后保存，
    最后调用 /api/session/report 时一并传入。

    作用：
    - 帮助 ReportAgent 分析对话氛围趋势；
    - 帮助 PredictionAgent 解释成功率变化；
    - 帮助 AnalysisAgent 找出节奏、压力、防御感等问题；
    - 帮助 RewriteAgent 生成更符合当前状态的下一步话术。
    """

    model_config = ConfigDict(extra="forbid")

    turn_index: int = Field(ge=1, description="第几轮对话")

    metrics: ConversationDynamics = Field(
        description="该轮对话后的氛围与节奏指标",
    )

    rhythm_label: Optional[RhythmLabel] = Field(
        default=None,
        description="该轮对话节奏标签",
    )

    atmosphere_label: Optional[AtmosphereLabel] = Field(
        default=None,
        description="该轮对话氛围标签",
    )

    recommended_next_move: Optional[RecommendedNextMove] = Field(
        default=None,
        description="该轮之后建议的下一步动作",
    )

    control_suggestions: List[str] = Field(
        default_factory=list,
        description="该轮之后控制氛围和节奏的建议",
    )

    user_message: str = Field(description="该轮用户发言")
    target_reply: str = Field(description="该轮目标人物回复")


class ReportRequest(BaseModel):
    """
    复盘报告请求。

    state_timeline:
    - 可选字段；
    - 旧前端不传也可以正常生成报告；
    - 新前端传入后，报告可以分析多轮对话的氛围、节奏、压力、清晰度和推进趋势。
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scenario: ScenarioKey

    goal: str = Field(
        description="用户想通过本次沟通达成的目标",
        validation_alias=AliasChoices("goal", "user_goal"),
        serialization_alias="goal",
    )

    outcome: str = Field(
        default="",
        description="用户期待的理想结果",
    )

    persona: Persona = Field(description="目标人物画像")

    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="完整模拟对话历史",
    )

    state_timeline: Optional[List[ReportStateTimelineItem]] = Field(
        default=None,
        description="每轮对话后的氛围与节奏动态指标，用于报告分析趋势",
    )

    @property
    def user_goal(self) -> str:
        """
        兼容旧代码中的 request.user_goal。
        后续建议统一使用 request.goal。
        """

        return self.goal


class ReportResponse(BaseModel):
    """
    复盘报告响应。

    注意：
    当前仍保持旧前端兼容结构。
    新增的 dynamics 分析暂时可以被写入：
    - likely_outcome
    - problems
    - key_risks
    - next_step_advice

    后续如果前端报告页升级，可以再新增：
    - main_influence_factors
    - dynamics_summary
    - turn_diagnostics
    - rewrite_pack
    """

    model_config = ConfigDict(extra="forbid")

    success_probability: int = Field(
        ge=0,
        le=100,
        description="模拟条件下的沟通目标成功概率",
    )

    likely_outcome: str = Field(
        description="基于当前模拟对话和动态指标推断的可能结果",
    )

    strengths: List[str] = Field(
        description="用户本次沟通中的优点",
    )

    problems: List[str] = Field(
        description="用户本次沟通中的主要问题",
    )

    key_risks: List[str] = Field(
        description="关键风险点",
    )

    suggested_rewrite: str = Field(
        description="推荐改写话术",
    )

    next_step_advice: str = Field(
        description="下一步沟通建议",
    )