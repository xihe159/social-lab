from __future__ import annotations

from hashlib import sha256

from app.agents.prompts import EVALUATION_SYSTEM_PROMPT, build_evaluation_user_prompt
from app.llm.client import generate_structured
from app.schemas.evaluation import (
    EvaluationScoreItem,
    EvaluationVerdict,
    FailureAttribution,
    InternalCorrection,
    SimulationEvaluationRequest,
    SimulationEvaluationResponse,
)
from app.services.simulation_quality import weighted_simulation_score


EVALUATION_PROMPT_VERSION = "evaluation-v2.1-phase5-session-signals"
_DIMENSIONS = (
    "persona_fidelity",
    "dyadic_consistency",
    "state_continuity",
    "strategy_adherence",
    "reaction_plausibility",
    "style_fidelity",
    "evidence_grounding",
)
_COACH_LEAKAGE_MARKERS = (
    "你可以这样说",
    "建议用户说",
    "用户下一句",
    "候选话术",
    "candidate message",
)
_INVENTED_TRAIT_MARKERS = (
    "invented_persona_trait",
    "hallucinated_persona_trait",
    "凭空创造人物特征",
    "编造人物特征",
    "虚构人物特征",
)


class EvaluationAgent:
    """Independently evaluate target-person simulation fidelity."""

    prompt_version = EVALUATION_PROMPT_VERSION

    async def run(
        self,
        request: SimulationEvaluationRequest,
    ) -> SimulationEvaluationResponse:
        result = await generate_structured(
            system_prompt=EVALUATION_SYSTEM_PROMPT,
            user_prompt=build_evaluation_user_prompt(request),
            output_model=SimulationEvaluationResponse,
            temperature=0.1,
        )
        return self.post_process(result=result, request=request)

    def post_process(
        self,
        *,
        result: SimulationEvaluationResponse,
        request: SimulationEvaluationRequest,
    ) -> SimulationEvaluationResponse:
        candidate_digest = sha256(
            (
                request.simulation_result.policy_id
                + "|"
                + request.simulation_result.reply
            ).encode("utf-8")
        ).hexdigest()[:12]
        result.evaluation_id = (
            f"evaluation:{request.trace_id}:{request.turn_id}:{candidate_digest}"
        )

        for dimension in _DIMENSIONS:
            setattr(
                result,
                dimension,
                self._normalize_score_item(getattr(result, dimension)),
            )

        if (
            request.simulation_result.policy_id
            != request.response_policy.policy_id
        ):
            result.strategy_adherence.score = 0
            self._append_unique(
                result.critical_issues,
                "POLICY_ID_MISMATCH: Simulation 结果未使用本轮 Response Policy。",
            )

        result.critical_issues = self._clean_list(result.critical_issues)
        result.session_learning_signals = self._clean_internal_list(
            result.session_learning_signals
        )
        result.evaluator_notes = self._clean_internal_list(result.evaluator_notes)
        result.correction_for_strategy = self._normalize_correction(
            result.correction_for_strategy
        )
        result.correction_for_simulation = self._normalize_correction(
            result.correction_for_simulation
        )

        chat_record_available = (
            request.persona_snapshot.evidence_summary.chat_record_available
        )
        scores = {
            dimension: getattr(result, dimension).score
            for dimension in _DIMENSIONS
        }
        result.simulation_success_score = weighted_simulation_score(
            scores,
            chat_record_available=chat_record_available,
        )

        invented_trait = self._contains_invented_trait(result.critical_issues)
        if invented_trait:
            result.simulation_success_score = min(
                result.simulation_success_score,
                59,
            )

        result.confidence = self._clamp_confidence(result.confidence)
        context_gap = self._has_context_gap(request)
        if not chat_record_available:
            result.confidence = min(result.confidence, 0.69)
            self._append_unique(
                result.evaluator_notes,
                "未提供聊天记录，style_fidelity 与 evidence_grounding 已降权。",
            )
        if context_gap:
            result.confidence = min(result.confidence, 0.59)

        result.failure_attribution = self._resolve_attribution(
            result=result,
            context_gap=context_gap,
        )
        result.verdict = self._resolve_verdict(
            result=result,
            context_gap=context_gap,
            invented_trait=invented_trait,
        )
        self._route_corrections(result)
        return result

    def _resolve_attribution(
        self,
        *,
        result: SimulationEvaluationResponse,
        context_gap: bool,
    ) -> FailureAttribution:
        if context_gap and result.confidence < 0.6:
            return FailureAttribution.CONTEXT_GAP
        if (
            result.simulation_success_score >= 75
            and result.persona_fidelity.score >= 60
            and result.strategy_adherence.score >= 55
            and not result.critical_issues
        ):
            return FailureAttribution.NONE
        if result.failure_attribution != FailureAttribution.NONE:
            return result.failure_attribution

        persona_failed = result.persona_fidelity.score < 60
        execution_failed = result.strategy_adherence.score < 55
        if persona_failed and execution_failed:
            return FailureAttribution.MIXED
        if persona_failed:
            return FailureAttribution.STRATEGY_ERROR
        return FailureAttribution.SIMULATION_EXECUTION_ERROR

    def _resolve_verdict(
        self,
        *,
        result: SimulationEvaluationResponse,
        context_gap: bool,
        invented_trait: bool,
    ) -> EvaluationVerdict:
        score = result.simulation_success_score
        attribution = result.failure_attribution

        if context_gap and result.confidence < 0.6:
            return EvaluationVerdict.INSUFFICIENT_EVIDENCE
        if invented_trait or score < 60:
            return EvaluationVerdict.REPLAN_AND_REGENERATE
        if result.persona_fidelity.score < 60:
            if attribution in {
                FailureAttribution.STRATEGY_ERROR,
                FailureAttribution.MIXED,
            }:
                return EvaluationVerdict.REPLAN_AND_REGENERATE
            return EvaluationVerdict.REVISE_SIMULATION
        if result.strategy_adherence.score < 55:
            return EvaluationVerdict.REVISE_SIMULATION
        if score < 75 or result.critical_issues:
            if attribution in {
                FailureAttribution.STRATEGY_ERROR,
                FailureAttribution.MIXED,
            }:
                return EvaluationVerdict.REPLAN_AND_REGENERATE
            return EvaluationVerdict.REVISE_SIMULATION
        if score < 85:
            return EvaluationVerdict.ACCEPT_WITH_FEEDBACK
        return EvaluationVerdict.ACCEPT

    def _route_corrections(self, result: SimulationEvaluationResponse) -> None:
        attribution = result.failure_attribution
        if attribution in {FailureAttribution.NONE, FailureAttribution.CONTEXT_GAP}:
            result.correction_for_strategy = None
            result.correction_for_simulation = None
            return

        if attribution == FailureAttribution.STRATEGY_ERROR:
            result.correction_for_simulation = None
            result.correction_for_strategy = (
                result.correction_for_strategy
                or self._fallback_strategy_correction()
            )
            return

        if attribution == FailureAttribution.SIMULATION_EXECUTION_ERROR:
            result.correction_for_strategy = None
            result.correction_for_simulation = (
                result.correction_for_simulation
                or self._fallback_simulation_correction()
            )
            return

        result.correction_for_strategy = (
            result.correction_for_strategy or self._fallback_strategy_correction()
        )
        result.correction_for_simulation = (
            result.correction_for_simulation
            or self._fallback_simulation_correction()
        )

    def _normalize_score_item(self, item: EvaluationScoreItem) -> EvaluationScoreItem:
        item.score = self._clamp_score(item.score)
        item.reason = self._clean_text(item.reason)[:500] or "未提供评分原因。"
        item.evidence = self._clean_list(item.evidence, limit=12)
        return item

    def _normalize_correction(
        self,
        correction: InternalCorrection | None,
    ) -> InternalCorrection | None:
        if correction is None:
            return None
        correction.keep = self._clean_internal_list(correction.keep)
        correction.change = self._clean_internal_list(correction.change)
        correction.must_not = self._clean_internal_list(correction.must_not)
        if not (correction.keep or correction.change or correction.must_not):
            return None
        return correction

    def _has_context_gap(self, request: SimulationEvaluationRequest) -> bool:
        evidence = request.persona_snapshot.evidence_summary
        memory = request.session_memory
        has_memory_evidence = bool(
            memory.memory_items
            or memory.important_events
            or memory.target_sensitive_points
        )
        return (
            not evidence.chat_record_available
            and evidence.evidence_count == 0
            and evidence.overall_confidence < 0.6
            and not has_memory_evidence
        )

    @staticmethod
    def _contains_invented_trait(issues: list[str]) -> bool:
        combined = " ".join(issues).lower()
        return any(marker in combined for marker in _INVENTED_TRAIT_MARKERS)

    def _clean_internal_list(self, values: list[str]) -> list[str]:
        cleaned = self._clean_list(values)
        return [
            value
            for value in cleaned
            if not any(marker in value.lower() for marker in _COACH_LEAKAGE_MARKERS)
        ]

    def _clean_list(self, values: list[str], *, limit: int = 8) -> list[str]:
        cleaned: list[str] = []
        for value in values or []:
            text = self._clean_text(value)[:500]
            if text and text not in cleaned:
                cleaned.append(text)
        return cleaned[:limit]

    @staticmethod
    def _clean_text(value: object) -> str:
        return "" if value is None else str(value).strip()

    @staticmethod
    def _clamp_score(value: int) -> int:
        try:
            return max(0, min(100, int(value)))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _clamp_confidence(value: float) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _append_unique(values: list[str], value: str) -> None:
        if value not in values:
            values.append(value)

    @staticmethod
    def _fallback_strategy_correction() -> InternalCorrection:
        return InternalCorrection(
            keep=[],
            change=["依据 Persona、关系状态和证据重新制定 Response Policy。"],
            must_not=["不得把 Simulation 的措辞问题误写为 Persona 事实。"],
        )

    @staticmethod
    def _fallback_simulation_correction() -> InternalCorrection:
        return InternalCorrection(
            keep=["保持当前 Response Policy 的 action 和 response_goal。"],
            change=["按低分维度重新执行 Response Policy。"],
            must_not=["不得在重生成时自行改变 Strategy Action。"],
        )
