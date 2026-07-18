from __future__ import annotations

import logging

from app.agents.prompts import (
    STRATEGY_PROMPT_VERSION,
    STRATEGY_SYSTEM_PROMPT,
    build_strategy_user_prompt,
)
from app.llm.client import generate_structured
from app.schemas.strategy import (
    ResponseAction,
    TargetResponsePolicy,
    TargetResponseStrategyRequest,
)


logger = logging.getLogger(__name__)

STRATEGY_AGENT_MODE = "shadow"
EXTREME_ACTIONS = {
    ResponseAction.NO_REPLY,
    ResponseAction.END_CONVERSATION,
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
    """Create a target-person response policy without writing the final reply."""

    prompt_version = STRATEGY_PROMPT_VERSION

    def __init__(self, *, mode: str = STRATEGY_AGENT_MODE) -> None:
        if mode not in {"shadow", "active"}:
            raise ValueError("StrategyAgent mode must be shadow or active")
        self.mode = mode

    async def run(
        self,
        request: TargetResponseStrategyRequest,
    ) -> TargetResponsePolicy:
        result = await generate_structured(
            system_prompt=STRATEGY_SYSTEM_PROMPT,
            user_prompt=build_strategy_user_prompt(request),
            output_model=TargetResponsePolicy,
            temperature=0.2,
        )
        policy = self.post_process(result=result, request=request)

        # Shadow Mode only records safe metadata. It does not affect SimulationAgent.
        logger.info(
            f"strategy_policy_{self.mode}_generated",
            extra={
                "trace_id": request.trace_id,
                "session_id": request.session_id,
                "turn_id": request.turn_id,
                "policy_id": policy.policy_id,
                "action": policy.action.value,
                "confidence": policy.confidence,
                "persona_evidence_count": len(policy.persona_evidence_refs),
                "memory_evidence_count": len(policy.memory_evidence_refs),
                "prompt_version": self.prompt_version,
                "mode": self.mode,
            },
        )
        return policy

    def post_process(
        self,
        *,
        result: TargetResponsePolicy,
        request: TargetResponseStrategyRequest,
    ) -> TargetResponsePolicy:
        result.policy_id = result.policy_id.strip() or f"policy_{request.turn_id}"
        result.response_goal = self._clean_internal_text(
            result.response_goal,
            fallback="从目标人物立场回应用户本轮表达。",
        )
        result.stance = self._clean_internal_text(
            result.stance,
            fallback="保持与当前人物画像和关系状态一致。",
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

        self._guard_extreme_action(result)
        return result

    def _guard_extreme_action(self, result: TargetResponsePolicy) -> None:
        if result.action not in EXTREME_ACTIONS:
            return

        has_grounding = bool(
            result.persona_evidence_refs and result.memory_evidence_refs
        )
        if result.confidence >= 0.8 and has_grounding:
            return

        previous_action = result.action
        result.action = (
            ResponseAction.DEFER
            if previous_action == ResponseAction.NO_REPLY
            else ResponseAction.SET_BOUNDARY
        )
        self._append_uncertainty(
            result,
            "no_reply 或 end_conversation 缺少高置信度双来源证据，已降级为较保守动作。",
        )

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
        result: TargetResponsePolicy,
        message: str,
    ) -> None:
        if message not in result.uncertainty_notes:
            result.uncertainty_notes.append(message)
        result.uncertainty_notes = result.uncertainty_notes[:5]
