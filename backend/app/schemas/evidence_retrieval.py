from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EvidenceRetrievalSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class RetrievalQuery(EvidenceRetrievalSchema):
    current_topic: str
    keywords: list[str] = Field(default_factory=list)
    user_behaviors: list[str] = Field(default_factory=list)
    conflict_signals: list[str] = Field(default_factory=list)
    state_signals: list[str] = Field(default_factory=list)


class RetrievedEvidence(EvidenceRetrievalSchema):
    evidence_id: str
    episode_id: str
    content: str
    target_utterances: list[str] = Field(default_factory=list)
    relevance_score: float = Field(ge=0.0, le=1.0)
    match_reasons: list[str] = Field(default_factory=list)
    scope: list[str] = Field(default_factory=list)

    def decision_context(self) -> str:
        reasons = "、".join(self.match_reasons) or "相关历史互动"
        return (
            f"[{self.episode_id} | REAL_CHAT | relevance={self.relevance_score:.3f} | {reasons}]\n"
            f"{self.content}"
        )

    def linguistic_context(self) -> str:
        return "\n".join(self.target_utterances)


class EvidenceRetrievalResult(EvidenceRetrievalSchema):
    query: RetrievalQuery
    items: list[RetrievedEvidence] = Field(default_factory=list)
    total_candidates: int = Field(default=0, ge=0)
    retrieval_mode: str = "persona_summary"


class SessionEvidenceMeta(EvidenceRetrievalSchema):
    retrieval_mode: str
    evidence_ids: list[str] = Field(default_factory=list)
    episode_ids: list[str] = Field(default_factory=list)
    relevance_scores: list[float] = Field(default_factory=list)

