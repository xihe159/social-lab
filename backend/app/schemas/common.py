from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


ScenarioKey = Literal["advisor", "work", "social"]


class RelationshipState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trust: int = Field(ge=0, le=100, description="信任程度")
    respect: int = Field(ge=0, le=100, description="尊重程度")
    familiarity: int = Field(ge=0, le=100, description="熟悉程度")
    affinity: int = Field(ge=0, le=100, description="亲近程度")
    authority: int = Field(ge=0, le=100, description="权力距离或权威强度")
    emotional: int = Field(ge=-100, le=100, description="情绪稳定度，负数代表紧张或敏感")