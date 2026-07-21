from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SentenceRewrite(BaseModel):
    """
    RewriteAgent 对低效或高风险句子的改写结果。

    改进意见只存在于本模型及 RewriteAgent 输出中，
    不进入 AnalysisAgent 的逐句拆解。
    """

    model_config = ConfigDict(extra="forbid")

    turn_index: int = Field(ge=1)
    sentence_index: int = Field(ge=1)
    original_text: str
    rewritten_text: str
    rewrite_reason: str
    expected_effect: str


class RewriteVariants(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minimal_edit: str
    warmer_version: str
    firmer_version: str


class RewriteResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggested_rewrite: str
    sentence_rewrites: list[SentenceRewrite]
    variants: RewriteVariants
    next_step_advice: str
    do_not_say: list[str]
