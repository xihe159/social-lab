from __future__ import annotations

import json
from typing import Any

from app.llm.client import generate_structured
from app.schemas.analysis import ConversationProcessAnalysis
from app.schemas.prediction import PredictionResult
from app.schemas.report import ReportRequest
from app.schemas.rewrite import (
    RewriteResult,
    RewriteVariants,
    SentenceRewrite,
)


REWRITE_SYSTEM_PROMPT = """
你是 Social Lab 的 RewriteAgent。

AnalysisAgent 已经完成逐句观察和评价，但没有给出任何改进意见。
你的职责是单独完成所有改进相关内容：

1. 对低效、高风险或阻碍目标的用户句子提供逐句改写；
2. 生成一段综合最推荐话术；
3. 生成最小修改版、温和版、坚定边界版；
4. 给出下一步沟通行动；
5. 列出下一轮应避免的表达。

要求：
- sentence_rewrites 只能引用 AnalysisAgent 中真实存在的用户句子；
- original_text 必须原样复制；
- 每个逐句改写要说明改写原因和预期影响；
- 不要修改目标人物的回复；
- 不要操控、威胁、欺骗、道德绑架或持续施压；
- 如果目标人物已经明确拒绝或终止沟通，不要继续强推；
- 如果压力较高，优先减少催促和立即表态要求；
- 如果清晰度较低，补足必要背景、责任和具体安排；
- 推荐表达要自然、可复制，并保留对方选择空间。

输出必须严格符合 RewriteResult JSON Schema，不要输出 Markdown。
""".strip()


class RewriteAgent:
    """
    所有改进、逐句改写和下一步建议统一由本 Agent 负责。
    """

    async def run(
        self,
        *,
        request: ReportRequest,
        prediction: PredictionResult,
        analysis: ConversationProcessAnalysis,
    ) -> RewriteResult:
        result = await generate_structured(
            system_prompt=REWRITE_SYSTEM_PROMPT,
            user_prompt=self._build_prompt(
                request=request,
                prediction=prediction,
                analysis=analysis,
            ),
            output_model=RewriteResult,
            temperature=0.25,
        )
        return self.post_process(
            result=result,
            request=request,
            analysis=analysis,
        )

    def post_process(
        self,
        *,
        result: RewriteResult,
        request: ReportRequest,
        analysis: ConversationProcessAnalysis,
    ) -> RewriteResult:
        sentence_lookup = {
            (sentence.turn_index, sentence.sentence_index): sentence
            for turn in analysis.turns
            for sentence in turn.sentences
        }

        cleaned_rewrites: list[SentenceRewrite] = []
        seen: set[tuple[int, int]] = set()

        for item in result.sentence_rewrites:
            key = (item.turn_index, item.sentence_index)
            source = sentence_lookup.get(key)
            if source is None or key in seen:
                continue

            item.original_text = source.sentence_text
            item.rewritten_text = self._clean_text(
                item.rewritten_text,
                source.sentence_text,
                600,
            )
            item.rewrite_reason = self._clean_text(
                item.rewrite_reason,
                "该改写用于降低表达阻力并提高信息完整度。",
                260,
            )
            item.expected_effect = self._clean_text(
                item.expected_effect,
                "预计会降低目标人物的判断成本或沟通压力。",
                260,
            )

            if item.rewritten_text.strip() == source.sentence_text.strip():
                continue

            cleaned_rewrites.append(item)
            seen.add(key)

        cleaned_rewrites.sort(
            key=lambda item: (
                item.turn_index,
                item.sentence_index,
            )
        )
        result.sentence_rewrites = cleaned_rewrites[:10]

        default_rewrite = self._default_rewrite(request)
        result.suggested_rewrite = self._clean_text(
            result.suggested_rewrite,
            default_rewrite,
            1000,
        )

        result.variants.minimal_edit = self._clean_text(
            result.variants.minimal_edit,
            result.suggested_rewrite,
            700,
        )
        result.variants.warmer_version = self._clean_text(
            result.variants.warmer_version,
            result.suggested_rewrite,
            700,
        )
        result.variants.firmer_version = self._clean_text(
            result.variants.firmer_version,
            result.suggested_rewrite,
            700,
        )

        result.next_step_advice = self._clean_text(
            result.next_step_advice,
            "先确认目标人物当前是否愿意继续讨论，再推进一个具体且可拒绝的小步骤。",
            900,
        )
        result.do_not_say = self._clean_list(
            result.do_not_say,
            fallback=[
                "不要使用命令、威胁、道德绑架或要求立即表态的表达。"
            ],
            max_items=6,
        )
        return result

    def _build_prompt(
        self,
        *,
        request: ReportRequest,
        prediction: PredictionResult,
        analysis: ConversationProcessAnalysis,
    ) -> str:
        rewrite_candidates = [
            {
                "turn_index": sentence.turn_index,
                "sentence_index": sentence.sentence_index,
                "sentence_text": sentence.sentence_text,
                "evaluation_label": sentence.evaluation_label,
                "evaluation_score": sentence.evaluation_score,
                "goal_effect": sentence.goal_effect,
                "target_likely_feeling": (
                    sentence.target_likely_feeling
                ),
                "evaluation_reason": sentence.evaluation_reason,
            }
            for turn in analysis.turns
            for sentence in turn.sentences
            if (
                sentence.evaluation_label
                in {"neutral", "risky", "damaging"}
                or sentence.goal_effect == "obstructs"
                or sentence.evaluation_score < 65
            )
        ]

        return f"""
请输出 RewriteResult。

【场景】
{request.scenario}

【用户目标】
{request.goal}

【期望结果】
{request.outcome or "未提供"}

【PredictionAgent 结果】
{self._pretty(prediction.model_dump())}

【AnalysisAgent 整体分析】
{self._pretty({
    "overall_assessment": analysis.overall_assessment,
    "problems": analysis.problems,
    "key_risks": analysis.key_risks,
    "primary_bottleneck": analysis.primary_bottleneck,
    "evaluation_scores": analysis.evaluation_scores.model_dump(),
    "state_trajectory_summary": analysis.state_trajectory_summary,
})}

【可逐句改写的候选句】
{self._pretty(rewrite_candidates)}

【完整逐句分析】
{self._pretty([
    turn.model_dump()
    for turn in analysis.turns
])}

请注意：
- sentence_rewrites 只处理确有改进价值的句子；
- 不必改写已经 strong 或 clearly effective 的句子；
- 所有下一步和改进意见都在本输出中完成；
- suggested_rewrite 应形成一段自然连贯的完整表达。
""".strip()

    @staticmethod
    def _default_rewrite(request: ReportRequest) -> str:
        last_user_message = ""
        for message in reversed(request.messages):
            if (
                message.role == "user"
                and message.content.strip()
            ):
                last_user_message = message.content.strip()
                break

        if last_user_message:
            return (
                f"我想重新更清楚地说明一下：{last_user_message}\n\n"
                "我会把背景、我的责任和具体安排说明清楚；"
                "如果这件事对你不方便，也可以直接告诉我。"
            )

        return (
            "我想先把背景、我的考虑和具体请求说明清楚，"
            "也想了解你目前的顾虑和可接受范围。"
        )

    @staticmethod
    def _clean_text(
        value: object,
        fallback: str,
        max_length: int,
    ) -> str:
        text = value.strip() if isinstance(value, str) else ""
        text = text or fallback
        if len(text) <= max_length:
            return text
        return text[: max_length - 1].rstrip() + "…"

    @staticmethod
    def _clean_list(
        values: list[str],
        *,
        fallback: list[str],
        max_items: int,
    ) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = str(value).strip()
            if item and item not in cleaned:
                cleaned.append(item[:260])

        for item in fallback:
            if item and item not in cleaned:
                cleaned.append(item)

        return cleaned[:max_items]

    @staticmethod
    def _pretty(value: Any) -> str:
        return json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
        )
