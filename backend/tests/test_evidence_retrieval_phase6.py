from __future__ import annotations

import unittest
import sys
import types
from unittest.mock import AsyncMock


llm_client_stub = types.ModuleType("app.llm.client")
llm_client_stub.generate_structured = AsyncMock()
sys.modules.setdefault("app.llm.client", llm_client_stub)

from app.agents.simulation.context_builder import SimulationContextBuilder
from app.schemas.simulation_state import (
    ConversationState,
    EmotionalState,
    RelationshipStateV2,
    SimulationState,
)
from app.services.chat_record_analyzer import ChatRecordAnalyzer
from app.services.evidence_retriever import EvidenceRetriever
from app.services.evidence_store import EvidenceStore, EpisodeStore, PersonaEvidenceRepository


CHAT_LOG = """2026-06-01 09:00 我：老师，材料来不及准备，能否延期一天？
2026-06-01 09:05 导师：具体还缺什么？今天先把已有材料发我。
2026-06-05 10:00 我：下周会议改到周三可以吗？
2026-06-05 10:03 导师：可以，你提前通知其他人。
2026-06-10 11:00 我：上次是我的问题，我会负责把文件补齐。
2026-06-10 11:10 导师：好的，补齐后发我确认。
2026-06-15 14:00 我：麻烦您帮我看一下新的研究方向。
2026-06-15 14:05 导师：先写一页说明，把问题和方法列清楚。"""


def state() -> SimulationState:
    return SimulationState(
        session_id="session_phase6",
        persona_id="persona_phase6",
        relationship_state=RelationshipStateV2(
            patience=0.3,
            willingness_to_engage=0.6,
        ),
        emotional_state=EmotionalState(irritation=0.35),
        conversation_state=ConversationState(conflict_level=0.2),
    )


def repository() -> PersonaEvidenceRepository:
    analysis = ChatRecordAnalyzer().analyze(
        CHAT_LOG,
        target_role="导师",
        relation="师生关系",
    )
    assert analysis is not None
    result = PersonaEvidenceRepository(EpisodeStore(), EvidenceStore())
    result.register("persona_phase6", analysis)
    return result


class EvidenceStorePhase6Tests(unittest.TestCase):
    def test_episode_and_evidence_stores_return_independent_copies(self) -> None:
        repo = repository()
        first = repo.candidates("persona_phase6")
        first[0].episode.context = "changed_by_test"

        second = repo.candidates("persona_phase6")

        self.assertEqual(len(second), 4)
        self.assertNotEqual(second[0].episode.context, "changed_by_test")
        self.assertTrue(all(item.evidence.source_type == "REAL_CHAT" for item in second))


class EvidenceRetrieverPhase6Tests(unittest.TestCase):
    def test_repeated_delay_query_prioritizes_delay_episode(self) -> None:
        retriever = EvidenceRetriever(repository())

        result = retriever.retrieve(
            persona_id="persona_phase6",
            user_message="老师，这次可能还是需要延期，我会承担责任。",
            state=state(),
            top_k=4,
        )

        self.assertEqual(result.retrieval_mode, "keyword_behavior_top_k")
        self.assertTrue(result.items)
        self.assertEqual(result.items[0].episode_id, "episode_0001")
        self.assertIn("延期", result.items[0].content)
        self.assertIn("重复问题匹配", result.items[0].match_reasons)
        self.assertLessEqual(len(result.items), 4)

    def test_small_record_uses_persona_summary_instead_of_noisy_retrieval(self) -> None:
        repo = repository()
        short_repo = PersonaEvidenceRepository(EpisodeStore(), EvidenceStore())
        candidates = repo.candidates("persona_phase6")[:2]
        # Store interfaces remain separate; use a normal analysis and retain two entries.
        analysis = ChatRecordAnalyzer().analyze(CHAT_LOG, target_role="导师")
        assert analysis is not None
        analysis.episodes = analysis.episodes[:2]
        analysis.evidence = analysis.evidence[:2]
        short_repo.register("persona_phase6", analysis)

        result = EvidenceRetriever(short_repo).retrieve(
            persona_id="persona_phase6",
            user_message="能再延期吗？",
            state=state(),
        )

        self.assertEqual(len(candidates), 2)
        self.assertEqual(result.retrieval_mode, "persona_summary")
        self.assertEqual(result.items, [])

    def test_context_builder_separates_decision_and_linguistic_evidence(self) -> None:
        builder = SimulationContextBuilder(EvidenceRetriever(repository()))

        context = builder.build_evidence_context(
            persona_id="persona_phase6",
            user_message="材料又要延期一天。",
            state=state(),
        )

        self.assertTrue(context.decision_evidence)
        self.assertIn("REAL_CHAT", context.decision_evidence[0])
        self.assertTrue(context.linguistic_evidence)
        self.assertTrue(all("我：" not in item for item in context.linguistic_evidence))


if __name__ == "__main__":
    unittest.main()
