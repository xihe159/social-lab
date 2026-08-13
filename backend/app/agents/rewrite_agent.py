from __future__ import annotations

import json
from typing import Any

from app.llm.client import generate_structured
from app.prompts.report import REWRITE_PROMPT, build_rewrite_user_prompt
from app.schemas.analysis import ConversationProcessAnalysis
from app.schemas.prediction import PredictionResult
from app.schemas.report import ReportRequest
from app.schemas.rewrite import (
    RewriteResult,
    RewriteVariants,
    SentenceRewrite,
)

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
            system_prompt=REWRITE_PROMPT.system_prompt,
            user_prompt=build_rewrite_user_prompt(
                request=request,
                prediction=prediction,
                analysis=analysis,
            ),
            output_model=RewriteResult,
            temperature=REWRITE_PROMPT.temperature,
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
