from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from threading import RLock

from app.schemas.chat_record import ChatEvidence, ChatRecordAnalysis, ConversationEpisode


class EpisodeStore:
    """Bounded in-memory Episode Store; persistence can replace this interface later."""

    def __init__(self, *, max_personas: int = 256) -> None:
        self.max_personas = max(1, max_personas)
        self._items: OrderedDict[str, tuple[ConversationEpisode, ...]] = OrderedDict()
        self._lock = RLock()

    def put(self, persona_id: str, episodes: list[ConversationEpisode]) -> None:
        with self._lock:
            self._items[persona_id] = tuple(item.model_copy(deep=True) for item in episodes)
            self._items.move_to_end(persona_id)
            self._trim()

    def get(self, persona_id: str) -> list[ConversationEpisode]:
        with self._lock:
            items = self._items.get(persona_id, ())
            if persona_id in self._items:
                self._items.move_to_end(persona_id)
            return [item.model_copy(deep=True) for item in items]

    def clear(self, persona_id: str | None = None) -> None:
        with self._lock:
            if persona_id is None:
                self._items.clear()
            else:
                self._items.pop(persona_id, None)

    def _trim(self) -> None:
        while len(self._items) > self.max_personas:
            self._items.popitem(last=False)


class EvidenceStore:
    """Bounded in-memory REAL_CHAT Evidence Store."""

    def __init__(self, *, max_personas: int = 256) -> None:
        self.max_personas = max(1, max_personas)
        self._items: OrderedDict[str, tuple[ChatEvidence, ...]] = OrderedDict()
        self._lock = RLock()

    def put(self, persona_id: str, evidence: list[ChatEvidence]) -> None:
        with self._lock:
            self._items[persona_id] = tuple(item.model_copy(deep=True) for item in evidence)
            self._items.move_to_end(persona_id)
            self._trim()

    def get(self, persona_id: str) -> list[ChatEvidence]:
        with self._lock:
            items = self._items.get(persona_id, ())
            if persona_id in self._items:
                self._items.move_to_end(persona_id)
            return [item.model_copy(deep=True) for item in items]

    def clear(self, persona_id: str | None = None) -> None:
        with self._lock:
            if persona_id is None:
                self._items.clear()
            else:
                self._items.pop(persona_id, None)

    def _trim(self) -> None:
        while len(self._items) > self.max_personas:
            self._items.popitem(last=False)


@dataclass(frozen=True)
class StoredEvidenceCandidate:
    episode: ConversationEpisode
    evidence: ChatEvidence


class PersonaEvidenceRepository:
    """Coordinates Episode and Evidence stores without coupling retrieval to storage."""

    def __init__(
        self,
        episode_store: EpisodeStore | None = None,
        evidence_store: EvidenceStore | None = None,
    ) -> None:
        self.episodes = episode_store or EpisodeStore()
        self.evidence = evidence_store or EvidenceStore()

    def register(self, persona_id: str, analysis: ChatRecordAnalysis) -> None:
        self.episodes.put(persona_id, analysis.episodes)
        self.evidence.put(persona_id, analysis.evidence)

    def candidates(self, persona_id: str) -> list[StoredEvidenceCandidate]:
        episodes = self.episodes.get(persona_id)
        evidence = self.evidence.get(persona_id)
        evidence_by_suffix = {
            item.evidence_id.rsplit("_", 1)[-1]: item for item in evidence
        }
        candidates: list[StoredEvidenceCandidate] = []
        for episode in episodes:
            item = evidence_by_suffix.get(episode.episode_id.rsplit("_", 1)[-1])
            if item is not None:
                candidates.append(StoredEvidenceCandidate(episode=episode, evidence=item))
        return candidates

    def clear(self, persona_id: str | None = None) -> None:
        self.episodes.clear(persona_id)
        self.evidence.clear(persona_id)


persona_evidence_repository = PersonaEvidenceRepository()

