from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import AsyncMock

from pydantic import ValidationError


llm_client_stub = types.ModuleType("app.llm.client")
llm_client_stub.generate_structured = AsyncMock()
sys.modules.setdefault("app.llm.client", llm_client_stub)

from app.agents.simulation_agent_v2 import SimulationAgentV2
from app.schemas.common import RelationshipState
from app.schemas.persona import Persona
from app.schemas.session import SessionMessageRequest
from app.schemas.simulation_decision import (
    BehaviorSignals,
    ResponsePolicy,
    SimulationStateDelta,
    TurnAnalysis,
    TurnDecisionOutput,
    TurnDecisionResult,
)
from app.schemas.simulation_generation import GeneratedResponse
from app.schemas.simulation_state import RelationshipStateV2, SimulationState
from app.services.persona_v2_adapter import compile_legacy_persona
from app.services.chat_record_analyzer import ChatRecordAnalyzer
from app.services.evidence_retriever import EvidenceRetriever
from app.services.evidence_store import EvidenceStore, EpisodeStore, PersonaEvidenceRepository
from app.agents.simulation.consistency_evaluator import ConsistencyEvaluator
from app.schemas.consistency_evaluation import (
    ConsistencyEvaluationOutput,
    ConsistencyIssue,
    ConsistencyScores,
)


def build_request(
    *,
    simulation_state: SimulationState | None = None,
) -> SessionMessageRequest:
    return SessionMessageRequest(
        scenario="advisor",
        goal="请求导师修改推荐信",
        outcome="导师愿意帮忙",
        role="导师",
        relation="师生关系，彼此尊重",
        persona=Persona(
            title="严格但愿意帮助的导师",
            style="直接、简洁、结果导向",
            speed="偏慢",
            focus="材料是否完整",
            risk="临时催促和缺少责任承担",
            strategy="提供完整材料和明确时间",
            state=RelationshipState(
                trust=60,
                respect=70,
                familiarity=45,
                affinity=50,
                authority=80,
                emotional=20,
            ),
        ),
        messages=[],
        user_message="老师您好，材料我已经整理完整了，想请您帮忙看看。",
        persona_id="persona_test",
        session_id="session_test",
        simulation_state=simulation_state,
    )


def build_decision_result(
    state: SimulationState,
    *,
    action: str = "REPLY_BRIEF",
) -> TurnDecisionResult:
    zero_delta = {
        "trust": 0.05,
        "respect": 0.02,
        "warmth": 0.03,
        "patience": 0.0,
        "psychological_safety": 0.02,
        "willingness_to_engage": 0.05,
        "irritation": -0.02,
        "hurt": 0.0,
        "anxiety": 0.0,
        "defensiveness": -0.02,
        "fatigue": 0.0,
        "conflict_level": -0.02,
        "topic_resolution": 0.08,
        "boundary_pressure": -0.02,
    }
    return TurnDecisionResult(
        decision=TurnDecisionOutput(
            turn_analysis=TurnAnalysis(
                intent="request_review",
                behavior_signals=BehaviorSignals(
                    politeness=0.9,
                    clarity=0.8,
                    accountability=0.8,
                    pressure=0.1,
                    blame=0.0,
                    vulnerability=0.2,
                    boundary_violation=0.0,
                    honesty_signal=0.8,
                ),
                detected_events=["materials_prepared"],
            ),
            state_delta=SimulationStateDelta(**zero_delta),
            response_policy=ResponsePolicy(
                action=action,
                content_goals=["确认可以查看", "要求发送材料"],
                tone="直接但愿意帮助",
                reply_length="short",
                must_avoid=[],
            ),
            confidence=0.82,
        ),
        updated_state=state,
    )


class SimulationAgentV2PipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_v2_runs_decision_then_generation_and_keeps_legacy_response(self) -> None:
        updated_state = SimulationState(
            session_id="session_test",
            persona_id="persona_test",
            relationship_state=RelationshipStateV2(
                trust=0.65,
                respect=0.72,
                warmth=0.53,
                patience=0.6,
                psychological_safety=0.62,
                willingness_to_engage=0.7,
            ),
        )
        decision_engine = AsyncMock()
        decision_engine.run.return_value = build_decision_result(updated_state)
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text="可以，把完整材料发给我。",
            response_action="REPLY_BRIEF",
        )
        agent = SimulationAgentV2(
            decision_engine=decision_engine,
            response_generator=generator,
        )

        response = await agent.run(build_request())

        self.assertEqual(response.target_message.content, "可以，把完整材料发给我。")
        self.assertEqual(response.simulation.reply, response.target_message.content)
        self.assertEqual(response.simulation.attitude, "简短回应")
        self.assertEqual(response.updated_state.trust, 65)
        self.assertEqual(response.simulation_state, updated_state)
        decision_engine.run.assert_awaited_once()
        generator.run.assert_awaited_once()
        self.assertFalse(response.evaluation_meta.evaluated)

    async def test_previous_v2_state_is_passed_to_next_decision(self) -> None:
        previous_state = SimulationState(
            session_id="session_test",
            persona_id="persona_test",
            relationship_state=RelationshipStateV2(trust=0.75),
        )
        decision_engine = AsyncMock()
        decision_engine.run.return_value = build_decision_result(previous_state)
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text="发过来吧。",
            response_action="REPLY_BRIEF",
        )

        await SimulationAgentV2(
            decision_engine=decision_engine,
            response_generator=generator,
        ).run(build_request(simulation_state=previous_state))

        decision_input = decision_engine.run.await_args.args[0]
        self.assertEqual(decision_input.current_state.relationship_state.trust, 0.75)
        self.assertEqual(decision_input.current_state.session_id, "session_test")

    async def test_precompiled_persona_v2_is_used_by_decision_engine(self) -> None:
        request = build_request()
        learned = compile_legacy_persona(
            request.persona,
            persona_id="persona_test",
            role=request.role,
            relation=request.relation,
            scenario=request.scenario,
        )
        learned.communication_style.average_reply_length = "long"
        learned.evidence_summary.chat_record_available = True
        request.persona_v2 = learned
        state = SimulationState(session_id="session_test", persona_id="persona_test")
        decision_engine = AsyncMock()
        decision_engine.run.return_value = build_decision_result(state)
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text="可以，把材料发来。",
            response_action="REPLY_BRIEF",
        )

        await SimulationAgentV2(
            decision_engine=decision_engine,
            response_generator=generator,
        ).run(request)

        decision_input = decision_engine.run.await_args.args[0]
        self.assertEqual(decision_input.persona.communication_style.average_reply_length, "long")
        self.assertTrue(decision_input.persona.evidence_summary.chat_record_available)

    async def test_retrieved_real_chat_evidence_reaches_both_model_stages(self) -> None:
        chat_log = """我：材料来不及，能否延期一天？
导师：具体还缺什么？今天先发已有材料。
我：会议改到周三可以吗？
导师：可以，提前通知其他人。
我：这是我的问题，我会负责补齐。
导师：好的，补齐后发我确认。"""
        analysis = ChatRecordAnalyzer().analyze(chat_log, target_role="导师")
        assert analysis is not None
        repo = PersonaEvidenceRepository(EpisodeStore(), EvidenceStore())
        repo.register("persona_test", analysis)
        retriever = EvidenceRetriever(repo)
        request = build_request()
        request.user_message = "老师，这次可能还是需要延期。"
        state = SimulationState(session_id="session_test", persona_id="persona_test")
        decision_engine = AsyncMock()
        decision_engine.run.return_value = build_decision_result(state)
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text="具体还需要多久？",
            response_action="REPLY_BRIEF",
        )

        response = await SimulationAgentV2(
            decision_engine=decision_engine,
            response_generator=generator,
            evidence_retriever=retriever,
        ).run(request)

        decision_input = decision_engine.run.await_args.args[0]
        generation_input = generator.run.await_args.args[0]
        self.assertTrue(decision_input.relevant_evidence)
        self.assertIn("延期", decision_input.relevant_evidence[0])
        self.assertTrue(generation_input.relevant_linguistic_evidence)
        self.assertEqual(response.evidence_meta.retrieval_mode, "keyword_behavior_top_k")
        self.assertEqual(response.evidence_meta.episode_ids[0], "episode_0001")

    async def test_request_rejects_mismatched_v2_context(self) -> None:
        mismatched = SimulationState(
            session_id="session_other",
            persona_id="persona_other",
        )

        with self.assertRaises(ValidationError):
            build_request(simulation_state=mismatched)

    async def test_read_no_reply_skips_generator_and_returns_status(self) -> None:
        state = SimulationState(
            session_id="session_test",
            persona_id="persona_test",
        )
        decision_engine = AsyncMock()
        decision_engine.run.return_value = build_decision_result(
            state,
            action="READ_NO_REPLY",
        )
        generator = AsyncMock()

        response = await SimulationAgentV2(
            decision_engine=decision_engine,
            response_generator=generator,
        ).run(build_request())

        generator.run.assert_not_awaited()
        self.assertEqual(response.response.action, "READ_NO_REPLY")
        self.assertEqual(response.response.text, "")
        self.assertEqual(response.response.status_text, "对方已读了消息。")
        self.assertFalse(response.response.conversation_ended)
        self.assertEqual(response.target_message.role, "system")

    async def test_end_conversation_generates_final_text_and_marks_end(self) -> None:
        state = SimulationState(
            session_id="session_test",
            persona_id="persona_test",
        )
        decision_engine = AsyncMock()
        decision_engine.run.return_value = build_decision_result(
            state,
            action="END_CONVERSATION",
        )
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text="这件事先到这里吧。",
            response_action="END_CONVERSATION",
        )
        evaluator = ConsistencyEvaluator()
        evaluator.evaluate = AsyncMock(return_value=_passing_evaluation())

        response = await SimulationAgentV2(
            decision_engine=decision_engine,
            response_generator=generator,
            consistency_evaluator=evaluator,
        ).run(build_request())

        generator.run.assert_awaited_once()
        self.assertEqual(response.target_message.role, "target")
        self.assertEqual(response.response.text, "这件事先到这里吧。")
        self.assertEqual(response.response.status_text, "对方结束了本次交流。")
        self.assertTrue(response.response.conversation_ended)
        self.assertTrue(response.evaluation_meta.evaluated)
        evaluator.evaluate.assert_awaited_once()

    async def test_failed_style_evaluation_retries_generation_only_once(self) -> None:
        state = SimulationState(session_id="session_test", persona_id="persona_test")
        decision_engine = AsyncMock()
        decision_engine.run.return_value = build_decision_result(state)
        generator = AsyncMock()
        generator.run.side_effect = [
            GeneratedResponse(
                response_text="哈哈😂😂" + "这是一段明显过长且过于随意的回复。" * 8,
                response_action="REPLY_BRIEF",
            ),
            GeneratedResponse(
                response_text="可以，把材料发来。",
                response_action="REPLY_BRIEF",
            ),
        ]
        evaluator = ConsistencyEvaluator()
        evaluator.evaluate = AsyncMock(return_value=_failed_style_evaluation())

        response = await SimulationAgentV2(
            decision_engine=decision_engine,
            response_generator=generator,
            consistency_evaluator=evaluator,
        ).run(build_request())

        self.assertEqual(generator.run.await_count, 2)
        self.assertEqual(evaluator.evaluate.await_count, 1)
        retry_input = generator.run.await_args_list[1].args[0]
        self.assertEqual(retry_input.generation_attempt, 2)
        self.assertTrue(retry_input.consistency_feedback)
        self.assertEqual(response.response.text, "可以，把材料发来。")
        self.assertEqual(response.evaluation_meta.retry_count, 1)

    async def test_evaluator_failure_does_not_block_initial_reply(self) -> None:
        state = SimulationState(session_id="session_test", persona_id="persona_test")
        decision_engine = AsyncMock()
        decision_engine.run.return_value = build_decision_result(state)
        initial = "哈哈😂😂" + "这是一段明显过长且过于随意的回复。" * 8
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text=initial,
            response_action="REPLY_BRIEF",
        )
        evaluator = ConsistencyEvaluator()
        evaluator.evaluate = AsyncMock(side_effect=RuntimeError("evaluator unavailable"))

        with self.assertLogs("app.agents.simulation_agent_v2", level="ERROR"):
            response = await SimulationAgentV2(
                decision_engine=decision_engine,
                response_generator=generator,
                consistency_evaluator=evaluator,
            ).run(build_request())

        self.assertEqual(response.response.text, initial)
        self.assertTrue(response.evaluation_meta.evaluator_failed)
        self.assertEqual(response.evaluation_meta.retry_count, 0)
        self.assertEqual(generator.run.await_count, 1)


def _passing_evaluation() -> ConsistencyEvaluationOutput:
    return ConsistencyEvaluationOutput(
        **{
            "pass": True,
            "scores": _scores(0.9),
            "issues": [],
        }
    )


def _failed_style_evaluation() -> ConsistencyEvaluationOutput:
    scores = _scores(0.9)
    scores.style_consistency = 0.35
    return ConsistencyEvaluationOutput(
        **{
            "pass": False,
            "scores": scores,
            "issues": [
                ConsistencyIssue(
                    dimension="style_consistency",
                    severity="high",
                    message="回复明显偏离人物语言风格。",
                    retry_instruction="缩短回复，移除 emoji，并保持正式表达。",
                )
            ],
        }
    )


def _scores(value: float) -> ConsistencyScores:
    return ConsistencyScores(
        persona_consistency=value,
        dyadic_consistency=value,
        style_consistency=value,
        emotional_continuity=value,
        evidence_consistency=value,
        reaction_proportionality=value,
    )


if __name__ == "__main__":
    unittest.main()
