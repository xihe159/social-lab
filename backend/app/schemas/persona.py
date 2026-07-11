from typing import Literal, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import ScenarioKey, RelationshipState


class Persona(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="人物画像标题，例如：严格但愿意帮忙的导师画像")
    style: str = Field(description="沟通风格，例如：理性型、结果导向、情绪敏感型")
    speed: str = Field(description="回复速度，例如：偏快、正常、偏慢")
    focus: str = Field(description="对方最关注什么")
    risk: str = Field(description="沟通中最容易触发风险的点")
    strategy: str = Field(description="推荐沟通策略")
    state: RelationshipState


class PersonaEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["goal", "outcome", "role", "relation", "habit", "chatLog"]
    quote: str
    inference: str


class PersonaCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: ScenarioKey
    goal: str
    outcome: str
    role: str
    relation: str
    habit: str
    chatLog: str = ""


class PersonaCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    persona: Persona
    opening_message: str = Field(description="模拟对象第一句开场白")
    communication_rules: List[str] = Field(description="后续 Target Agent 对话时需要遵守的角色规则")
    evidence: List[PersonaEvidence] = Field(description="画像依据，必须来自用户输入")
    assumptions: List[str] = Field(description="LLM 无法确定但合理假设的内容")
    confidence: float = Field(ge=0, le=1, description="画像可信度")
    persona_id: Optional[str] = None
    saved: bool = False
