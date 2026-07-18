from __future__ import annotations

import unittest
import sys
import types
from unittest.mock import AsyncMock, patch

llm_client_stub = types.ModuleType("app.llm.client")
llm_client_stub.generate_structured = AsyncMock()
sys.modules.setdefault("app.llm.client", llm_client_stub)

from app.agents.evaluation_agent import EvaluationAgent
from app.agents.prompts import EVALUATION_SYSTEM_PROMPT, build_evaluation_user_prompt
from app.schemas.evaluation import (
    EvaluationScoreItem,
    EvaluationVerdict,
    FailureAttribution,
    InternalCorrection,
    SimulationEvaluationRequest,
    SimulationEvaluationResponse,
    SimulationEvaluationResult,
)
from app.schemas.memory import SessionMemory
from app.schemas.simulation_state import RelationshipStateV2
from app.schemas.strategy import (
    ResponseAction,
    StrategyMessage,
    TargetInterpretation,
    TargetResponsePolicy,
    ToneProfile,
)
from app.services.simulation_quality import weighted_simulation_score
from evaluation.fixtures import persona_a_direct_advisor


def memory(*, with_evidence: bool = True) -> SessionMemory:
    return SessionMemory(
        conversation_summary="用户正在确认材料截止时间。" if with_evidence else "",
        user_strategy_pattern=[],
        target_sensitive_points=["材料不完整"] if with_evidence else [],
        resolved_points=[],
        unresolved_points=["材料截止时间"] if with_evidence else [],
        important_events=["导师要求先提交已有材料"] if with_evidence else [],
        next_suggested_focus="确认时间" if with_evidence else "",
    )


def policy() -> TargetResponsePolicy:
    return TargetResponsePolicy(
        policy_id="policy_phase3",
        interpretation=TargetInterpretation(
            perceived_intent="用户希望确认是否能延后提交。",
            perceived_tone="礼貌但有压力。",
            salient_point="用户尚未准备完整材料。",
            perceived_concern="错过截止时间。",
        ),
        action=ResponseAction.ACCEPT_WITH_CONDITION,
        response_goal="允许延后，但要求先提交已有材料。",
        stance="直接且克制。",
        required_content=["先提交已有材料", "给出明确时间"],
        forbidden_content=["无条件接受", "长篇安慰"],
        tone_profile=ToneProfile(
            warmth=35,
            directness=85,
            formality=80,
            emotional_intensity=20,
            length="short",
        ),
        persona_evidence_refs=["persona_snapshot:eval_persona_a"],
        memory_evidence_refs=["导师要求先提交已有材料"],
        confidence=0.86,
        uncertainty_notes=[],
    )


def request(
    *,
    chat_record_available: bool = True,
    context_evidence: bool = True,
) -> SimulationEvaluationRequest:
    persona = persona_a_direct_advisor()
    persona.evidence_summary.chat_record_available = chat_record_available
    persona.evidence_summary.evidence_count = 8 if context_evidence else 0
    persona.evidence_summary.overall_confidence = 0.9 if context_evidence else 0.35
    return SimulationEvaluationRequest(
        trace_id="trace_phase3",
        session_id="session_phase3",
        turn_id="turn_phase3",
        persona_snapshot=persona,
        relationship_state_before=RelationshipStateV2(
            trust=0.6,
            respect=0.75,
            warmth=0.4,
            patience=0.45,
        ),
        session_memory=memory(with_evidence=context_evidence),
        recent_messages=[
            StrategyMessage(role="target", content="先把已有材料发我。")
        ],
        user_message="老师，我能晚一天交吗？",
        response_policy=policy(),
        simulation_result=SimulationEvaluationResult(
            reply="可以，今天先把已有材料发我，明天中午前补齐。",
            attitude="有条件接受",
            emotion="克制",
            perceived_user_tone="礼貌但焦虑",
            state_delta={"trust": 0.0, "patience": -0.02},
            risk_flags=[],
            policy_id="policy_phase3",
            used_evidence_refs=["persona_snapshot:eval_persona_a"],
        ),
        strategy_prompt_version="strategy-v2.0-phase1",
        simulation_prompt_version="simulation-v2.0-phase2",
        evaluation_prompt_version="evaluation-v2.0-phase3",
    )


def response(
    *,
    scores: dict[str, int] | None = None,
    confidence: float = 0.9,
    attribution: FailureAttribution = FailureAttribution.NONE,
    critical_issues: list[str] | None = None,
    strategy_correction: InternalCorrection | None = None,
    simulation_correction: InternalCorrection | None = None,
) -> SimulationEvaluationResponse:
    values = {
        "persona_fidelity": 90,
        "dyadic_consistency": 90,
        "state_continuity": 90,
        "strategy_adherence": 90,
        "reaction_plausibility": 90,
        "style_fidelity": 90,
        "evidence_grounding": 90,
    }
    values.update(scores or {})

    def item(dimension: str) -> EvaluationScoreItem:
        return EvaluationScoreItem(
            score=values[dimension],
            reason=f"{dimension} reason",
            evidence=[f"{dimension} evidence"],
        )

    return SimulationEvaluationResponse(
        evaluation_id="evaluation_phase3",
        simulation_success_score=1,
        confidence=confidence,
        verdict=EvaluationVerdict.ACCEPT,
        failure_attribution=attribution,
        persona_fidelity=item("persona_fidelity"),
        dyadic_consistency=item("dyadic_consistency"),
        state_continuity=item("state_continuity"),
        strategy_adherence=item("strategy_adherence"),
        reaction_plausibility=item("reaction_plausibility"),
        style_fidelity=item("style_fidelity"),
        evidence_grounding=item("evidence_grounding"),
        critical_issues=critical_issues or [],
        correction_for_strategy=strategy_correction,
        correction_for_simulation=simulation_correction,
        session_learning_signals=[],
        evaluator_notes=[],
    )


class EvaluationSchemaPhase3Tests(unittest.TestCase):
    def test_v2_schema_has_only_simulation_quality_dimensions(self) -> None:
        fields = set(SimulationEvaluationResponse.model_fields)
        self.assertTrue(
            {
                "persona_fidelity",
                "dyadic_consistency",
                "state_continuity",
                "strategy_adherence",
                "reaction_plausibility",
                "style_fidelity",
                "evidence_grounding",
            }.issubset(fields)
        )
        self.assertTrue(
            {
                "pedagogical_value",
                "responsiveness",
                "suggested_fixes",
                "major_problems",
                "debug_notes",
            }.isdisjoint(fields)
        )

    def test_request_carries_policy_result_and_prompt_versions(self) -> None:
        req = request()
        self.assertEqual(req.response_policy.policy_id, "policy_phase3")
        self.assertEqual(req.simulation_result.policy_id, "policy_phase3")
        self.assertEqual(req.evaluation_prompt_version, "evaluation-v2.0-phase3")

    def test_base_weighted_score_is_not_simple_average(self) -> None:
        scores = {
            "persona_fidelity": 90,
            "dyadic_consistency": 80,
            "state_continuity": 70,
            "strategy_adherence": 60,
            "reaction_plausibility": 50,
            "style_fidelity": 40,
            "evidence_grounding": 30,
        }
        self.assertEqual(
            weighted_simulation_score(scores, chat_record_available=True),
            64,
        )
        self.assertNotEqual(round(sum(scores.values()) / len(scores)), 64)


class EvaluationAgentPhase3Tests(unittest.IsolatedAsyncioTestCase):
    async def test_run_uses_v2_output_and_low_temperature(self) -> None:
        expected = response()
        req = request()
        with patch(
            "app.agents.evaluation_agent.generate_structured",
            new=AsyncMock(return_value=expected),
        ) as mocked:
            result = await EvaluationAgent().run(req)

        self.assertEqual(result.simulation_success_score, 90)
        kwargs = mocked.await_args.kwargs
        self.assertIs(kwargs["output_model"], SimulationEvaluationResponse)
        self.assertEqual(kwargs["temperature"], 0.1)

    def test_no_chat_record_reduces_weights_and_confidence(self) -> None:
        scores = {
            "persona_fidelity": 90,
            "dyadic_consistency": 80,
            "state_continuity": 70,
            "strategy_adherence": 60,
            "reaction_plausibility": 50,
            "style_fidelity": 40,
            "evidence_grounding": 30,
        }
        result = EvaluationAgent().post_process(
            result=response(scores=scores, confidence=0.95),
            request=request(chat_record_available=False, context_evidence=True),
        )
        self.assertEqual(result.simulation_success_score, 68)
        self.assertEqual(result.confidence, 0.69)
        self.assertTrue(any("已降权" in note for note in result.evaluator_notes))

    def test_context_gap_returns_insufficient_evidence_without_corrections(self) -> None:
        result = EvaluationAgent().post_process(
            result=response(
                confidence=0.9,
                strategy_correction=InternalCorrection(
                    keep=[], change=["改策略"], must_not=[]
                ),
            ),
            request=request(chat_record_available=False, context_evidence=False),
        )
        self.assertEqual(result.confidence, 0.59)
        self.assertEqual(result.verdict, EvaluationVerdict.INSUFFICIENT_EVIDENCE)
        self.assertEqual(result.failure_attribution, FailureAttribution.CONTEXT_GAP)
        self.assertIsNone(result.correction_for_strategy)
        self.assertIsNone(result.correction_for_simulation)

    def test_persona_hard_limit_blocks_accept(self) -> None:
        result = EvaluationAgent().post_process(
            result=response(scores={"persona_fidelity": 59}),
            request=request(),
        )
        self.assertNotIn(
            result.verdict,
            {EvaluationVerdict.ACCEPT, EvaluationVerdict.ACCEPT_WITH_FEEDBACK},
        )

    def test_strategy_adherence_hard_limit_forces_revision(self) -> None:
        result = EvaluationAgent().post_process(
            result=response(scores={"strategy_adherence": 54}),
            request=request(),
        )
        self.assertEqual(result.verdict, EvaluationVerdict.REVISE_SIMULATION)
        self.assertEqual(
            result.failure_attribution,
            FailureAttribution.SIMULATION_EXECUTION_ERROR,
        )
        self.assertIsNotNone(result.correction_for_simulation)
        self.assertIsNone(result.correction_for_strategy)

    def test_policy_id_mismatch_cannot_pass_strategy_adherence(self) -> None:
        req = request()
        req.simulation_result.policy_id = "policy_from_previous_turn"
        result = EvaluationAgent().post_process(
            result=response(),
            request=req,
        )
        self.assertEqual(result.strategy_adherence.score, 0)
        self.assertEqual(result.verdict, EvaluationVerdict.REVISE_SIMULATION)
        self.assertTrue(
            any("POLICY_ID_MISMATCH" in issue for issue in result.critical_issues)
        )

    def test_invented_persona_trait_caps_score_and_replans(self) -> None:
        result = EvaluationAgent().post_process(
            result=response(
                critical_issues=[
                    "INVENTED_PERSONA_TRAIT: 回复声称人物喜欢每天视频，但输入无此证据。"
                ]
            ),
            request=request(),
        )
        self.assertEqual(result.simulation_success_score, 59)
        self.assertEqual(result.verdict, EvaluationVerdict.REPLAN_AND_REGENERATE)

    def test_strategy_error_routes_only_strategy_correction(self) -> None:
        result = EvaluationAgent().post_process(
            result=response(
                scores={"persona_fidelity": 55},
                attribution=FailureAttribution.STRATEGY_ERROR,
                simulation_correction=InternalCorrection(
                    keep=[], change=["改措辞"], must_not=[]
                ),
            ),
            request=request(),
        )
        self.assertEqual(result.verdict, EvaluationVerdict.REPLAN_AND_REGENERATE)
        self.assertIsNotNone(result.correction_for_strategy)
        self.assertIsNone(result.correction_for_simulation)

    def test_coach_language_is_removed_from_internal_learning_signals(self) -> None:
        raw = response()
        raw.session_learning_signals = [
            "回复总是过长",
            "你可以这样说：请再考虑一下",
        ]
        result = EvaluationAgent().post_process(result=raw, request=request())
        self.assertEqual(result.session_learning_signals, ["回复总是过长"])

    def test_prompt_keeps_evaluation_out_of_coach_and_simulation_roles(self) -> None:
        prompt = build_evaluation_user_prompt(request())
        self.assertIn("evaluation-v2.0-phase3", prompt)
        self.assertIn("不充当 CoachAgent", EVALUATION_SYSTEM_PROMPT)
        self.assertIn("不生成或改写目标人物最终回复", EVALUATION_SYSTEM_PROMPT)
        self.assertNotIn("pedagogical_value", prompt)


if __name__ == "__main__":
    unittest.main()
