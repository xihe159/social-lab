from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from pydantic import BaseModel


llm_client_stub = types.ModuleType("app.llm.client")
llm_client_stub.generate_structured = AsyncMock()
sys.modules.setdefault("app.llm.client", llm_client_stub)

from app.agents.simulation.consistency_evaluator import ConsistencyEvaluator
from app.agents.simulation.decision_engine import (
    TurnDecisionEngine,
    apply_simulation_state_delta,
)
from app.agents.simulation.response_generator import ResponseGenerator
from app.agents.simulation_agent_v2 import SimulationAgentV2
from app.llm.structured_output import (
    StructuredOutputRepairError,
    validate_with_single_repair,
)
from app.schemas.common import RelationshipState
from app.schemas.persona import Persona
from app.schemas.session import SessionMessageRequest
from app.schemas.simulation_decision import (
    BehaviorSignals,
    ResponsePolicy,
    SimulationStateDelta,
    TurnAnalysis,
    TurnDecisionInput,
    TurnDecisionOutput,
    TurnDecisionResult,
)
from app.schemas.simulation_generation import GeneratedResponse, ResponseGenerationInput
from app.schemas.simulation_state import ConversationState, RelationshipStateV2, SimulationState
from app.services.chat_record_analyzer import ChatRecordAnalyzer
from app.services.evidence_retriever import EvidenceRetriever
from app.services.evidence_store import EvidenceStore, EpisodeStore, PersonaEvidenceRepository
from app.services.simulation_state_service import create_initial_simulation_state
from app.services.simulation_turn_store import SimulationTurnStore
from evaluation.fixtures import REAL_CHAT_FIXTURE, fixed_personas


def signals(*, polite: bool) -> BehaviorSignals:
    return BehaviorSignals(
        politeness=0.9 if polite else 0.1,
        clarity=0.8,
        accountability=0.8 if polite else 0.1,
        pressure=0.1 if polite else 0.85,
        blame=0.0 if polite else 0.8,
        vulnerability=0.2,
        boundary_violation=0.0 if polite else 0.65,
        honesty_signal=0.8 if polite else 0.4,
    )


def decision(
    *,
    action: str,
    polite: bool = True,
    trust: float = 0.02,
    conflict: float = 0.0,
    reply_length: str = "short",
) -> TurnDecisionOutput:
    return TurnDecisionOutput(
        turn_analysis=TurnAnalysis(
            intent="request" if polite else "pressuring_request",
            behavior_signals=signals(polite=polite),
            detected_events=[],
        ),
        state_delta=SimulationStateDelta(
            trust=trust,
            respect=trust,
            warmth=trust,
            patience=trust,
            psychological_safety=trust,
            willingness_to_engage=trust,
            irritation=-trust,
            hurt=0,
            anxiety=0,
            defensiveness=-trust,
            fatigue=0,
            conflict_level=conflict,
            topic_resolution=0.05 if polite else -0.05,
            boundary_pressure=0 if polite else 0.1,
        ),
        response_policy=ResponsePolicy(
            action=action,
            content_goals=["回应当前表达"],
            tone="direct" if not polite else "neutral",
            reply_length=reply_length,
            must_avoid=[],
        ),
        confidence=0.85,
    )


def legacy_persona() -> Persona:
    return Persona(
        title="强势、直接、责任导向导师",
        style="直接、简洁、正式",
        speed="正常",
        focus="材料和责任",
        risk="反复拖延",
        strategy="说明事实并承担责任",
        state=RelationshipState(
            trust=60,
            respect=75,
            familiarity=45,
            affinity=45,
            authority=80,
            emotional=10,
        ),
    )


def request(persona_v2=None, *, user_message: str = "老师您好，能否请您看一下材料？"):
    persona_v2 = persona_v2 or fixed_personas()[0]
    return SessionMessageRequest(
        scenario="advisor",
        goal="请导师确认材料",
        outcome="获得明确回复",
        role="导师",
        relation="师生关系",
        persona=legacy_persona(),
        persona_v2=persona_v2,
        messages=[],
        user_message=user_message,
        persona_id=persona_v2.persona_id,
        session_id="eval_session",
    )


class Phase8EvaluationSetTests(unittest.IsolatedAsyncioTestCase):
    async def test_1_counterfactual_user_changes_delta_action_and_reply(self) -> None:
        persona = fixed_personas()[0]
        state = create_initial_simulation_state(persona, session_id="eval_user")
        polite_output = decision(action="REPLY_BRIEF", polite=True, trust=0.05)
        rude_output = decision(action="CONFRONT", polite=False, trust=-0.12, conflict=0.12)
        engine = TurnDecisionEngine()

        with patch(
            "app.agents.simulation.decision_engine.generate_structured",
            new=AsyncMock(side_effect=[polite_output, rude_output]),
        ):
            polite = await engine.run(
                TurnDecisionInput(
                    persona=persona,
                    current_state=state,
                    scenario="advisor",
                    goal="延期",
                    user_message="老师您好，我会承担责任，能否延期一天？",
                )
            )
            rude = await engine.run(
                TurnDecisionInput(
                    persona=persona,
                    current_state=state,
                    scenario="advisor",
                    goal="延期",
                    user_message="你必须给我延期，别问那么多。",
                )
            )

        renderer = ResponseGenerator()
        polite_reply = renderer.post_process(
            generated=GeneratedResponse(
                response_text="可以，把现有材料和补齐时间发来。",
                response_action="REPLY_BRIEF",
            ),
            request=_generation_input(persona, polite),
        )
        rude_reply = renderer.post_process(
            generated=GeneratedResponse(
                response_text="你的表达方式不合适。先把情况说清楚。",
                response_action="CONFRONT",
            ),
            request=_generation_input(persona, rude),
        )

        self.assertNotEqual(polite.decision.response_policy.action, rude.decision.response_policy.action)
        self.assertGreater(polite.decision.state_delta.trust, rude.decision.state_delta.trust)
        self.assertNotEqual(polite_reply.response_text, rude_reply.response_text)

    def test_2_counterfactual_personas_have_distinct_behavior_signatures(self) -> None:
        persona_a, persona_b, persona_c = fixed_personas()
        signatures = {
            (
                item.communication_style.average_reply_length,
                round(item.stable_traits.directness, 2),
                round(item.stable_traits.conflict_avoidance, 2),
                round(item.stable_traits.sensitivity_to_rejection, 2),
            )
            for item in (persona_a, persona_b, persona_c)
        }
        expected_actions = {
            persona_a.persona_id: "CONFRONT",
            persona_b.persona_id: "DEFER_REPLY",
            persona_c.persona_id: "ASK_CLARIFICATION",
        }

        self.assertEqual(len(signatures), 3)
        self.assertEqual(len(set(expected_actions.values())), 3)
        self.assertGreater(persona_a.stable_traits.directness, persona_b.stable_traits.directness)
        self.assertGreater(
            persona_c.stable_traits.sensitivity_to_rejection,
            persona_a.stable_traits.sensitivity_to_rejection,
        )

    def test_3_longitudinal_state_changes_continuously_without_reset(self) -> None:
        persona = fixed_personas()[0]
        state = create_initial_simulation_state(persona, session_id="eval_longitudinal")
        positive = _delta(trust=0.04, warmth=0.03, irritation=-0.02)
        pressure = _delta(trust=-0.06, warmth=-0.05, irritation=0.08, conflict=0.08)
        apology = _delta(trust=0.04, warmth=0.04, irritation=-0.06, conflict=-0.04)

        snapshots = [state]
        for delta in [positive] * 3 + [pressure] * 3 + [apology]:
            state = apply_simulation_state_delta(state=state, delta=delta)
            snapshots.append(state)

        self.assertEqual(state.conversation_state.turn_count, 7)
        self.assertGreater(snapshots[3].relationship_state.trust, snapshots[0].relationship_state.trust)
        self.assertLess(snapshots[6].relationship_state.trust, snapshots[3].relationship_state.trust)
        self.assertGreater(snapshots[7].relationship_state.trust, snapshots[6].relationship_state.trust)
        self.assertLess(snapshots[7].relationship_state.trust, snapshots[3].relationship_state.trust)
        self.assertTrue(all(0 <= item.relationship_state.trust <= 1 for item in snapshots))

    def test_4_chat_evidence_learns_style_patterns_and_retrieves_delay(self) -> None:
        analyzer = ChatRecordAnalyzer()
        analysis = analyzer.analyze(REAL_CHAT_FIXTURE, target_role="导师", relation="师生关系")
        self.assertIsNotNone(analysis)
        assert analysis is not None
        repo = PersonaEvidenceRepository(EpisodeStore(), EvidenceStore())
        repo.register("eval_persona_a", analysis)
        state = SimulationState(session_id="eval_evidence", persona_id="eval_persona_a")
        retrieval = EvidenceRetriever(repo).retrieve(
            persona_id="eval_persona_a",
            user_message="老师，这次可能还是要延期。",
            state=state,
        )

        self.assertEqual(analysis.communication_style.average_reply_length, "short")
        self.assertGreaterEqual(len(analysis.behavior_patterns), 3)
        self.assertTrue(analysis.evidence)
        self.assertEqual(retrieval.items[0].episode_id, "episode_0001")

    def test_5_no_reply_contract_distinguishes_reply_cold_and_silent(self) -> None:
        policies = {
            "normal": ResponsePolicy(
                action="REPLY_NORMAL", content_goals=["回应"], tone="neutral", reply_length="medium", must_avoid=[]
            ),
            "cold": ResponsePolicy(
                action="REPLY_COLD", content_goals=["简短回应"], tone="cold", reply_length="short", must_avoid=[]
            ),
            "silent": ResponsePolicy(
                action="READ_NO_REPLY", content_goals=["不回应"], tone="silent", reply_length="short", must_avoid=[]
            ),
        }
        generator = ResponseGenerator()
        persona = fixed_personas()[0]
        state = create_initial_simulation_state(persona, session_id="eval_no_reply")

        normal = generator.post_process(
            generated=GeneratedResponse(response_text="可以，发来吧。", response_action="REPLY_NORMAL"),
            request=ResponseGenerationInput(
                persona=persona, current_state=state, response_policy=policies["normal"], user_message="请帮忙"
            ),
        )
        cold = generator.post_process(
            generated=GeneratedResponse(response_text="知道了。", response_action="REPLY_COLD"),
            request=ResponseGenerationInput(
                persona=persona, current_state=state, response_policy=policies["cold"], user_message="催促"
            ),
        )
        silent = generator.post_process(
            generated=GeneratedResponse(response_text="不应出现", response_action="READ_NO_REPLY"),
            request=ResponseGenerationInput(
                persona=persona, current_state=state, response_policy=policies["silent"], user_message="越界施压"
            ),
        )

        self.assertTrue(normal.response_text)
        self.assertEqual(cold.response_action, "REPLY_COLD")
        self.assertEqual(silent.response_text, "")

    def test_6_mild_rudeness_cannot_collapse_relationship(self) -> None:
        persona = fixed_personas()[0]
        state = create_initial_simulation_state(persona, session_id="eval_overreaction")
        raw = decision(action="END_CONVERSATION", polite=False, trust=-0.8, conflict=0.8)
        processed = TurnDecisionEngine().post_process(decision=raw, current_state=state)
        trigger = ConsistencyEvaluator().should_run(
            persona=persona,
            previous_state=state,
            decision_result=processed,
            generated=GeneratedResponse(
                response_text="这件事到这里。",
                response_action="END_CONVERSATION",
            ),
            relevant_evidence=[],
        )

        self.assertEqual(processed.decision.state_delta.trust, -0.15)
        self.assertGreater(processed.updated_state.relationship_state.trust, 0)
        self.assertTrue(trigger.triggered)
        self.assertIn("potential_overreaction", trigger.reasons)


class Phase8ReliabilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_json_repair_runs_exactly_once(self) -> None:
        class Payload(BaseModel):
            value: int

        repair = AsyncMock(return_value='{"value": 7}')
        result = await validate_with_single_repair(
            content='{"value": "invalid"}',
            output_model=Payload,
            repair=repair,
        )
        self.assertEqual(result.value, 7)
        repair.assert_awaited_once()

        failed_repair = AsyncMock(return_value='{"value": "still invalid"}')
        with self.assertRaises(StructuredOutputRepairError):
            await validate_with_single_repair(
                content="not json",
                output_model=Payload,
                repair=failed_repair,
            )
        failed_repair.assert_awaited_once()

    async def test_decision_failure_uses_previous_state_and_records_private_metadata(self) -> None:
        persona = fixed_personas()[0]
        req = request(persona, user_message="这是不能写入存储的敏感原文。")
        decision_engine = AsyncMock()
        decision_engine.run.side_effect = RuntimeError("decision unavailable")
        generator = AsyncMock()
        generator.run.return_value = GeneratedResponse(
            response_text="我知道了，你继续说。",
            response_action="REPLY_NORMAL",
        )
        store = SimulationTurnStore(max_records=10)

        with self.assertLogs("app.agents.simulation_agent_v2", level="ERROR"):
            response = await SimulationAgentV2(
                decision_engine=decision_engine,
                response_generator=generator,
                turn_store=store,
            ).run(req)

        self.assertTrue(response.runtime_meta.decision_fallback_used)
        self.assertEqual(response.simulation_state.conversation_state.turn_count, 0)
        self.assertEqual(response.response.action, "REPLY_NORMAL")
        records = store.list_for_session("eval_session")
        self.assertEqual(len(records), 1)
        serialized = records[0].model_dump_json()
        self.assertNotIn(req.user_message, serialized)
        self.assertNotIn(response.response.text, serialized)
        self.assertEqual(len(records[0].user_message_digest), 64)

    async def test_generator_retries_once_then_uses_action_aligned_fallback(self) -> None:
        persona = fixed_personas()[0]
        req = request(persona)
        state = create_initial_simulation_state(persona, session_id="eval_session")
        output = decision(action="REPLY_BRIEF", polite=True)
        result = TurnDecisionEngine().post_process(decision=output, current_state=state)
        decision_engine = AsyncMock()
        decision_engine.run.return_value = result
        generator = AsyncMock(side_effect=RuntimeError("unused"))
        generator.run = AsyncMock(side_effect=[RuntimeError("first"), RuntimeError("second")])

        with self.assertLogs("app.agents.simulation_agent_v2", level="ERROR"):
            response = await SimulationAgentV2(
                decision_engine=decision_engine,
                response_generator=generator,
                turn_store=SimulationTurnStore(max_records=10),
            ).run(req)

        self.assertEqual(generator.run.await_count, 2)
        self.assertEqual(response.runtime_meta.generator_retry_count, 1)
        self.assertTrue(response.runtime_meta.generator_fallback_used)
        self.assertEqual(response.response.action, "REPLY_BRIEF")
        self.assertEqual(response.response.text, "知道了。")

    def test_quality_baseline_declares_all_prd_dimensions_and_release_gates(self) -> None:
        path = Path(__file__).parents[1] / "evaluation" / "quality_baseline.json"
        baseline = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(baseline["fixed_personas"]), 3)
        self.assertEqual(len(baseline["required_regression_suites"]), 6)
        self.assertEqual(len(baseline["quality_dimensions"]), 8)
        self.assertEqual(baseline["offline_release_gates"]["max_normal_llm_calls"], 2)
        self.assertFalse(baseline["offline_release_gates"]["raw_sensitive_text_persisted"])


def _generation_input(persona, result: TurnDecisionResult) -> ResponseGenerationInput:
    return ResponseGenerationInput(
        persona=persona,
        current_state=result.updated_state,
        response_policy=result.decision.response_policy,
        user_message="test",
    )


def _delta(
    *,
    trust: float,
    warmth: float,
    irritation: float,
    conflict: float = 0,
) -> SimulationStateDelta:
    return SimulationStateDelta(
        trust=trust,
        respect=0,
        warmth=warmth,
        patience=0,
        psychological_safety=0,
        willingness_to_engage=0,
        irritation=irritation,
        hurt=0,
        anxiety=0,
        defensiveness=0,
        fatigue=0,
        conflict_level=conflict,
        topic_resolution=0,
        boundary_pressure=0,
    )


if __name__ == "__main__":
    unittest.main()
