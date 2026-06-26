from __future__ import annotations

from app.agents.prompts import COACH_SYSTEM_PROMPT, build_report_user_prompt
from app.llm.client import generate_structured
from app.schemas.report import ReportRequest, ReportResponse
from app.schemas.session import ChatMessage


class CoachAgent:
    """
    CoachAgent 负责在模拟结束后生成沟通复盘报告。

    设计原则：
    1. Agent 层只负责业务流程，不直接接触 OpenAI / Qwen SDK。
    2. LLM 调用统一交给 app.llm.client.generate_structured。
    3. 输出必须是 ReportResponse，并经过业务级 post_process 修正。
    4. 报告必须保持“模拟预测”语气，不能把结果说成现实必然。
    """

    async def run(self, request: ReportRequest) -> ReportResponse:
        """
        根据完整模拟对话生成沟通分析报告。

        Args:
            request: 报告生成请求。

        Returns:
            ReportResponse: 沟通成功率、可能结果、优点、问题、风险、改写建议和下一步建议。
        """

        payload = request.model_dump()

        result = await generate_structured(
            system_prompt=COACH_SYSTEM_PROMPT,
            user_prompt=build_report_user_prompt(payload),
            output_model=ReportResponse,
        )

        return self.post_process(result=result, request=request)

    def post_process(
        self,
        *,
        result: ReportResponse,
        request: ReportRequest,
    ) -> ReportResponse:
        """
        对 LLM 已经通过 Pydantic 校验的报告结果进行业务级修正。

        Pydantic 负责结构合法性，post_process 负责业务合理性，例如：
        - success_probability 必须在 0 到 100；
        - 列表字段不应为空或过长；
        - suggested_rewrite 必须能直接复制使用；
        - 没有有效对话时不能给出过高成功率。
        """

        result.success_probability = self._clamp(result.success_probability, 0, 100)

        result.likely_outcome = self._clean_text(
            result.likely_outcome,
            default=self._default_likely_outcome(result.success_probability),
        )

        result.strengths = self._normalize_list(
            result.strengths,
            defaults=["能够主动表达沟通目标。"],
            max_items=5,
        )
        result.problems = self._normalize_list(
            result.problems,
            defaults=["部分表达仍需要补充具体背景、时间安排或对对方成本的考虑。"],
            max_items=5,
        )
        result.key_risks = self._normalize_list(
            result.key_risks,
            defaults=["如果请求过于直接或缺少缓冲，可能让对方感到压力。"],
            max_items=5,
        )

        result.suggested_rewrite = self._clean_text(
            result.suggested_rewrite,
            default=self._default_rewrite(request),
        )
        result.suggested_rewrite = self._truncate(result.suggested_rewrite, max_length=900)

        result.next_step_advice = self._clean_text(
            result.next_step_advice,
            default="下一步建议先补充具体背景和可执行方案，再以低压力方式提出请求。",
        )
        result.next_step_advice = self._truncate(result.next_step_advice, max_length=500)

        if not self._has_user_messages(request.messages):
            result.success_probability = min(result.success_probability, 50)
            if "尚未形成有效模拟对话，当前报告只能基于目标人物画像和沟通目标进行初步判断。" not in result.key_risks:
                result.key_risks.append("尚未形成有效模拟对话，当前报告只能基于目标人物画像和沟通目标进行初步判断。")

        return result

    def _default_likely_outcome(self, probability: int) -> str:
        if probability >= 75:
            return "从模拟结果看，对方较可能接受或至少愿意继续讨论，但仍需要保持具体、尊重和低压力的表达。"
        if probability >= 50:
            return "从模拟结果看，对方可能不会直接拒绝，但仍会关注请求是否合理、成本是否清晰。"
        return "从模拟结果看，对方可能存在明显顾虑，需要先降低对方压力并补充更多背景。"

    def _default_rewrite(self, request: ReportRequest) -> str:
        last_user_message = self._last_user_message(request.messages)
        if last_user_message:
            return (
                f"我想重新更清楚地表达一下：{last_user_message}\n\n"
                "如果这件事对你来说不方便，也完全可以直接告诉我；我主要是想先把背景和我的想法说明清楚。"
            )

        if request.scenario == "advisor":
            return "老师您好，我想向您说明一下目前的情况、已经尝试过的解决办法，以及我接下来的具体计划。希望您能看一下这个安排是否可行，如果不合适我也可以根据您的建议调整。"
        if request.scenario == "work":
            return "我想先同步一下这件事的背景、目前影响和我建议的处理方案。也想听听您这边是否有其他优先级或限制，我可以据此调整。"
        if request.scenario == "social":
            return "我想认真和你说一下这件事。我的本意不是给你压力，而是希望把我的想法说明白，也想听听你的感受。"
        return "我想更清楚地说明一下背景、我的想法和希望达成的结果。如果你觉得不方便，也可以直接告诉我。"

    @staticmethod
    def _has_user_messages(messages: list[ChatMessage]) -> bool:
        return any(message.role == "user" and message.content.strip() for message in messages)

    @staticmethod
    def _last_user_message(messages: list[ChatMessage]) -> str:
        for message in reversed(messages):
            if message.role == "user" and message.content.strip():
                return message.content.strip()
        return ""

    @staticmethod
    def _normalize_list(
        values: list[str],
        *,
        defaults: list[str],
        max_items: int,
    ) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            value = value.strip()
            if not value:
                continue
            if value not in cleaned:
                cleaned.append(value[:160])

        for value in defaults:
            if value not in cleaned:
                cleaned.append(value)

        return cleaned[:max_items]

    @staticmethod
    def _clean_text(value: str, *, default: str) -> str:
        value = value.strip() if isinstance(value, str) else ""
        return value or default

    @staticmethod
    def _truncate(value: str, *, max_length: int) -> str:
        value = value.strip()
        if len(value) <= max_length:
            return value
        return value[: max_length - 1].rstrip() + "…"

    @staticmethod
    def _clamp(value: int, low: int, high: int) -> int:
        return max(low, min(high, int(value)))
