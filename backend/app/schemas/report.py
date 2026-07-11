from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import ScenarioKey
from app.schemas.persona import Persona
from app.schemas.session import ChatMessage


class ReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: ScenarioKey
    goal: str
    outcome: str = ""
    persona: Persona
    messages: List[ChatMessage]
    persona_id: Optional[str] = None
    session_id: Optional[str] = None

    @property
    def user_goal(self) -> str:
        return self.goal


class ReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success_probability: int = Field(ge=0, le=100, description="模拟成功概率，0 到 100")
    likely_outcome: str = Field(description="基于模拟的可能结果")
    strengths: List[str] = Field(description="用户表达中的优点")
    problems: List[str] = Field(description="用户表达中的问题")
    key_risks: List[str] = Field(description="主要沟通风险")
    suggested_rewrite: str = Field(description="推荐改写后的完整话术")
    next_step_advice: str = Field(description="下一步沟通建议")
    report_id: Optional[str] = None
    saved: bool = False
