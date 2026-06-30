from __future__ import annotations

from app.agents.prompts import MEMORY_SYSTEM_PROMPT, build_memory_user_prompt
from app.llm.client import generate_structured
from app.schemas.memory import MemoryUpdateRequest, MemoryUpdateResponse, SessionMemory


class MemoryAgent:
    """
    MemoryAgent 负责维护单次模拟会话中的短期记忆。

    设计原则：
    1. 只总结当前模拟会话，不生成长期用户记忆。
    2. 不声称真实了解目标人物。
    3. 输出必须符合 MemoryUpdateResponse。
    4. 结果进入 post_process，防止列表为空、摘要过长或下一步重点缺失。
    """

    async def run(self, request: MemoryUpdateRequest) -> MemoryUpdateResponse:
        payload = request.model_dump(mode="json")

        result = await generate_structured(
            system_prompt=MEMORY_SYSTEM_PROMPT,
            user_prompt=build_memory_user_prompt(payload),
            output_model=MemoryUpdateResponse,
        )

        return self.post_process(result=result, request=request)

    def post_process(
        self,
        *,
        result: MemoryUpdateResponse,
        request: MemoryUpdateRequest,
    ) -> MemoryUpdateResponse:
        memory = result.memory

        memory.conversation_summary = self._clean_text(
            memory.conversation_summary,
            default=self._fallback_summary(request),
        )
        memory.user_strategy_pattern = self._clean_list(
            memory.user_strategy_pattern,
            fallback=["用户正在尝试通过对话达成沟通目标。"],
            limit=6,
        )
        memory.target_sensitive_points = self._clean_list(
            memory.target_sensitive_points,
            fallback=[request.persona.focus or "对方关注沟通目标是否清楚、表达是否合适。"],
            limit=6,
        )
        memory.resolved_points = self._clean_list(
            memory.resolved_points,
            fallback=[],
            limit=6,
        )
        memory.unresolved_points = self._clean_list(
            memory.unresolved_points,
            fallback=["后续仍需根据目标人物反馈继续调整表达。"],
            limit=6,
        )
        memory.important_events = self._clean_list(
            memory.important_events,
            fallback=[self._event_from_turn(request)],
            limit=8,
        )
        memory.next_suggested_focus = self._clean_text(
            memory.next_suggested_focus,
            default="下一轮应围绕对方最关注的问题，补充具体事实、时间安排和可执行方案。",
        )

        result.memory_reason = self._clean_text(
            result.memory_reason,
            default="已根据本轮用户发言、目标人物回复和关系状态变化更新会话记忆。",
        )
        result.new_facts = self._clean_list(
            result.new_facts,
            fallback=[self._event_from_turn(request)],
            limit=6,
        )
        result.next_focus = self._clean_text(
            result.next_focus,
            default=memory.next_suggested_focus,
        )

        return result

    @staticmethod
    def _clean_text(value: str, *, default: str) -> str:
        text = (value or "").strip()
        return text if text else default

    @staticmethod
    def _clean_list(values: list[str], *, fallback: list[str], limit: int) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()

        for value in values or []:
            item = str(value).strip()
            if not item or item in seen:
                continue
            cleaned.append(item[:300])
            seen.add(item)

        if not cleaned:
            for value in fallback:
                item = str(value).strip()
                if item and item not in seen:
                    cleaned.append(item[:300])
                    seen.add(item)

        return cleaned[:limit]

    @staticmethod
    def _fallback_summary(request: MemoryUpdateRequest) -> str:
        return (
            f"用户的目标是：{request.goal}。本轮用户表达为：{request.user_message} "
            f"目标人物回复为：{request.target_reply}"
        )[:500]

    @staticmethod
    def _event_from_turn(request: MemoryUpdateRequest) -> str:
        return (
            f"用户提出：{request.user_message[:120]}；"
            f"目标人物回应：{request.target_reply[:120]}"
        )
