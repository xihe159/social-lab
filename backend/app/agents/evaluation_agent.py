from __future__ import annotations

from hashlib import sha256

from app.prompts.strategy import (
    EVALUATION_PROMPT,
    EVALUATION_PROMPT_VERSION,
    EVALUATION_SYSTEM_PROMPT,
    build_evaluation_user_prompt,
)
from app.llm.client import generate_structured
from app.schemas.evaluation import (
    EvaluationScoreItem,
    EvaluationVerdict,
    FailureAttribution,
    HardErrorCode,
    InternalCorrection,
    SimulationEvaluationRequest,
    SimulationEvaluationResponse,
)
from app.services.simulation_quality import weighted_simulation_score


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
_HARD_ERROR_MARKERS: dict[HardErrorCode, tuple[str, ...]] = {
    HardErrorCode.PERSONA_VIOLATION: (
        "persona_violation",
        "明显违反人物",
        "严重违背persona",
    ),
    HardErrorCode.MEMORY_CONTRADICTION: (
        "memory_contradiction",
        "与已确认记忆冲突",
        "与memory冲突",
    ),
    HardErrorCode.INVENTED_PERSONA_TRAIT: _INVENTED_TRAIT_MARKERS,
    HardErrorCode.ACTION_TEXT_CONTRADICTION: (
        "action_text_contradiction",
        "动作与文本矛盾",
        "action与回复矛盾",
    ),
    HardErrorCode.UNGROUNDED_GUIDANCE_DEVIATION: (
        "ungrounded_guidance_deviation",
        "无证据偏离guidance",
        "无依据偏离策略建议",
        "policy_id_mismatch",
    ),
}


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
            temperature=EVALUATION_PROMPT.temperature,
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

        expected_guidance_id = (
            request.response_guidance.guidance_id
            if request.response_guidance is not None
            else request.response_policy.policy_id
        )
        actual_guidance_id = (
            request.simulation_result.guidance_id
            or request.simulation_result.policy_id
        )
        if actual_guidance_id != expected_guidance_id:
            result.strategy_adherence.score = 0
            self._append_unique(
                result.critical_issues,
                "POLICY_ID_MISMATCH: Simulation 结果未关联本轮 Response Guidance。",
            )
            self._append_hard_error(
                result,
                HardErrorCode.UNGROUNDED_GUIDANCE_DEVIATION,
            )

        result.critical_issues = self._clean_list(result.critical_issues)
        self._infer_hard_errors(result)
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

        invented_trait = (
            HardErrorCode.INVENTED_PERSONA_TRAIT in result.hard_errors
            or self._contains_invented_trait(result.critical_issues)
        )
        if invented_trait:
            self._append_hard_error(
                result,
                HardErrorCode.INVENTED_PERSONA_TRAIT,
            )
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
            not result.hard_errors
        ):
            return FailureAttribution.NONE
        if result.failure_attribution != FailureAttribution.NONE:
            return result.failure_attribution

        strategy_errors = {
            HardErrorCode.PERSONA_VIOLATION,
            HardErrorCode.MEMORY_CONTRADICTION,
            HardErrorCode.INVENTED_PERSONA_TRAIT,
            HardErrorCode.UNGROUNDED_GUIDANCE_DEVIATION,
        }
        has_strategy_error = bool(set(result.hard_errors) & strategy_errors)
        has_execution_error = (
            HardErrorCode.ACTION_TEXT_CONTRADICTION in result.hard_errors
        )
        if has_strategy_error and has_execution_error:
            return FailureAttribution.MIXED
        if has_strategy_error:
            return FailureAttribution.STRATEGY_ERROR
        if has_execution_error:
            return FailureAttribution.SIMULATION_EXECUTION_ERROR
        return FailureAttribution.NONE

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
        if not result.hard_errors:
            return (
                EvaluationVerdict.ACCEPT
                if score >= 85
                else EvaluationVerdict.ACCEPT_WITH_FEEDBACK
            )
        if (
            result.hard_errors
            == [HardErrorCode.ACTION_TEXT_CONTRADICTION]
            or (
                set(result.hard_errors)
                == {HardErrorCode.ACTION_TEXT_CONTRADICTION}
            )
        ):
            return EvaluationVerdict.REVISE_SIMULATION
        if attribution == FailureAttribution.SIMULATION_EXECUTION_ERROR:
            return EvaluationVerdict.REVISE_SIMULATION
        return EvaluationVerdict.REPLAN_AND_REGENERATE

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

    def _infer_hard_errors(
        self,
        result: SimulationEvaluationResponse,
    ) -> None:
        combined = " ".join(result.critical_issues).lower()
        for code, markers in _HARD_ERROR_MARKERS.items():
            if any(marker.lower() in combined for marker in markers):
                self._append_hard_error(result, code)
        result.hard_errors = list(dict.fromkeys(result.hard_errors))[:5]

    @staticmethod
    def _append_hard_error(
        result: SimulationEvaluationResponse,
        code: HardErrorCode,
    ) -> None:
        if code not in result.hard_errors:
            result.hard_errors.append(code)

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
