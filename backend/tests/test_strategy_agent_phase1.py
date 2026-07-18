from __future__ import annotations

import unittest
import sys
import types
from unittest.mock import AsyncMock, patch

llm_client_stub = types.ModuleType("app.llm.client")
llm_client_stub.generate_structured = AsyncMock()
sys.modules.setdefault("app.llm.client", llm_client_stub)

from app.agents.prompts import (
    STRATEGY_SYSTEM_PROMPT,
    build_strategy_user_prompt,
)
from app.agents.strategy_agent import StrategyAgent
from app.schemas.simulation_state import RelationshipStateV2
from app.schemas.strategy import (
    ResponseAction,
    StrategyMessage,
    TargetInterpretation,
    TargetResponsePolicy,
    TargetResponseStrategyRequest,
    ToneProfile,
)
from evaluation.fixtures import (
    persona_a_direct_advisor,
    persona_b_gentle_avoidant_friend,
)


def request(
    *,
    persona=None,
    relationship_state: RelationshipStateV2 | None = None,
) -> TargetResponseStrategyRequest:
    persona = persona or persona_a_direct_advisor()
    return TargetResponseStrategyRequest(
        trace_id="trace_phase1",
        session_id="session_phase1",
        turn_id="turn_phase1",
        scenario="advisor",
        user_goal="请导师确认材料",
        persona_snapshot=persona,
        relationship_state=relationship_state
        or RelationshipStateV2(
            trust=0.6,
            respect=0.75,
            warmth=0.4,
            patience=0.45,
            psychological_safety=0.55,
            willingness_to_engage=0.65,
        ),
        recent_messages=[
            StrategyMessage(role="target", content="今天先把已有材料发我。")
        ],
        user_message="老师，我都说了会处理，您不要一直问了。",
    )


def policy(
    *,
    action: ResponseAction = ResponseAction.SET_BOUNDARY,
    goal: str = "确认用户自行处理，并要求其承担后续结果。",
    stance: str = "不满但保持克制。",
    confidence: float = 0.85,
    persona_refs: list[str] | None = None,
    memory_refs: list[str] | None = None,
) -> TargetResponsePolicy:
    return TargetResponsePolicy(
        policy_id="policy_turn_phase1",
        interpretation=TargetInterpretation(
            perceived_intent="用户希望停止被追问并自行处理。",
            perceived_tone="防御且略带否定。",
            salient_point="用户否定继续介入的必要性。",
            perceived_concern="后续结果和责任可能不清晰。",
        ),
        action=action,
        response_goal=goal,
        stance=stance,
        required_content=["接受用户自行处理的选择", "要求后续反馈结果"],
        forbidden_content=["长篇安慰", "继续追问大量细节"],
        tone_profile=ToneProfile(
            warmth=22,
            directness=84,
            formality=72,
            emotional_intensity=40,
            length="short",
        ),
        persona_evidence_refs=(
            persona_refs if persona_refs is not None else ["persona_rule_03"]
        ),
        memory_evidence_refs=(
            memory_refs if memory_refs is not None else []
        ),
        confidence=confidence,
        uncertainty_notes=[],
    )


class StrategySchemaPhase1Tests(unittest.TestCase):
    def test_schema_contains_only_target_response_policy_fields(self) -> None:
        fields = set(TargetResponsePolicy.model_fields)
        self.assertEqual(
            fields,
            {
                "policy_id",
                "interpretation",
                "action",
                "response_goal",
                "stance",
                "required_content",
                "forbidden_content",
                "tone_profile",
                "persona_evidence_refs",
                "memory_evidence_refs",
                "confidence",
                "uncertainty_notes",
            },
        )
        self.assertTrue(
            {
                "next_move",
                "recommended_tone",
                "candidate_message",
                "alternative_messages",
                "focus_points",
                "avoid",
                "risk_reminders",
            }.isdisjoint(fields)
        )

    def test_schema_accepts_all_twelve_target_actions(self) -> None:
        self.assertEqual(len(ResponseAction), 12)
        for action in ResponseAction:
            self.assertEqual(policy(action=action).action, action)

    def test_request_limits_context_to_six_recent_messages(self) -> None:
        payload = request().model_dump()
        payload["recent_messages"] = [
            {"role": "user", "content": str(index)} for index in range(7)
        ]
        with self.assertRaises(ValueError):
            TargetResponseStrategyRequest.model_validate(payload)


class StrategyAgentPhase1Tests(unittest.IsolatedAsyncioTestCase):
    async def test_run_uses_v2_policy_in_shadow_mode(self) -> None:
        expected = policy()
        req = request()
        with patch(
            "app.agents.strategy_agent.generate_structured",
            new=AsyncMock(return_value=expected),
        ) as mocked:
            result = await StrategyAgent().run(req)

        self.assertEqual(StrategyAgent().mode, "shadow")
        self.assertEqual(result.action, ResponseAction.SET_BOUNDARY)
        kwargs = mocked.await_args.kwargs
        self.assertIs(kwargs["output_model"], TargetResponsePolicy)
        self.assertEqual(kwargs["temperature"], 0.2)
        self.assertNotIn("candidate_message", kwargs["user_prompt"])

    async def test_same_message_can_produce_different_persona_policies(self) -> None:
        direct = policy(
            action=ResponseAction.SET_BOUNDARY,
            goal="要求用户对结果负责。",
        )
        gentle = policy(
            action=ResponseAction.DEFER,
            goal="暂缓冲突并保留之后回应的空间。",
        )
        agent = StrategyAgent()

        with patch(
            "app.agents.strategy_agent.generate_structured",
            new=AsyncMock(side_effect=[direct, gentle]),
        ):
            result_a = await agent.run(request(persona=persona_a_direct_advisor()))
            result_b = await agent.run(
                request(persona=persona_b_gentle_avoidant_friend())
            )

        self.assertNotEqual(result_a.action, result_b.action)
        self.assertNotEqual(result_a.response_goal, result_b.response_goal)

    def test_relationship_state_is_present_in_prompt(self) -> None:
        high = request(
            relationship_state=RelationshipStateV2(trust=0.9, warmth=0.8)
        )
        low = request(
            relationship_state=RelationshipStateV2(trust=0.2, warmth=0.2)
        )
        self.assertNotEqual(
            build_strategy_user_prompt(high),
            build_strategy_user_prompt(low),
        )
        self.assertIn('"trust": 0.9', build_strategy_user_prompt(high))
        self.assertIn('"trust": 0.2', build_strategy_user_prompt(low))

    def test_coach_advice_is_removed_from_internal_policy(self) -> None:
        leaked = policy(
            goal="你可以这样说：老师我会处理。",
            stance="建议用户下一句更温和。",
        )
        leaked.required_content = ["候选话术：我知道了"]
        processed = StrategyAgent().post_process(result=leaked, request=request())
        serialized = processed.model_dump_json()

        self.assertNotIn("你可以这样说", serialized)
        self.assertNotIn("建议用户", serialized)
        self.assertNotIn("候选话术", serialized)
        self.assertTrue(processed.required_content)

    def test_missing_persona_evidence_gets_traceable_fallback(self) -> None:
        result = policy(persona_refs=[])
        processed = StrategyAgent().post_process(result=result, request=request())
        self.assertEqual(
            processed.persona_evidence_refs,
            ["persona_snapshot:eval_persona_a"],
        )
        self.assertTrue(processed.uncertainty_notes)

    def test_extreme_actions_need_high_confidence_and_two_evidence_sources(self) -> None:
        req = request()
        low_grounding = policy(
            action=ResponseAction.END_CONVERSATION,
            confidence=0.95,
            persona_refs=["persona_rule_03"],
            memory_refs=[],
        )
        downgraded = StrategyAgent().post_process(
            result=low_grounding,
            request=req,
        )
        self.assertEqual(downgraded.action, ResponseAction.SET_BOUNDARY)

        grounded = policy(
            action=ResponseAction.END_CONVERSATION,
            confidence=0.9,
            persona_refs=["persona_snapshot:eval_persona_a"],
            memory_refs=["memory_event_12"],
        )
        req_with_memory_payload = req.model_dump()
        req_with_memory_payload["session_memory"] = {
            "conversation_summary": "用户已经连续施压。",
            "user_strategy_pattern": ["连续施压"],
            "target_sensitive_points": ["不尊重边界"],
            "resolved_points": [],
            "unresolved_points": ["边界冲突"],
            "important_events": ["目标人物已要求停止"],
            "next_suggested_focus": "边界",
            "memory_items": [
                {
                    "memory_id": "memory_event_12",
                    "category": "important_event",
                    "content": "目标人物已要求用户停止施压。",
                    "importance": 5,
                    "confidence": "high"
                }
            ],
        }
        req_with_memory = TargetResponseStrategyRequest.model_validate(
            req_with_memory_payload
        )
        kept = StrategyAgent().post_process(
            result=grounded,
            request=req_with_memory,
        )
        self.assertEqual(kept.action, ResponseAction.END_CONVERSATION)

    def test_prompt_forbids_final_reply_and_user_advice(self) -> None:
        self.assertIn("不负责", STRATEGY_SYSTEM_PROMPT)
        self.assertIn("给用户推荐下一句话", STRATEGY_SYSTEM_PROMPT)
        self.assertIn("生成目标人物最终回复", STRATEGY_SYSTEM_PROMPT)
        self.assertIn("证据规则", STRATEGY_SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
