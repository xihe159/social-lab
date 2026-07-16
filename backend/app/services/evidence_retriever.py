from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.evidence_retrieval import (
    EvidenceRetrievalResult,
    RetrievalQuery,
    RetrievedEvidence,
)
from app.schemas.simulation_state import SimulationState
from app.services.evidence_store import (
    PersonaEvidenceRepository,
    StoredEvidenceCandidate,
    persona_evidence_repository,
)


_CONCEPTS: dict[str, tuple[str, ...]] = {
    "delay": ("延期", "延迟", "推迟", "晚交", "晚一天", "来不及", "截止", "deadline", "拖"),
    "request": ("请求", "麻烦", "能否", "能不能", "可以吗", "请您", "帮忙"),
    "responsibility": ("负责", "责任", "我的错", "我的问题", "承担", "补救", "补齐"),
    "apology": ("抱歉", "对不起", "不好意思", "sorry"),
    "materials": ("材料", "文件", "文档", "附件", "资料"),
    "urgency": ("尽快", "马上", "立刻", "紧急", "今天必须", "急"),
    "boundary": ("不要", "不能", "别再", "边界", "到此为止"),
    "confirmation": ("确认", "收到", "看到了", "回复", "答复"),
    "mistake": ("错误", "犯错", "我的问题", "失误", "再拖"),
    "explanation": ("因为", "原因", "解释", "所以"),
}
_BEHAVIOR_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("apologizes", _CONCEPTS["apology"]),
    ("takes_responsibility", _CONCEPTS["responsibility"]),
    ("explains_reason", _CONCEPTS["explanation"]),
    ("makes_request", _CONCEPTS["request"]),
    ("expresses_urgency", _CONCEPTS["urgency"]),
    ("repeats_issue", ("又", "还是", "再次", "再一次", "仍然")),
)
_STOP_BIGRAMS = {
    "这个", "那个", "可以", "我们", "你们", "他们", "一下", "现在", "已经", "还是",
}


@dataclass(frozen=True)
class _ScoredCandidate:
    candidate: StoredEvidenceCandidate
    score: float
    reasons: tuple[str, ...]


class EvidenceRetriever:
    """Phase 6 lightweight retrieval, designed to be replaceable by embeddings."""

    def __init__(
        self,
        repository: PersonaEvidenceRepository | None = None,
        *,
        min_episode_count: int = 3,
        min_score: float = 0.14,
    ) -> None:
        self.repository = repository or persona_evidence_repository
        self.min_episode_count = max(1, min_episode_count)
        self.min_score = max(0.0, min(1.0, min_score))

    def build_query(
        self,
        *,
        user_message: str,
        state: SimulationState,
    ) -> RetrievalQuery:
        text = user_message.strip().lower()
        concepts = self._concepts(text)
        ordered_concepts = sorted(
            concepts,
            key=lambda concept: self._first_alias_position(text, _CONCEPTS[concept]),
        )
        behaviors = [
            label for label, aliases in _BEHAVIOR_RULES if any(alias in text for alias in aliases)
        ]
        if "?" in text or "？" in text or text.endswith(("吗", "么")):
            behaviors.append("asks_question")

        conflict_signals: list[str] = []
        if state.conversation_state.conflict_level >= 0.45:
            conflict_signals.append("ongoing_conflict")
        if state.conversation_state.boundary_pressure >= 0.45:
            conflict_signals.append("boundary_pressure")
        if any(word in text for word in ("不满", "生气", "指责", "凭什么", "必须")):
            conflict_signals.append("explicit_conflict")

        state_signals: list[str] = []
        emotion = state.emotional_state
        relationship = state.relationship_state
        if emotion.irritation >= 0.4:
            state_signals.append("irritated")
        if emotion.defensiveness >= 0.4:
            state_signals.append("defensive")
        if relationship.patience <= 0.35:
            state_signals.append("low_patience")
        if relationship.willingness_to_engage <= 0.35:
            state_signals.append("low_engagement")

        keywords = sorted(concepts | self._bigrams(text))[:24]
        topic = ordered_concepts[0] if ordered_concepts else text[:80] or "general"
        return RetrievalQuery(
            current_topic=topic,
            keywords=keywords,
            user_behaviors=self._dedupe(behaviors),
            conflict_signals=self._dedupe(conflict_signals),
            state_signals=self._dedupe(state_signals),
        )

    def retrieve(
        self,
        *,
        persona_id: str,
        user_message: str,
        state: SimulationState,
        top_k: int = 4,
    ) -> EvidenceRetrievalResult:
        candidates = self.repository.candidates(persona_id)
        query = self.build_query(user_message=user_message, state=state)
        if len(candidates) < self.min_episode_count:
            return EvidenceRetrievalResult(
                query=query,
                total_candidates=len(candidates),
                retrieval_mode="persona_summary",
            )

        limit = max(3, min(5, int(top_k)))
        scored = [self._score(query, candidate, index, len(candidates)) for index, candidate in enumerate(candidates)]
        selected = sorted(scored, key=lambda item: (-item.score, item.candidate.episode.episode_id))
        selected = [item for item in selected if item.score >= self.min_score][:limit]

        return EvidenceRetrievalResult(
            query=query,
            items=[self._to_retrieved(item) for item in selected],
            total_candidates=len(candidates),
            retrieval_mode="keyword_behavior_top_k" if selected else "persona_summary",
        )

    def _score(
        self,
        query: RetrievalQuery,
        candidate: StoredEvidenceCandidate,
        index: int,
        total: int,
    ) -> _ScoredCandidate:
        episode = candidate.episode
        evidence = candidate.evidence
        document = " ".join(
            (
                evidence.content,
                " ".join(evidence.supports),
                " ".join(evidence.scope),
                " ".join(episode.user_behavior),
                " ".join(episode.target_response),
                episode.context,
                episode.outcome,
            )
        ).lower()
        query_concepts = {item for item in query.keywords if item in _CONCEPTS}
        document_concepts = self._concepts(document)
        concept_matches = query_concepts & document_concepts
        behavior_matches = set(query.user_behaviors) & set(episode.user_behavior)
        bigram_matches = (set(query.keywords) - set(_CONCEPTS)) & self._bigrams(document)

        reasons: list[str] = []
        score = 0.0
        if concept_matches:
            score += 0.45 * len(concept_matches) / max(1, len(query_concepts))
            reasons.append("主题匹配:" + "/".join(sorted(concept_matches)))
        if query.current_topic in document_concepts:
            score += 0.2
            reasons.append("当前主话题匹配:" + query.current_topic)
        if behavior_matches:
            score += 0.25 * len(behavior_matches) / max(1, len(query.user_behaviors))
            reasons.append("用户行为匹配:" + "/".join(sorted(behavior_matches)))
        if bigram_matches:
            score += min(0.16, len(bigram_matches) * 0.025)
            reasons.append("关键词匹配")

        response_labels = set(episode.target_response)
        if "boundary_pressure" in query.conflict_signals and "sets_boundary" in response_labels:
            score += 0.1
            reasons.append("边界压力匹配")
        if "low_patience" in query.state_signals and "brief_response" in response_labels:
            score += 0.08
            reasons.append("低耐心状态匹配")
        if "repeats_issue" in query.user_behaviors and (
            "mistake" in document_concepts or "delay" in document_concepts
        ):
            score += 0.12
            reasons.append("重复问题匹配")

        recency = (index + 1) / max(1, total)
        score += evidence.confidence * 0.04 + recency * 0.02
        return _ScoredCandidate(
            candidate=candidate,
            score=round(max(0.0, min(1.0, score)), 3),
            reasons=tuple(reasons[:5]),
        )

    @staticmethod
    def _to_retrieved(item: _ScoredCandidate) -> RetrievedEvidence:
        evidence = item.candidate.evidence
        episode = item.candidate.episode
        target_utterances = []
        for line in evidence.content.splitlines():
            if line.startswith(("对方：", "target:", "Target:")):
                target_utterances.append(line.split("：", 1)[-1] if "：" in line else line.split(":", 1)[-1])
        return RetrievedEvidence(
            evidence_id=evidence.evidence_id,
            episode_id=episode.episode_id,
            content=evidence.content[:600],
            target_utterances=[item.strip()[:240] for item in target_utterances if item.strip()][:4],
            relevance_score=item.score,
            match_reasons=list(item.reasons),
            scope=evidence.scope,
        )

    @staticmethod
    def _concepts(text: str) -> set[str]:
        lowered = text.lower()
        return {
            concept
            for concept, aliases in _CONCEPTS.items()
            if any(alias in lowered for alias in aliases)
        }

    @staticmethod
    def _bigrams(text: str) -> set[str]:
        sequences = re.findall(r"[\u4e00-\u9fff]{2,}", text)
        result: set[str] = set()
        for sequence in sequences:
            for index in range(len(sequence) - 1):
                value = sequence[index : index + 2]
                if value not in _STOP_BIGRAMS:
                    result.add(value)
        result.update(word.lower() for word in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text))
        return result

    @staticmethod
    def _dedupe(values: list[str]) -> list[str]:
        return list(dict.fromkeys(value for value in values if value))

    @staticmethod
    def _first_alias_position(text: str, aliases: tuple[str, ...]) -> int:
        positions = [text.find(alias) for alias in aliases if alias in text]
        return min(positions) if positions else len(text)
