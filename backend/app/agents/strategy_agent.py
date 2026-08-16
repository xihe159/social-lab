from __future__ import annotations

import logging

from app.agents.prompts import (
    STRATEGY_PROMPT_VERSION,
    STRATEGY_SYSTEM_PROMPT,
    build_strategy_user_prompt,
)
from app.llm.client import generate_structured
from app.prompts.strategy import STRATEGY_PROMPT
from app.schemas.strategy import (
    ResponseMode,
    ResponseModeHypothesis,
    TargetResponseGuidance,
    TargetResponseStrategyRequest,
)


logger = logging.getLogger(__name__)

STRATEGY_AGENT_MODE = "shadow"
EXTREME_MODES = {
    ResponseMode.NO_REPLY,
    ResponseMode.END_CONVERSATION,
}
COACH_LEAK_MARKERS = (
    "你可以这样说",
    "建议用户",
    "用户下一句",
    "候选话术",
    "推荐话术",
    "温和版",
    "坚定版",
    "最小修改版",
)


class StrategyAgent:
    """Offer response hypotheses without taking final authority from Simulation."""

    prompt_version = STRATEGY_PROMPT_VERSION

    def __init__(self, *, mode: str = STRATEGY_AGENT_MODE) -> None:
        if mode not in {"shadow", "active"}:
            raise ValueError("StrategyAgent mode must be shadow or active")
        self.mode = mode

    async def run(
        self,
        request: TargetResponseStrategyRequest,
    ) -> TargetResponseGuidance:
        result = await generate_structured(
            system_prompt=STRATEGY_SYSTEM_PROMPT,
            user_prompt=build_strategy_user_prompt(request),
            output_model=TargetResponseGuidance,
            temperature=STRATEGY_PROMPT.temperature,
        )
        guidance = self.post_process(result=result, request=request)

        # Shadow Mode only records safe metadata. It does not affect SimulationAgent.
        logger.info(
            f"strategy_guidance_{self.mode}_generated",
            extra={
                "trace_id": request.trace_id,
                "session_id": request.session_id,
                "turn_id": request.turn_id,
                "guidance_id": guidance.guidance_id,
                "recommended_mode": guidance.recommended_mode.value,
                "confidence": guidance.confidence,
                "persona_evidence_count": len(guidance.persona_evidence_refs),
                "memory_evidence_count": len(guidance.memory_evidence_refs),
                "prompt_version": self.prompt_version,
                "mode": self.mode,
            },
        )
        return guidance

    def post_process(
        self,
        *,
        result: TargetResponseGuidance,
        request: TargetResponseStrategyRequest,
    ) -> TargetResponseGuidance:
        result.guidance_id = (
            result.guidance_id.strip() or f"guidance_{request.turn_id}"
        )
        result.communication_goal = self._clean_internal_text(
            result.communication_goal,
            fallback="从目标人物立场回应用户本轮表达。",
        )
        result.required_content = self._clean_internal_list(
            result.required_content,
            fallback=["回应用户本轮表达中的核心内容"],
            limit=5,
        )
        result.forbidden_content = self._clean_internal_list(
            result.forbidden_content,
            fallback=["替用户制定下一句话", "虚构无证据的人物事实"],
            limit=5,
        )
        result.uncertainty_notes = self._clean_list(
            result.uncertainty_notes,
            limit=5,
        )

        persona_ref = f"persona_snapshot:{request.persona_snapshot.persona_id}"
        persona_refs_before = list(result.persona_evidence_refs)
        result.persona_evidence_refs = self._valid_persona_refs(
            result.persona_evidence_refs,
            request=request,
        )
        if persona_refs_before and not result.persona_evidence_refs:
            self._append_uncertainty(
                result,
                "模型返回的 Persona evidence refs 在输入中不存在，已移除。",
            )
        if not result.persona_evidence_refs:
            result.persona_evidence_refs = [persona_ref]
            self._append_uncertainty(
                result,
                "模型未返回具体 Persona 证据，已回退到当前 Persona snapshot。",
            )

        memory_refs_before = list(result.memory_evidence_refs)
        result.memory_evidence_refs = self._valid_memory_refs(
            result.memory_evidence_refs,
            request=request,
        )
        if memory_refs_before and not result.memory_evidence_refs:
            self._append_uncertainty(
                result,
                "模型返回的 Memory evidence refs 在输入中不存在，已移除。",
            )

        self._guard_extreme_modes(result, request=request)
        return result

    def _guard_extreme_modes(
        self,
        result: TargetResponseGuidance,
        *,
        request: TargetResponseStrategyRequest,
    ) -> None:
        if result.recommended_mode not in EXTREME_MODES:
            return

        evidence_score = self._extreme_mode_evidence_score(
            result,
            request=request,
        )
        if evidence_score >= 0.60:
            result.confidence = min(
                result.confidence,
                0.60 + min(0.30, evidence_score * 0.30),
            )
            return

        fallback_mode = (
            ResponseMode.DEFER
            if result.recommended_mode == ResponseMode.NO_REPLY
            else ResponseMode.SET_BOUNDARY
        )
        existing = next(
            (
                item
                for item in result.possible_response_modes
                if item.mode == fallback_mode
            ),
            None,
        )
        if existing is None:
            fallback_hypothesis = ResponseModeHypothesis(
                mode=fallback_mode,
                probability=1.0,
                reason="当前证据不足以把极端反应作为推荐方向。",
            )
            if len(result.possible_response_modes) >= 3:
                extreme = next(
                    item
                    for item in result.possible_response_modes
                    if item.mode == result.recommended_mode
                )
                other = next(
                    (
                        item
                        for item in result.possible_response_modes
                        if item.mode != result.recommended_mode
                    ),
                    None,
                )
                result.possible_response_modes = [
                    item
                    for item in (extreme, other, fallback_hypothesis)
                    if item is not None
                ]
            else:
                result.possible_response_modes = [
                    *result.possible_response_modes,
                    fallback_hypothesis,
                ]
        result.recommended_mode = fallback_mode
        result.possible_response_modes = _normalize_hypotheses(
            result.possible_response_modes
        )
        result.confidence = min(result.confidence, 0.59)
        self._append_uncertainty(
            result,
            "极端反应缺少 Persona 与当前语义组合证据，已保留为候选但不作为推荐方向。",
        )

    @staticmethod
    def _extreme_mode_evidence_score(
        result: TargetResponseGuidance,
        *,
        request: TargetResponseStrategyRequest,
    ) -> float:
        score = 0.0
        if any(
            not ref.startswith("persona_snapshot:")
            for ref in result.persona_evidence_refs
        ):
            score += 0.35
        analysis = request.turn_state_analysis
        if analysis is not None and (
            analysis.behavior_signals.pressure >= 0.60
            or analysis.behavior_signals.boundary_violation >= 0.55
            or analysis.risk_flags
        ):
            score += 0.35
        if result.memory_evidence_refs:
            score += 0.20
        if analysis is not None and any(
            marker in " ".join(analysis.detected_events).lower()
            for marker in ("repeated", "连续", "反复")
        ):
            score += 0.10
        return min(1.0, score)

    def _clean_internal_text(self, value: str, *, fallback: str) -> str:
        cleaned = str(value or "").strip()
        if not cleaned or self._contains_coach_leak(cleaned):
            return fallback
        return cleaned[:240]

    def _clean_internal_list(
        self,
        values: list[str],
        *,
        fallback: list[str],
        limit: int,
    ) -> list[str]:
        cleaned = [
            item
            for item in self._clean_list(values, limit=limit)
            if not self._contains_coach_leak(item)
        ]
        return cleaned or list(fallback)

    @staticmethod
    def _clean_list(values: list[str], *, limit: int) -> list[str]:
        cleaned: list[str] = []
        for value in values or []:
            item = str(value).strip()
            if item and item not in cleaned:
                cleaned.append(item[:200])
            if len(cleaned) >= limit:
                break
        return cleaned

    def _valid_persona_refs(
        self,
        values: list[str],
        *,
        request: TargetResponseStrategyRequest,
    ) -> list[str]:
        persona = request.persona_snapshot
        allowed = {f"persona_snapshot:{persona.persona_id}"}
        for pattern in persona.behavior_patterns:
            allowed.add(pattern.pattern_id)
            allowed.update(pattern.evidence_ids)
            allowed.update(pattern.counter_evidence_ids)

        cleaned = self._clean_list(values, limit=6)
        return [
            item
            for item in cleaned
            if item in allowed or item.startswith("persona_field:")
        ]

    def _valid_memory_refs(
        self,
        values: list[str],
        *,
        request: TargetResponseStrategyRequest,
    ) -> list[str]:
        if request.session_memory is None:
            return []
        allowed = {
            item.memory_id for item in request.session_memory.memory_items
        }
        return [
            item
            for item in self._clean_list(values, limit=6)
            if item in allowed
        ]

    @staticmethod
    def _contains_coach_leak(value: str) -> bool:
        return any(marker in value for marker in COACH_LEAK_MARKERS)

    @staticmethod
    def _append_uncertainty(
        result: TargetResponseGuidance,
        message: str,
    ) -> None:
        if message not in result.uncertainty_notes:
            result.uncertainty_notes.append(message)
        result.uncertainty_notes = result.uncertainty_notes[:5]


def _normalize_hypotheses(
    values: list[ResponseModeHypothesis],
) -> list[ResponseModeHypothesis]:
    total = sum(item.probability for item in values)
    if total <= 0:
        probabilities = [1.0 / len(values)] * len(values)
    else:
        probabilities = [item.probability / total for item in values]
    rounded = [round(value, 4) for value in probabilities]
    rounded[-1] = round(1.0 - sum(rounded[:-1]), 4)
    for item, probability in zip(values, rounded, strict=True):
        item.probability = probability
    return values
