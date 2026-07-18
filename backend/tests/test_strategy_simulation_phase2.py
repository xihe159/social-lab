from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import AsyncMock


llm_client_stub = types.ModuleType("app.llm.client")
llm_client_stub.generate_structured = AsyncMock()
sys.modules.setdefault("app.llm.client", llm_client_stub)

from app.agents.simulation.response_generator import ResponseGenerator
from app.agents.simulation.strategy_policy_adapter import (
    STRATEGY_TO_SIMULATION_ACTION,
    adapt_strategy_policy,
    build_decision_result_from_strategy,
)
from app.schemas.persona_v2 import PersonaModelV2
from app.schemas.simulation_generation import (
    GeneratedResponse,
    ResponseGenerationInput,
)
from app.schemas.simulation_state import SimulationState
from app.schemas.strategy import (
    ResponseAction,
    TargetInterpretation,
    TargetResponsePolicy,
    ToneProfile,
)


def policy(
    action: ResponseAction,
    *,
    length: str = "short",
    perceived_tone: str = "中性、清晰。",
) -> TargetResponsePolicy:
    return TargetResponsePolicy(
        policy_id=f"policy_{action.value}",
        interpretation=TargetInterpretation(
            perceived_intent="用户希望目标人物作出回应。",
            perceived_tone=perceived_tone,
            salient_point="用户提出了当前请求。",
            perceived_concern="需要保持人物立场和边界。",
        ),
        action=action,
        response_goal=f"执行 {action.value} 行为。",
        stance="克制、直接。",
        required_content=["回应当前核心内容"],
        forbidden_content=["替用户制定下一句话"],
        tone_profile=ToneProfile(
            warmth=45,
            directness=70,
            formality=60,
            emotional_intensity=25,
            length=length,
        ),
        persona_evidence_refs=["persona_snapshot:phase2"],
        memory_evidence_refs=[],
        confidence=0.85,
        uncertainty_notes=[],
    )


def generation_input(
    strategy_policy: TargetResponsePolicy,
) -> ResponseGenerationInput:
    simulation_policy = adapt_strategy_policy(strategy_policy)
    return ResponseGenerationInput(
        persona=PersonaModelV2(persona_id="phase2"),
        current_state=SimulationState(
            session_id="session_phase2",
            persona_id="phase2",
        ),
        response_policy=simulation_policy,
        strategy_policy_id=strategy_policy.policy_id,
        strategy_action=strategy_policy.action.value,
        strategy_evidence_refs=strategy_policy.persona_evidence_refs,
        user_message="请回应我。",
    )


class StrategyPolicyAdapterPhase2Tests(unittest.TestCase):
    def test_all_twelve_strategy_actions_have_one_explicit_simulation_mapping(self) -> None:
        self.assertEqual(set(STRATEGY_TO_SIMULATION_ACTION), set(ResponseAction))
        self.assertEqual(len(STRATEGY_TO_SIMULATION_ACTION), 12)
        self.assertEqual(
            STRATEGY_TO_SIMULATION_ACTION[ResponseAction.REFUSE],
            "REPLY_COLD",
        )
        self.assertEqual(
            STRATEGY_TO_SIMULATION_ACTION[ResponseAction.NO_REPLY],
            "READ_NO_REPLY",
        )

    def test_adapter_preserves_goal_boundaries_tone_and_length(self) -> None:
        source = policy(ResponseAction.SET_BOUNDARY, length="very_short")
        result = adapt_strategy_policy(source)
        self.assertEqual(result.action, "SET_BOUNDARY")
        self.assertIn(source.response_goal, result.content_goals)
        self.assertIn(source.required_content[0], result.content_goals)
        self.assertIn(source.forbidden_content[0], result.must_avoid)
        self.assertIn("directness=70", result.tone)
        self.assertEqual(result.reply_length, "short")

    def test_strategy_drives_bounded_continuous_state_without_decision_llm(self) -> None:
        state = SimulationState(session_id="phase2", persona_id="phase2")
        positive = build_decision_result_from_strategy(
            policy=policy(
                ResponseAction.ACCEPT,
                perceived_tone="礼貌、真诚并承担责任。",
            ),
            current_state=state,
        )
        negative = build_decision_result_from_strategy(
            policy=policy(
                ResponseAction.SET_BOUNDARY,
                perceived_tone="不礼貌、连续施压并越界。",
            ),
            current_state=state,
        )

        self.assertGreater(
            positive.decision.state_delta.trust,
            negative.decision.state_delta.trust,
        )
        self.assertEqual(positive.updated_state.conversation_state.turn_count, 1)
        for result in (positive, negative):
            for name in type(result.decision.state_delta).model_fields:
                self.assertLessEqual(abs(getattr(result.decision.state_delta, name)), 0.15)


class PolicyExecutionContractPhase2Tests(unittest.TestCase):
    def test_policy_execution_contract_rate_is_at_least_eighty_five_percent(self) -> None:
        generator = ResponseGenerator()
        checks: list[bool] = []

        refusal = policy(ResponseAction.REFUSE)
        refusal_result = generator.post_process(
            generated=GeneratedResponse(
                response_text="可以，没问题，我答应。",
                response_action="REPLY_NORMAL",
            ),
            request=generation_input(refusal),
        )
        checks.append(
            refusal_result.response_action == "REPLY_COLD"
            and "不能答应" in refusal_result.response_text
        )

        boundary = policy(ResponseAction.SET_BOUNDARY, length="medium")
        boundary_result = generator.post_process(
            generated=GeneratedResponse(
                response_text="我理解你的感受，也非常愿意继续安慰和解释。" * 20,
                response_action="REPLY_NORMAL",
            ),
            request=generation_input(boundary),
        )
        checks.append(
            boundary_result.response_action == "SET_BOUNDARY"
            and len(boundary_result.response_text) <= 100
        )

        clarification = policy(ResponseAction.ASK_CLARIFICATION)
        clarification_result = generator.post_process(
            generated=GeneratedResponse(
                response_text="你具体需要什么？什么时候要？还缺哪些材料？",
                response_action="REPLY_NORMAL",
            ),
            request=generation_input(clarification),
        )
        checks.append(
            sum(
                clarification_result.response_text.count(mark)
                for mark in ("?", "？")
            )
            <= 1
        )

        no_reply = policy(ResponseAction.NO_REPLY)
        no_reply_result = generator.post_process(
            generated=GeneratedResponse(
                response_text="这段文字不应出现。",
                response_action="REPLY_NORMAL",
            ),
            request=generation_input(no_reply),
        )
        checks.append(
            no_reply_result.response_action == "READ_NO_REPLY"
            and no_reply_result.response_text == ""
        )

        short = policy(ResponseAction.ACKNOWLEDGE, length="short")
        short_result = generator.post_process(
            generated=GeneratedResponse(
                response_text="这是一段明显超过简短回复长度要求的内容。" * 20,
                response_action="REPLY_NORMAL",
            ),
            request=generation_input(short),
        )
        checks.append(len(short_result.response_text) <= 60)

        pass_rate = sum(checks) / len(checks)
        self.assertGreaterEqual(pass_rate, 0.85)
        self.assertTrue(all(checks))


if __name__ == "__main__":
    unittest.main()
