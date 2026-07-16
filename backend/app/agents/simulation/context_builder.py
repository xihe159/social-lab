from __future__ import annotations

from dataclasses import dataclass

from app.schemas.evidence_retrieval import EvidenceRetrievalResult
from app.schemas.simulation_state import SimulationState
from app.services.evidence_retriever import EvidenceRetriever


@dataclass(frozen=True)
class SimulationEvidenceContext:
    retrieval: EvidenceRetrievalResult
    decision_evidence: tuple[str, ...]
    linguistic_evidence: tuple[str, ...]


class SimulationContextBuilder:
    """Build the high-signal evidence slice used by both V2 model calls."""

    def __init__(self, evidence_retriever: EvidenceRetriever | None = None) -> None:
        self.evidence_retriever = evidence_retriever or EvidenceRetriever()

    def build_evidence_context(
        self,
        *,
        persona_id: str,
        user_message: str,
        state: SimulationState,
        top_k: int = 4,
    ) -> SimulationEvidenceContext:
        retrieval = self.evidence_retriever.retrieve(
            persona_id=persona_id,
            user_message=user_message,
            state=state,
            top_k=top_k,
        )
        decision_evidence = tuple(item.decision_context() for item in retrieval.items)
        linguistic_evidence = tuple(
            value
            for item in retrieval.items
            if (value := item.linguistic_context())
        )
        return SimulationEvidenceContext(
            retrieval=retrieval,
            decision_evidence=decision_evidence,
            linguistic_evidence=linguistic_evidence,
        )

