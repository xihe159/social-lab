# social-lab/backend/app/agents/strategy_agent.py
# 2026/07/01
# 新增内容：StrategyAgent，用于生成下一轮沟通策略。
# 设计注意：
# 1. 不直接依赖 SessionOrchestrator，作为独立 Agent 可被 API 或后续 Orchestrator 调用。
# 2. LLM 失败由 API 层捕获；本文件负责结构化输出与业务后处理。
# 3. 后处理只做清洗、裁剪、兜底，不改变接口结构。

from __future__ import annotations

from app.agents.prompts import STRATEGY_SYSTEM_PROMPT, build_strategy_user_prompt
from app.llm.client import generate_structured
from app.schemas.strategy import (
    StrategyAdviceRequest,
    StrategyAdviceResponse,
    StrategyCandidateMessage,
)


class StrategyAgent:
    async def run(self, request: StrategyAdviceRequest) -> StrategyAdviceResponse:
        payload = request.model_dump()

        result = await generate_structured(
            system_prompt=STRATEGY_SYSTEM_PROMPT,
            user_prompt=build_strategy_user_prompt(payload),
            output_model=StrategyAdviceResponse,
        )

        return self.post_process(result=result, request=request)

    def post_process(
        self,
        *,
        result: StrategyAdviceResponse,
        request: StrategyAdviceRequest,
    ) -> StrategyAdviceResponse:
        """
        对 StrategyAgent 输出做业务级稳定化处理。
        """

        result.next_move = self._clean_text(
            result.next_move,
            fallback="先回应对方关切，再补充具体事实和下一步计划。",
        )
        result.recommended_tone = self._clean_text(
            result.recommended_tone,
            fallback="诚恳、具体、尊重边界",
        )
        result.candidate_message = self._clean_text(
            result.candidate_message,
            fallback=self._build_fallback_message(request),
        )
        result.reason = self._clean_text(
            result.reason,
            fallback="当前策略需要同时降低对方的不确定感，并推动用户目标向前一步。",
        )

        result.avoid = self._clean_list(
            result.avoid,
            fallback=["不要施压或要求对方立刻答应", "不要只表达情绪而不提供具体信息"],
            limit=5,
        )
        result.focus_points = self._clean_list(
            result.focus_points,
            fallback=["补充具体事实", "说明下一步安排", "尊重对方选择"],
            limit=5,
        )
        result.risk_reminders = self._clean_list(
            result.risk_reminders,
            fallback=[],
            limit=5,
        )

        result.alternative_messages = self._clean_candidate_messages(
            result.alternative_messages,
            fallback_message=result.candidate_message,
        )

        # 如果 SafetyAgent 已经给出风险提示，则 StrategyAgent 的风险提醒中保留该安全提示。
        safety = request.safety
        if safety is not None and getattr(safety, "action", "allow") in {"warn", "block"}:
            notice = getattr(safety, "user_notice", "") or getattr(safety, "safe_rewrite_hint", "")
            if notice:
                result.risk_reminders = self._append_unique(
                    result.risk_reminders,
                    notice,
                    limit=5,
                )

        return result

    def _clean_text(self, value: str, *, fallback: str) -> str:
        value = (value or "").strip()
        return value or fallback

    def _clean_list(self, values: list[str], *, fallback: list[str], limit: int) -> list[str]:
        cleaned: list[str] = []
        for item in values or []:
            text = str(item).strip()
            if text and text not in cleaned:
                cleaned.append(text)
            if len(cleaned) >= limit:
                break
        return cleaned or fallback

    def _clean_candidate_messages(
        self,
        values: list[StrategyCandidateMessage],
        *,
        fallback_message: str,
    ) -> list[StrategyCandidateMessage]:
        cleaned: list[StrategyCandidateMessage] = []

        for item in values or []:
            label = (item.label or "").strip() or "备选话术"
            message = (item.message or "").strip()
            use_when = (item.use_when or "").strip() or "当你希望更稳妥地推进沟通时使用"

            if not message:
                continue

            cleaned.append(
                StrategyCandidateMessage(
                    label=label,
                    message=message,
                    use_when=use_when,
                )
            )

            if len(cleaned) >= 3:
                break

        if cleaned:
            return cleaned

        return [
            StrategyCandidateMessage(
                label="稳妥版",
                message=fallback_message,
                use_when="当你希望先降低对方压力，再继续推进目标时使用。",
            )
        ]

    def _append_unique(self, values: list[str], item: str, *, limit: int) -> list[str]:
        cleaned = list(values)
        if item not in cleaned:
            cleaned.append(item)
        return cleaned[:limit]

    def _build_fallback_message(self, request: StrategyAdviceRequest) -> str:
        scenario = request.scenario

        if scenario == "advisor":
            return "老师，我想补充说明一下目前的具体情况和后续安排，也想听听您对下一步的建议。"

        if scenario == "work":
            return "我补充一下目前的进展、风险和下一步计划，方便我们一起确认后续怎么推进。"

        return "我想更清楚地说明一下我的想法，也会尊重你的感受和选择。"
