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
from app.schemas.evaluation import (
    EvaluationScoreItem,
    EvaluationVerdict,
    FailureAttribution,
    InternalCorrection,
    SimulationEvaluationResponse,
)
from app.schemas.persona import Persona
from app.schemas.session import SessionMessageRequest
from app.schemas.simulation_generation import GeneratedResponse
from app.schemas.simulation_state import RelationshipStateV2, SimulationState
from app.schemas.strategy import (
    ResponseAction,
    TargetInterpretation,
    TargetResponsePolicy,
    ToneProfile,
)
from app.services.chat_record_analyzer import ChatRecordAnalyzer
from app.services.evidence_retriever import EvidenceRetriever
from app.services.evidence_store import (
    EvidenceStore,
    EpisodeStore,
    PersonaEvidenceRepository,
)
from app.services.persona_v2_adapter import compile_legacy_persona


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


def build_policy(
    *,
    action: ResponseAction = ResponseAction.ACKNOWLEDGE,
    length: str = "short",
    confidence: float = 0.82,
) -> TargetResponsePolicy:
    return TargetResponsePolicy(
        policy_id=f"policy_{action.value}",
        interpretation=TargetInterpretation(
            perceived_intent="用户礼貌请求查看材料。",
            perceived_tone="礼貌、具体并愿意负责。",
            salient_point="材料已经准备完整。",
            perceived_concern="需要确认材料是否可以进入审核。",
        ),
        action=action,
        response_goal="回应当前请求并保持导师立场。",
        stance="直接、克制、关注材料完整度。",
        required_content=["回应是否愿意查看材料"],
        forbidden_content=["替用户制定下一句话", "无条件扩大承诺"],
        tone_profile=ToneProfile(
            warmth=50,
            directness=80,
            formality=75,
            emotional_intensity=20,
            length=length,
        ),
        persona_evidence_refs=["persona_snapshot:persona_test"],
        memory_evidence_refs=[],
        confidence=confidence,
        uncertainty_notes=[],
    )


def strategy_mock(policy: TargetResponsePolicy) -> AsyncMock:
    agent = AsyncMock()
    agent.run.return_value = policy
    agent.prompt_version = "strategy-v2.0-active-test"
    return agent


class SimulationAgentV2PipelineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        llm_client_stub.generate_structured.return_value = _passing_evaluation()

    async def test_v2_runs_strategy_then_generation_and_keeps_legacy_response(self) -> None:
        strategy = strategy_mock(build_policy())
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text="可以，把完整材料发给我。",
            response_action="REPLY_BRIEF",
        )
        agent = SimulationAgentV2(
            strategy_agent=strategy,
            response_generator=generator,
        )
        response = await agent.run(build_request())

        strategy.run.assert_awaited_once()
        self.assertFalse(hasattr(agent, "decision_engine"))
        generator.run.assert_awaited_once()
        self.assertEqual(response.target_message.content, "可以，把完整材料发给我。")
        self.assertEqual(response.simulation.reply, response.target_message.content)
        self.assertEqual(response.response.action, "REPLY_BRIEF")
        self.assertGreater(response.updated_state.trust, 60)
        self.assertEqual(response.simulation_state.conversation_state.turn_count, 1)
        self.assertEqual(response.strategy_meta.strategy_action, "acknowledge")
        self.assertEqual(response.strategy_meta.simulation_action, "REPLY_BRIEF")
        self.assertFalse(response.runtime_meta.decision_fallback_used)

    async def test_previous_v2_state_is_passed_to_strategy(self) -> None:
        previous_state = SimulationState(
            session_id="session_test",
            persona_id="persona_test",
            relationship_state=RelationshipStateV2(trust=0.75),
        )
        strategy = strategy_mock(build_policy())
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text="发过来吧。",
            response_action="REPLY_BRIEF",
        )

        await SimulationAgentV2(
            strategy_agent=strategy,
            response_generator=generator,
        ).run(build_request(simulation_state=previous_state))

        strategy_input = strategy.run.await_args.args[0]
        self.assertEqual(strategy_input.relationship_state.trust, 0.75)
        self.assertEqual(strategy_input.session_id, "session_test")

    async def test_optional_precomputed_policy_skips_strategy_call(self) -> None:
        req = build_request()
        req.response_policy = build_policy(action=ResponseAction.REFUSE)
        strategy = strategy_mock(build_policy())
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text="这件事我不能答应。",
            response_action="REPLY_COLD",
        )

        response = await SimulationAgentV2(
            strategy_agent=strategy,
            response_generator=generator,
        ).run(req)

        strategy.run.assert_not_awaited()
        self.assertEqual(response.strategy_meta.policy_id, "policy_refuse")
        self.assertEqual(response.strategy_meta.strategy_action, "refuse")
        self.assertEqual(response.response.action, "REPLY_COLD")

    async def test_precompiled_persona_v2_is_used_by_strategy(self) -> None:
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
        strategy = strategy_mock(build_policy())
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text="可以，把材料发来。",
            response_action="REPLY_BRIEF",
        )

        await SimulationAgentV2(
            strategy_agent=strategy,
            response_generator=generator,
        ).run(request)

        strategy_input = strategy.run.await_args.args[0]
        self.assertEqual(
            strategy_input.persona_snapshot.communication_style.average_reply_length,
            "long",
        )
        self.assertTrue(
            strategy_input.persona_snapshot.evidence_summary.chat_record_available
        )

    async def test_retrieved_real_chat_evidence_reaches_simulation_generator(self) -> None:
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
        request = build_request()
        request.user_message = "老师，这次可能还是需要延期。"
        strategy = strategy_mock(
            build_policy(action=ResponseAction.ASK_CLARIFICATION)
        )
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text="具体还需要多久？",
            response_action="ASK_CLARIFICATION",
        )

        response = await SimulationAgentV2(
            strategy_agent=strategy,
            response_generator=generator,
            evidence_retriever=EvidenceRetriever(repo),
        ).run(request)

        generation_input = generator.run.await_args.args[0]
        self.assertTrue(generation_input.relevant_linguistic_evidence)
        self.assertIn("材料", generation_input.relevant_linguistic_evidence[0])
        self.assertEqual(response.evidence_meta.retrieval_mode, "keyword_behavior_top_k")
        self.assertEqual(response.evidence_meta.episode_ids[0], "episode_0001")

    async def test_request_rejects_mismatched_v2_context(self) -> None:
        mismatched = SimulationState(
            session_id="session_other",
            persona_id="persona_other",
        )
        with self.assertRaises(ValidationError):
            build_request(simulation_state=mismatched)

    async def test_no_reply_policy_skips_generator_and_returns_status(self) -> None:
        strategy = strategy_mock(build_policy(action=ResponseAction.NO_REPLY))
        generator = AsyncMock()
        response = await SimulationAgentV2(
            strategy_agent=strategy,
            response_generator=generator,
        ).run(build_request())

        generator.run.assert_not_awaited()
        self.assertEqual(response.response.action, "READ_NO_REPLY")
        self.assertEqual(response.response.text, "")
        self.assertEqual(response.response.status_text, "对方已读了消息。")
        self.assertEqual(response.target_message.role, "system")

    async def test_end_conversation_policy_generates_final_text_and_marks_end(self) -> None:
        strategy = strategy_mock(
            build_policy(action=ResponseAction.END_CONVERSATION, confidence=0.9)
        )
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text="这件事先到这里吧。",
            response_action="END_CONVERSATION",
        )
        evaluator = AsyncMock()
        evaluator.run.return_value = _passing_evaluation()
        evaluator.prompt_version = "evaluation-v2-test"

        response = await SimulationAgentV2(
            strategy_agent=strategy,
            response_generator=generator,
            evaluation_agent=evaluator,
        ).run(build_request())

        self.assertEqual(response.response.text, "这件事先到这里吧。")
        self.assertEqual(response.response.status_text, "对方结束了本次交流。")
        self.assertTrue(response.response.conversation_ended)
        self.assertTrue(response.evaluation_meta.evaluated)
        evaluator.run.assert_awaited_once()

    async def test_failed_style_evaluation_retries_generation_only_once(self) -> None:
        strategy = strategy_mock(build_policy())
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
        evaluator = AsyncMock()
        evaluator.run.side_effect = [
            _failed_style_evaluation(),
            _passing_evaluation(),
        ]
        evaluator.prompt_version = "evaluation-v2-test"

        response = await SimulationAgentV2(
            strategy_agent=strategy,
            response_generator=generator,
            evaluation_agent=evaluator,
        ).run(build_request())

        self.assertEqual(generator.run.await_count, 2)
        self.assertEqual(evaluator.run.await_count, 2)
        self.assertEqual(response.response.text, "可以，把材料发来。")
        self.assertEqual(response.evaluation_meta.retry_count, 1)
        self.assertEqual(response.evaluation_meta.feedback_action, "revise_simulation")

    async def test_evaluator_failure_does_not_block_initial_reply(self) -> None:
        strategy = strategy_mock(build_policy())
        initial = "哈哈😂😂" + "这是一段明显过长且过于随意的回复。" * 8
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text=initial,
            response_action="REPLY_BRIEF",
        )
        evaluator = AsyncMock()
        evaluator.run.side_effect = RuntimeError("unavailable")
        evaluator.prompt_version = "evaluation-v2-test"

        with self.assertLogs("app.agents.simulation_agent_v2", level="ERROR"):
            response = await SimulationAgentV2(
                strategy_agent=strategy,
                response_generator=generator,
                evaluation_agent=evaluator,
            ).run(build_request())

        self.assertEqual(response.response.text, initial)
        self.assertTrue(response.evaluation_meta.evaluator_failed)
        self.assertEqual(response.evaluation_meta.retry_count, 0)


def _score(value: int) -> EvaluationScoreItem:
    return EvaluationScoreItem(
        score=value,
        reason="符合当前人物与策略。",
        evidence=["persona_snapshot:persona_test"],
    )


def _passing_evaluation() -> SimulationEvaluationResponse:
    return _evaluation(score=90)


def _failed_style_evaluation() -> SimulationEvaluationResponse:
    return _evaluation(
        score=70,
        verdict=EvaluationVerdict.REVISE_SIMULATION,
        attribution=FailureAttribution.SIMULATION_EXECUTION_ERROR,
        correction=InternalCorrection(
            keep=["保持原 Response Policy。"],
            change=["缩短回复，移除 emoji，并保持正式表达。"],
            must_not=["不得改变 Response Action。"],
        ),
    )


def _evaluation(
    *,
    score: int,
    verdict: EvaluationVerdict = EvaluationVerdict.ACCEPT,
    attribution: FailureAttribution = FailureAttribution.NONE,
    correction: InternalCorrection | None = None,
) -> SimulationEvaluationResponse:
    item = _score(score)
    return SimulationEvaluationResponse(
        evaluation_id="evaluation_test",
        simulation_success_score=score,
        confidence=0.9,
        verdict=verdict,
        failure_attribution=attribution,
        persona_fidelity=item.model_copy(deep=True),
        dyadic_consistency=item.model_copy(deep=True),
        state_continuity=item.model_copy(deep=True),
        strategy_adherence=item.model_copy(deep=True),
        reaction_plausibility=item.model_copy(deep=True),
        style_fidelity=item.model_copy(deep=True),
        evidence_grounding=item.model_copy(deep=True),
        critical_issues=[] if correction is None else ["风格执行偏差"],
        correction_for_strategy=None,
        correction_for_simulation=correction,
        session_learning_signals=[],
        evaluator_notes=[],
    )


if __name__ == "__main__":
    unittest.main()
