from __future__ import annotations

import os
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch


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
    SimulationEvaluationResponse,
)
from app.schemas.persona import Persona
from app.schemas.runtime_metrics import AgentRuntimeMetric
from app.schemas.session import SessionMessageRequest
from app.schemas.simulation_generation import GeneratedResponse
from app.schemas.strategy import (
    ResponseAction,
    TargetInterpretation,
    TargetResponsePolicy,
    ToneProfile,
)
from app.services.agent_runtime_metrics import AgentRuntimeMetricsStore
from app.services.evaluation_execution_policy import (
    resolve_evaluation_execution_mode,
)
from app.services.simulation_adjustment_manager import SimulationAdjustmentManager


def _request(
    session_id: str = "session_phase6",
    *,
    user_message: str = "老师，材料可以这样提交吗？",
) -> SessionMessageRequest:
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
        user_message=user_message,
        persona_id="persona_phase6",
        session_id=session_id,
    )


def _policy(
    index: int,
    *,
    confidence: float = 0.9,
    action: ResponseAction = ResponseAction.ACKNOWLEDGE,
    tone: str = "礼貌且具体。",
) -> TargetResponsePolicy:
    return TargetResponsePolicy(
        policy_id=f"policy_{index}",
        interpretation=TargetInterpretation(
            perceived_intent="用户希望确认材料。",
            perceived_tone=tone,
            salient_point="材料等待确认。",
            perceived_concern="是否可以提交。",
        ),
        action=action,
        response_goal="确认已看到材料。",
        stance="直接、克制。",
        required_content=["确认已看到材料。"],
        forbidden_content=["无条件扩大承诺"],
        tone_profile=ToneProfile(
            warmth=45,
            directness=80,
            formality=80,
            emotional_intensity=20,
            length="short",
        ),
        persona_evidence_refs=["persona_snapshot:persona_phase6"],
        memory_evidence_refs=[],
        confidence=confidence,
        uncertainty_notes=[],
    )


def _evaluation(index: int, signals: list[str] | None = None):
    item = EvaluationScoreItem(
        score=88,
        reason="第六阶段固定测试评分。",
        evidence=["persona_snapshot:persona_phase6"],
    )
    return SimulationEvaluationResponse(
        evaluation_id=f"evaluation_{index}",
        simulation_success_score=88,
        confidence=0.9,
        verdict=EvaluationVerdict.ACCEPT,
        failure_attribution=FailureAttribution.NONE,
        persona_fidelity=item.model_copy(deep=True),
        dyadic_consistency=item.model_copy(deep=True),
        state_continuity=item.model_copy(deep=True),
        strategy_adherence=item.model_copy(deep=True),
        reaction_plausibility=item.model_copy(deep=True),
        style_fidelity=item.model_copy(deep=True),
        evidence_grounding=item.model_copy(deep=True),
        critical_issues=[],
        correction_for_strategy=None,
        correction_for_simulation=None,
        session_learning_signals=signals or [],
        evaluator_notes=[],
    )


def _strategy(*policies: TargetResponsePolicy) -> AsyncMock:
    agent = AsyncMock()
    agent.run.side_effect = list(policies)
    agent.prompt_version = "strategy-v2.2-phase6-test"
    return agent


def _generator(count: int) -> AsyncMock:
    agent = AsyncMock()
    agent.run.side_effect = [
        GeneratedResponse(response_text="收到。", response_action="REPLY_BRIEF")
        for _ in range(count)
    ]
    agent.prompt_version = "simulation-v2.2-phase6-test"
    return agent


def _evaluator(*results: SimulationEvaluationResponse) -> AsyncMock:
    agent = AsyncMock()
    agent.run.side_effect = list(results)
    agent.prompt_version = "evaluation-v2.1-phase6-test"
    return agent


class _DeferredTasks:
    def __init__(self) -> None:
        self.items: list[tuple[object, tuple, dict]] = []

    def add_task(self, function, *args, **kwargs) -> None:
        self.items.append((function, args, kwargs))

    async def run(self, index: int = 0) -> None:
        function, args, kwargs = self.items[index]
        await function(*args, **kwargs)


class EvaluationExecutionPolicyPhase6Tests(unittest.TestCase):
    def test_environment_selects_development_sync_and_production_hybrid(self) -> None:
        with patch.dict(os.environ, {"APP_ENV": "development"}, clear=True):
            self.assertEqual(
                resolve_evaluation_execution_mode(),
                "development_sync",
            )
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=True):
            self.assertEqual(
                resolve_evaluation_execution_mode(),
                "production_hybrid",
            )


class AsyncEvaluationPhase6Tests(unittest.IsolatedAsyncioTestCase):
    async def test_normal_turn_returns_before_background_evaluation(self) -> None:
        deferred = _DeferredTasks()
        evaluator = _evaluator(_evaluation(1))
        metrics = AgentRuntimeMetricsStore()
        agent = SimulationAgentV2(
            strategy_agent=_strategy(_policy(1)),
            response_generator=_generator(1),
            evaluation_agent=evaluator,
            adjustment_manager=SimulationAdjustmentManager(),
            evaluation_execution_mode="production_hybrid",
            runtime_metrics=metrics,
        )

        response = await agent.run(
            _request(),
            defer_background=deferred.add_task,
        )

        evaluator.run.assert_not_awaited()
        self.assertEqual(response.response.text, "收到。")
        self.assertEqual(response.evaluation_meta.execution_mode, "background")
        self.assertTrue(response.evaluation_meta.background_scheduled)
        self.assertFalse(response.evaluation_meta.evaluated)
        self.assertEqual(response.runtime_meta.evaluation_call_count, 0)
        self.assertEqual(len(deferred.items), 1)

        await deferred.run()
        evaluator.run.assert_awaited_once()
        background_summary = next(
            item
            for item in metrics.snapshot().summaries
            if item.agent == "EvaluationAgent" and item.run_mode == "background"
        )
        self.assertEqual(background_summary.success_rate, 1.0)

    async def test_low_confidence_turn_keeps_synchronous_feedback_gate(self) -> None:
        deferred = _DeferredTasks()
        evaluator = _evaluator(_evaluation(1))
        agent = SimulationAgentV2(
            strategy_agent=_strategy(_policy(1, confidence=0.69)),
            response_generator=_generator(1),
            evaluation_agent=evaluator,
            adjustment_manager=SimulationAdjustmentManager(),
            evaluation_execution_mode="production_hybrid",
            runtime_metrics=AgentRuntimeMetricsStore(),
        )

        response = await agent.run(
            _request(),
            defer_background=deferred.add_task,
        )

        evaluator.run.assert_awaited_once()
        self.assertEqual(response.evaluation_meta.execution_mode, "synchronous")
        self.assertIn(
            "low_strategy_confidence",
            response.evaluation_meta.critical_reasons,
        )
        self.assertTrue(response.evaluation_meta.evaluated)
        self.assertEqual(deferred.items, [])

    async def test_user_pressure_turn_is_evaluated_synchronously(self) -> None:
        deferred = _DeferredTasks()
        evaluator = _evaluator(_evaluation(1))
        agent = SimulationAgentV2(
            strategy_agent=_strategy(_policy(1)),
            response_generator=_generator(1),
            evaluation_agent=evaluator,
            adjustment_manager=SimulationAdjustmentManager(),
            evaluation_execution_mode="production_hybrid",
            runtime_metrics=AgentRuntimeMetricsStore(),
        )

        response = await agent.run(
            _request(user_message="你必须马上答应，不然你就等着。"),
            defer_background=deferred.add_task,
        )

        evaluator.run.assert_awaited_once()
        self.assertIn(
            "user_pressure_or_threat",
            response.evaluation_meta.critical_reasons,
        )
        self.assertEqual(deferred.items, [])

    async def test_two_previous_same_issues_make_next_turn_synchronous(self) -> None:
        manager = SimulationAdjustmentManager()
        for index in range(1, 3):
            context = manager.begin_turn("session_repeated")
            manager.observe(
                session_id="session_repeated",
                turn_number=context.turn_number,
                evaluation_id=f"evaluation_{index}",
                signals=["reply_too_long"],
                confidence=0.9,
                failure_attribution=FailureAttribution.NONE,
            )
        deferred = _DeferredTasks()
        evaluator = _evaluator(_evaluation(3))
        agent = SimulationAgentV2(
            strategy_agent=_strategy(_policy(3)),
            response_generator=_generator(1),
            evaluation_agent=evaluator,
            adjustment_manager=manager,
            evaluation_execution_mode="production_hybrid",
            runtime_metrics=AgentRuntimeMetricsStore(),
        )

        response = await agent.run(
            _request("session_repeated"),
            defer_background=deferred.add_task,
        )

        self.assertIn(
            "repeated_evaluation_issue",
            response.evaluation_meta.critical_reasons,
        )
        evaluator.run.assert_awaited_once()
        self.assertEqual(deferred.items, [])

    async def test_out_of_order_background_results_still_feed_next_profile(self) -> None:
        manager = SimulationAdjustmentManager()
        deferred = _DeferredTasks()
        strategy = _strategy(*[_policy(index) for index in range(1, 5)])
        evaluator = _evaluator(
            *[
                _evaluation(index, ["reply_too_long"])
                for index in range(1, 4)
            ]
        )
        agent = SimulationAgentV2(
            strategy_agent=strategy,
            response_generator=_generator(4),
            evaluation_agent=evaluator,
            adjustment_manager=manager,
            evaluation_execution_mode="production_hybrid",
            runtime_metrics=AgentRuntimeMetricsStore(),
        )
        request = _request("session_out_of_order")

        for _ in range(3):
            await agent.run(request, defer_background=deferred.add_task)
        self.assertEqual(len(deferred.items), 3)

        await deferred.run(1)
        await deferred.run(2)
        await deferred.run(0)

        fourth = await agent.run(request, defer_background=deferred.add_task)
        fourth_strategy_input = strategy.run.await_args_list[3].args[0]
        self.assertTrue(fourth.adjustment_meta.applied)
        self.assertIsNotNone(fourth_strategy_input.simulation_adjustments)
        self.assertEqual(
            fourth_strategy_input.simulation_adjustments.style_adjustments,
            ["下一轮回复长度控制在两句以内。"],
        )


class RuntimeMetricsPhase6Tests(unittest.TestCase):
    def test_metrics_expose_success_rate_p95_and_correction_effect(self) -> None:
        store = AgentRuntimeMetricsStore(max_records=30)
        for index in range(1, 21):
            store.record(
                AgentRuntimeMetric(
                    trace_id=f"trace_{index}",
                    session_id="session_metrics",
                    turn_id=f"turn_{index}",
                    agent="EvaluationAgent",
                    version="evaluation-v2.1-phase6-test",
                    run_mode="background",
                    latency_ms=index,
                    success=index % 2 == 0,
                    correction_applied=index in {18, 20},
                    score_delta=5 if index == 20 else 0 if index == 18 else None,
                )
            )

        summary = store.snapshot().summaries[0]
        self.assertEqual(summary.call_count, 20)
        self.assertEqual(summary.success_rate, 0.5)
        self.assertEqual(summary.p95_latency_ms, 19)
        self.assertEqual(summary.correction_count, 2)
        self.assertEqual(summary.correction_improved_count, 1)


if __name__ == "__main__":
    unittest.main()
