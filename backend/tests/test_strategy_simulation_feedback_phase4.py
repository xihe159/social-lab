from __future__ import annotations

import hashlib
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock


llm_client_stub = sys.modules.setdefault(
    "app.llm.client",
    types.ModuleType("app.llm.client"),
)


class StubLLMClientError(RuntimeError):
    pass


llm_client_stub.LLMClientError = StubLLMClientError
if not hasattr(llm_client_stub, "generate_structured"):
    llm_client_stub.generate_structured = AsyncMock()

from app.agents.simulation_agent_v2 import SimulationAgentV2
from app.schemas.common import RelationshipState
from app.schemas.evaluation import (
    EvaluationScoreItem,
    EvaluationVerdict,
    FailureAttribution,
    FeedbackAction,
    SimulationEvaluationResponse,
)
from app.schemas.feedback import InternalCorrection
from app.schemas.memory import SessionMemory
from app.schemas.persona import Persona
from app.schemas.safety import SafetyCheckResponse
from app.schemas.session import SessionMessageRequest
from app.schemas.simulation_generation import GeneratedResponse
from app.schemas.strategy import (
    ResponseAction,
    TargetInterpretation,
    TargetResponsePolicy,
    ToneProfile,
)
from app.services.session_orchestrator import SessionOrchestrator
from app.services.simulation_feedback_loop import SimulationFeedbackLoop
from app.services.simulation_turn_store import SimulationTurnStore


def request() -> SessionMessageRequest:
    return SessionMessageRequest(
        scenario="advisor",
        goal="请导师确认材料",
        outcome="确认是否可以提交",
        role="导师",
        relation="师生关系",
        persona=Persona(
            title="直接的导师",
            style="简短、正式",
            speed="正常",
            focus="材料完整度",
            risk="无条件承诺",
            strategy="先确认材料",
            state=RelationshipState(
                trust=60,
                respect=70,
                familiarity=40,
                affinity=45,
                authority=80,
                emotional=10,
            ),
        ),
        messages=[],
        user_message="老师，材料可以这样提交吗？",
        persona_id="persona_phase4",
        session_id="session_phase4",
    )


def policy(
    policy_id: str,
    *,
    action: ResponseAction = ResponseAction.ACKNOWLEDGE,
    goal: str = "确认已看到材料。",
) -> TargetResponsePolicy:
    return TargetResponsePolicy(
        policy_id=policy_id,
        interpretation=TargetInterpretation(
            perceived_intent="用户希望确认材料。",
            perceived_tone="礼貌且具体。",
            salient_point="材料等待确认。",
            perceived_concern="是否可以提交。",
        ),
        action=action,
        response_goal=goal,
        stance="直接、克制。",
        required_content=[goal],
        forbidden_content=["无条件扩大承诺"],
        tone_profile=ToneProfile(
            warmth=45,
            directness=80,
            formality=80,
            emotional_intensity=20,
            length="short",
        ),
        persona_evidence_refs=["persona_snapshot:persona_phase4"],
        memory_evidence_refs=[],
        confidence=0.86,
        uncertainty_notes=[],
    )


def correction(label: str) -> InternalCorrection:
    return InternalCorrection(
        keep=["保持人物的直接语气。"],
        change=[label],
        must_not=["不得生成用户建议。"],
    )


def evaluation(
    score: int,
    verdict: EvaluationVerdict,
    attribution: FailureAttribution,
    *,
    strategy_correction: InternalCorrection | None = None,
    simulation_correction: InternalCorrection | None = None,
) -> SimulationEvaluationResponse:
    item = EvaluationScoreItem(
        score=score,
        reason="阶段 4 固定测试评分。",
        evidence=["persona_snapshot:persona_phase4"],
    )
    return SimulationEvaluationResponse(
        evaluation_id=f"evaluation_{score}",
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
        critical_issues=[] if score >= 75 else ["需要内部修正"],
        correction_for_strategy=strategy_correction,
        correction_for_simulation=simulation_correction,
        session_learning_signals=[],
        evaluator_notes=[],
    )


def strategy_agent(*policies: TargetResponsePolicy) -> AsyncMock:
    agent = AsyncMock()
    agent.run.side_effect = list(policies)
    agent.prompt_version = "strategy-v2.1-phase4-test"
    return agent


def evaluation_agent(*results: SimulationEvaluationResponse) -> AsyncMock:
    agent = AsyncMock()
    agent.run.side_effect = list(results)
    agent.prompt_version = "evaluation-v2.0-phase3-test"
    return agent


def generator(*texts: str) -> AsyncMock:
    agent = AsyncMock()
    agent.run.side_effect = [
        GeneratedResponse(response_text=text, response_action="REPLY_BRIEF")
        for text in texts
    ]
    agent.prompt_version = "simulation-v2.1-phase4-test"
    return agent


def allowed_safety() -> SafetyCheckResponse:
    return SafetyCheckResponse(
        allowed=True,
        risk_level="none",
        action="allow",
        risk_types=[],
        user_notice="",
        safe_rewrite_hint="",
        should_redact=False,
        redacted_fields=[],
    )


def empty_memory() -> SessionMemory:
    return SessionMemory(
        conversation_summary="仅包含最终回复。",
        user_strategy_pattern=[],
        target_sensitive_points=[],
        resolved_points=[],
        unresolved_points=[],
        important_events=[],
        next_suggested_focus="",
    )


class FeedbackRoutingPhase4Tests(unittest.TestCase):
    def test_feedback_controller_enforces_one_correction_maximum(self) -> None:
        failed = evaluation(
            60,
            EvaluationVerdict.REVISE_SIMULATION,
            FailureAttribution.SIMULATION_EXECUTION_ERROR,
            simulation_correction=correction("缩短回复。"),
        )
        loop = SimulationFeedbackLoop()
        self.assertEqual(
            loop.plan(failed, corrections_used=0).action,
            FeedbackAction.REVISE_SIMULATION,
        )
        self.assertEqual(
            loop.plan(failed, corrections_used=1).action,
            FeedbackAction.NONE,
        )


class StrategySimulationFeedbackPhase4Tests(unittest.IsolatedAsyncioTestCase):
    async def test_simulation_error_reuses_policy_and_regenerates_once(self) -> None:
        same_policy = policy("policy_initial")
        strategy = strategy_agent(same_policy)
        render = generator("过长且偏离策略的首次候选。", "收到，材料发来。")
        sim_correction = correction("将回复缩短为一句，并删除额外承诺。")
        evaluator = evaluation_agent(
            evaluation(
                68,
                EvaluationVerdict.REVISE_SIMULATION,
                FailureAttribution.SIMULATION_EXECUTION_ERROR,
                simulation_correction=sim_correction,
            ),
            evaluation(90, EvaluationVerdict.ACCEPT, FailureAttribution.NONE),
        )

        response = await SimulationAgentV2(
            strategy_agent=strategy,
            response_generator=render,
            evaluation_agent=evaluator,
        ).run(request())

        self.assertEqual(strategy.run.await_count, 1)
        self.assertEqual(render.run.await_count, 2)
        self.assertEqual(evaluator.run.await_count, 2)
        retry_input = render.run.await_args_list[1].args[0]
        self.assertEqual(retry_input.strategy_policy_id, "policy_initial")
        self.assertEqual(retry_input.evaluation_correction, sim_correction)
        self.assertEqual(response.response.text, "收到，材料发来。")
        self.assertEqual(response.evaluation_meta.initial_score, 68)
        self.assertEqual(response.evaluation_meta.final_score, 90)
        self.assertEqual(response.evaluation_meta.score_delta, 22)
        self.assertEqual(response.runtime_meta.simulation_revision_count, 1)
        self.assertEqual(response.runtime_meta.feedback_retry_count, 1)

    async def test_strategy_error_replans_then_regenerates_once(self) -> None:
        initial_policy = policy("policy_initial")
        revised_policy = policy(
            "policy_revised",
            action=ResponseAction.ACCEPT_WITH_CONDITION,
            goal="允许提交，但要求先补齐缺失页。",
        )
        strategy_fix = correction("把无条件接受改为有条件接受。")
        strategy = strategy_agent(initial_policy, revised_policy)
        render = generator("当然可以，直接提交。", "可以，先补齐缺失页再提交。")
        evaluator = evaluation_agent(
            evaluation(
                52,
                EvaluationVerdict.REPLAN_AND_REGENERATE,
                FailureAttribution.STRATEGY_ERROR,
                strategy_correction=strategy_fix,
            ),
            evaluation(88, EvaluationVerdict.ACCEPT, FailureAttribution.NONE),
        )

        response = await SimulationAgentV2(
            strategy_agent=strategy,
            response_generator=render,
            evaluation_agent=evaluator,
        ).run(request())

        self.assertEqual(strategy.run.await_count, 2)
        retry_strategy_request = strategy.run.await_args_list[1].args[0]
        self.assertEqual(retry_strategy_request.evaluation_correction, strategy_fix)
        self.assertEqual(render.run.await_count, 2)
        final_evaluation_request = evaluator.run.await_args_list[1].args[0]
        self.assertEqual(
            final_evaluation_request.response_policy.policy_id,
            "policy_revised",
        )
        self.assertEqual(response.strategy_meta.policy_id, "policy_revised")
        self.assertEqual(response.response.text, "可以，先补齐缺失页再提交。")
        self.assertEqual(response.runtime_meta.strategy_replan_count, 1)

    async def test_final_low_score_never_starts_a_second_feedback_loop(self) -> None:
        strategy = strategy_agent(
            policy("policy_initial"),
            policy("policy_revised", action=ResponseAction.SET_BOUNDARY),
        )
        render = generator("首次候选。", "修正后的最终候选。")
        evaluator = evaluation_agent(
            evaluation(
                50,
                EvaluationVerdict.REPLAN_AND_REGENERATE,
                FailureAttribution.STRATEGY_ERROR,
                strategy_correction=correction("重新制定边界策略。"),
            ),
            evaluation(
                58,
                EvaluationVerdict.REPLAN_AND_REGENERATE,
                FailureAttribution.MIXED,
                strategy_correction=correction("仍需继续重规划。"),
            ),
        )

        response = await SimulationAgentV2(
            strategy_agent=strategy,
            response_generator=render,
            evaluation_agent=evaluator,
        ).run(request())

        self.assertEqual(strategy.run.await_count, 2)
        self.assertEqual(render.run.await_count, 2)
        self.assertEqual(evaluator.run.await_count, 2)
        self.assertEqual(response.runtime_meta.feedback_retry_count, 1)
        self.assertEqual(response.response.text, "修正后的最终候选。")
        self.assertEqual(
            response.evaluation_meta.final_verdict,
            EvaluationVerdict.REPLAN_AND_REGENERATE,
        )

    async def test_rejected_candidate_never_reaches_turn_store_or_memory(self) -> None:
        initial_text = "这条被 Evaluation 拒绝的候选不能进入 Memory。"
        final_text = "收到，请先补齐材料。"
        store = SimulationTurnStore(max_records=10)
        agent = SimulationAgentV2(
            strategy_agent=strategy_agent(policy("policy_initial")),
            response_generator=generator(initial_text, final_text),
            evaluation_agent=evaluation_agent(
                evaluation(
                    65,
                    EvaluationVerdict.REVISE_SIMULATION,
                    FailureAttribution.SIMULATION_EXECUTION_ERROR,
                    simulation_correction=correction("删除额外承诺。"),
                ),
                evaluation(90, EvaluationVerdict.ACCEPT, FailureAttribution.NONE),
            ),
            turn_store=store,
        )
        orchestrator = SessionOrchestrator(simulation_agent_version="v2")
        orchestrator.simulation_agent = agent
        orchestrator._run_safety_agent = AsyncMock(return_value=allowed_safety())
        orchestrator.memory_agent.run = AsyncMock(
            return_value=SimpleNamespace(
                memory=empty_memory(),
                memory_reason="只记录最终候选。",
                new_facts=[],
                next_focus="",
            )
        )

        response = await orchestrator.handle_message(request())

        memory_input = orchestrator.memory_agent.run.await_args.args[0]
        self.assertEqual(memory_input.target_reply, final_text)
        self.assertNotIn(initial_text, memory_input.model_dump_json())
        self.assertEqual(response.response.text, final_text)
        records = store.list_for_session("session_phase4")
        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0].response_text_digest,
            hashlib.sha256(final_text.encode("utf-8")).hexdigest(),
        )
        self.assertNotEqual(
            records[0].response_text_digest,
            hashlib.sha256(initial_text.encode("utf-8")).hexdigest(),
        )
        self.assertTrue(records[0].rejected_candidate_discarded)

    async def test_active_v2_pipeline_has_no_consistency_evaluator_owner(self) -> None:
        agent = SimulationAgentV2(
            strategy_agent=strategy_agent(policy("policy_initial")),
            response_generator=generator("收到。"),
            evaluation_agent=evaluation_agent(
                evaluation(90, EvaluationVerdict.ACCEPT, FailureAttribution.NONE)
            ),
        )
        await agent.run(request())
        self.assertFalse(hasattr(agent, "consistency_evaluator"))


if __name__ == "__main__":
    unittest.main()
