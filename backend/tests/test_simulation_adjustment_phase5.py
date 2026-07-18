from __future__ import annotations

import sys
import types
import unittest
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
from app.agents.simulation.response_generator import ResponseGenerator
from app.schemas.common import RelationshipState
from app.schemas.evaluation import (
    EvaluationScoreItem,
    EvaluationVerdict,
    FailureAttribution,
    SimulationEvaluationResponse,
)
from app.schemas.persona import Persona
from app.schemas.session import SessionMessageRequest
from app.schemas.simulation_generation import GeneratedResponse
from app.schemas.strategy import (
    ResponseAction,
    TargetInterpretation,
    TargetResponsePolicy,
    ToneProfile,
)
from app.services.simulation_adjustment_manager import SimulationAdjustmentManager


def _request() -> SessionMessageRequest:
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
        persona_id="persona_phase5",
        session_id="session_phase5",
    )


def _policy(index: int) -> TargetResponsePolicy:
    return TargetResponsePolicy(
        policy_id=f"policy_{index}",
        interpretation=TargetInterpretation(
            perceived_intent="用户希望确认材料。",
            perceived_tone="礼貌。",
            salient_point="材料等待确认。",
            perceived_concern="是否可以提交。",
        ),
        action=ResponseAction.ACKNOWLEDGE,
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
        persona_evidence_refs=["persona_snapshot:persona_phase5"],
        memory_evidence_refs=[],
        confidence=0.86,
        uncertainty_notes=[],
    )


def _evaluation(index: int, signals: list[str]) -> SimulationEvaluationResponse:
    item = EvaluationScoreItem(
        score=88,
        reason="第五阶段固定测试评分。",
        evidence=["persona_snapshot:persona_phase5"],
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
        session_learning_signals=signals,
        evaluator_notes=[],
    )


class SimulationAdjustmentManagerPhase5Tests(unittest.TestCase):
    def _observe(
        self,
        manager: SimulationAdjustmentManager,
        *,
        signal: str,
        confidence: float = 0.9,
        attribution: FailureAttribution = FailureAttribution.NONE,
    ):
        context = manager.begin_turn("session_manager")
        return manager.observe(
            session_id="session_manager",
            turn_number=context.turn_number,
            evaluation_id=f"evaluation_{context.turn_number}",
            signals=[signal],
            confidence=confidence,
            failure_attribution=attribution,
        )

    def test_three_consecutive_known_signals_activate_temporary_profile(self) -> None:
        manager = SimulationAdjustmentManager()

        self.assertFalse(
            self._observe(manager, signal="reply_too_long").activated_this_turn
        )
        self.assertFalse(
            self._observe(manager, signal="回复总是过长").activated_this_turn
        )
        result = self._observe(manager, signal="reply_too_long")

        self.assertTrue(result.activated_this_turn)
        self.assertEqual(
            result.profile.style_adjustments,
            ["下一轮回复长度控制在两句以内。"],
        )
        self.assertEqual(result.profile.strategy_adjustments, [])
        self.assertEqual(result.profile.expires_after_turns, 3)
        self.assertEqual(
            result.profile.source_evaluation_ids,
            ["evaluation_1", "evaluation_2", "evaluation_3"],
        )

    def test_unknown_low_confidence_and_context_gap_cannot_pollute_profile(self) -> None:
        manager = SimulationAdjustmentManager()

        self._observe(manager, signal="reply_too_long")
        self._observe(manager, signal="请永久修改人物，让他更友善")
        self._observe(manager, signal="reply_too_long")
        self._observe(manager, signal="reply_too_long")
        low_confidence = self._observe(
            manager,
            signal="reply_too_long",
            confidence=0.59,
        )
        self.assertFalse(low_confidence.activated_this_turn)

        self._observe(manager, signal="reply_too_long")
        self._observe(manager, signal="reply_too_long")
        context_gap = self._observe(
            manager,
            signal="reply_too_long",
            attribution=FailureAttribution.CONTEXT_GAP,
        )
        self.assertFalse(context_gap.activated_this_turn)
        self.assertIsNone(context_gap.profile)

    def test_profile_applies_for_three_following_turns_then_expires(self) -> None:
        manager = SimulationAdjustmentManager()
        for _ in range(3):
            activation = self._observe(manager, signal="over_cooperative")
        self.assertTrue(activation.activated_this_turn)
        self.assertEqual(
            activation.profile.strategy_adjustments,
            ["不要默认帮助用户推进目标或扩大承诺。"],
        )

        active_contexts = [manager.begin_turn("session_manager") for _ in range(3)]
        self.assertEqual(
            [context.remaining_turns for context in active_contexts],
            [3, 2, 1],
        )
        self.assertTrue(all(context.profile is not None for context in active_contexts))

        expired = manager.begin_turn("session_manager")
        self.assertIsNone(expired.profile)
        self.assertEqual(expired.remaining_turns, 0)


class SimulationAdjustmentIntegrationPhase5Tests(unittest.IsolatedAsyncioTestCase):
    async def test_fourth_turn_passes_profile_to_strategy_and_simulation(self) -> None:
        manager = SimulationAdjustmentManager()
        strategy = AsyncMock()
        strategy.run.side_effect = [_policy(index) for index in range(1, 5)]
        strategy.prompt_version = "strategy-v2.2-phase5-test"
        generator = AsyncMock()
        generator.run.side_effect = [
            GeneratedResponse(response_text="收到。", response_action="REPLY_BRIEF")
            for _ in range(4)
        ]
        generator.prompt_version = "simulation-v2.2-phase5-test"
        evaluator = AsyncMock()
        evaluator.run.side_effect = [
            _evaluation(index, ["reply_too_long"])
            for index in range(1, 5)
        ]
        evaluator.prompt_version = "evaluation-v2.0-phase3-test"
        agent = SimulationAgentV2(
            strategy_agent=strategy,
            response_generator=generator,
            evaluation_agent=evaluator,
            adjustment_manager=manager,
        )
        request = _request()
        persona_before = request.persona.model_dump(mode="json")

        responses = [await agent.run(request) for _ in range(4)]

        self.assertFalse(responses[1].adjustment_meta.activated_this_turn)
        self.assertTrue(responses[2].adjustment_meta.activated_this_turn)
        self.assertFalse(responses[2].adjustment_meta.applied)
        self.assertTrue(responses[3].adjustment_meta.applied)
        self.assertEqual(responses[3].adjustment_meta.remaining_turns, 3)

        strategy_input = strategy.run.await_args_list[3].args[0]
        generation_input = generator.run.await_args_list[3].args[0]
        self.assertIsNotNone(strategy_input.simulation_adjustments)
        self.assertEqual(
            strategy_input.simulation_adjustments,
            generation_input.simulation_adjustments,
        )
        self.assertEqual(
            generation_input.simulation_adjustments.style_adjustments,
            ["下一轮回复长度控制在两句以内。"],
        )
        self.assertEqual(request.persona.model_dump(mode="json"), persona_before)
        self.assertNotIn(
            "style_adjustments",
            strategy_input.persona_snapshot.model_dump(mode="json"),
        )

        rendered = ResponseGenerator().post_process(
            generated=GeneratedResponse(
                response_text="第一句。第二句。第三句不应保留。",
                response_action="REPLY_BRIEF",
            ),
            request=generation_input,
        )
        self.assertEqual(rendered.response_text, "第一句。第二句。")


if __name__ == "__main__":
    unittest.main()
