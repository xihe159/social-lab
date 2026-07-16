from __future__ import annotations

import unittest
import sys
import types
from unittest.mock import AsyncMock


llm_client_stub = types.ModuleType("app.llm.client")
llm_client_stub.generate_structured = AsyncMock()
sys.modules.setdefault("app.llm.client", llm_client_stub)

from app.schemas.common import RelationshipState
from app.schemas.persona import Persona
from app.schemas.persona import PersonaCreateRequest, PersonaCreateResponse
from app.agents.persona_agent import PersonaAgent
from app.services.chat_record_analyzer import ChatRecordAnalyzer
from app.services.persona_v2_adapter import compile_legacy_persona


CHAT_LOG = """2026-07-01 09:00 我：老师，不好意思，我因为材料没齐，能否晚一天提交？
2026-07-01 09:01 我：我会先把已有的发过去。
2026-07-01 09:05 导师：具体还缺什么？今天先把已有的发我。
以下为新消息
2026-07-02 10:00 我：是我的问题，我会今天补齐，可以吗？
2026-07-02 10:03 导师：可以，但不要再拖了。
2026-07-03 11:00 我：我已经补齐了，麻烦您确认。
2026-07-03 11:10 导师：好的，我看到了。以后提前准备。"""


def legacy_persona() -> Persona:
    return Persona(
        title="重视材料完整度的导师",
        style="直接、结果导向",
        speed="偏慢",
        focus="材料完整度",
        risk="重复拖延",
        strategy="说明事实并承担责任",
        state=RelationshipState(
            trust=60,
            respect=70,
            familiarity=55,
            affinity=50,
            authority=80,
            emotional=10,
        ),
    )


class ChatRecordPreprocessorPhase5Tests(unittest.TestCase):
    def test_preprocessor_normalizes_roles_time_and_consecutive_messages(self) -> None:
        messages = ChatRecordAnalyzer().preprocess(CHAT_LOG, target_role="导师")

        self.assertEqual(messages[0].speaker, "user")
        self.assertEqual(messages[0].merged_count, 2)
        self.assertIn("已有的发过去", messages[0].text)
        self.assertEqual(messages[0].timestamp, "2026-07-01T09:00:00")
        self.assertTrue(all("以下为新消息" not in item.text for item in messages))
        self.assertTrue(all(item.original_text for item in messages))

    def test_unidentified_or_targetless_log_does_not_invent_analysis(self) -> None:
        analysis = ChatRecordAnalyzer().analyze("这里没有可识别的说话人")
        self.assertIsNone(analysis)


class ChatRecordPipelinePhase5Tests(unittest.TestCase):
    def test_pipeline_outputs_prd_acceptance_fields(self) -> None:
        analysis = ChatRecordAnalyzer().analyze(
            CHAT_LOG,
            target_role="导师",
            relation="师生关系",
        )

        self.assertIsNotNone(analysis)
        assert analysis is not None
        self.assertEqual(len(analysis.episodes), 3)
        self.assertGreaterEqual(len(analysis.behavior_patterns), 3)
        self.assertEqual(analysis.communication_style.average_reply_length, "short")
        self.assertGreaterEqual(analysis.relationship_characteristics.target_decision_power, 0.7)
        self.assertGreater(analysis.confidence, 0)
        self.assertTrue(analysis.evidence)
        self.assertTrue(all(item.source_type == "REAL_CHAT" for item in analysis.evidence))
        self.assertTrue(all(item.evidence_ids for item in analysis.behavior_patterns))

    def test_persona_compiler_uses_real_chat_style_patterns_and_confidence(self) -> None:
        analyzer = ChatRecordAnalyzer()
        analysis = analyzer.analyze(CHAT_LOG, target_role="导师", relation="师生关系")
        assert analysis is not None
        base = compile_legacy_persona(
            legacy_persona(),
            persona_id="persona_phase5",
            role="导师",
            relation="师生关系",
        )

        compiled = analyzer.compile_persona(base, analysis)

        self.assertEqual(compiled.communication_style, analysis.communication_style)
        self.assertEqual(compiled.behavior_patterns, analysis.behavior_patterns)
        self.assertTrue(compiled.evidence_summary.chat_record_available)
        self.assertEqual(compiled.evidence_summary.evidence_count, len(analysis.evidence))
        self.assertEqual(compiled.evidence_summary.overall_confidence, analysis.confidence)
        self.assertEqual(base.behavior_patterns, [])

    def test_persona_create_post_process_exposes_analysis_and_compiled_v2(self) -> None:
        request = PersonaCreateRequest(
            scenario="advisor",
            goal="请导师确认材料",
            outcome="获得确认",
            role="导师",
            relation="师生关系",
            habit="回复简短",
            chatLog=CHAT_LOG,
        )
        result = PersonaCreateResponse(
            persona=legacy_persona(),
            opening_message="请说。",
            communication_rules=[],
            evidence=[],
            assumptions=[],
            confidence=0.7,
        )

        processed = PersonaAgent().post_process(result=result, request=request)

        self.assertIsNotNone(processed.chat_analysis)
        self.assertIsNotNone(processed.persona_v2)
        assert processed.persona_v2 is not None
        self.assertGreaterEqual(len(processed.persona_v2.behavior_patterns), 3)
        self.assertTrue(processed.persona_v2.evidence_summary.chat_record_available)


if __name__ == "__main__":
    unittest.main()
