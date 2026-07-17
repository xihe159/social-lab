from __future__ import annotations

import json
from typing import Any

from app.agents.coach_metrics import (
    build_dynamics_features,
    exact_or_nearest_quote,
    split_user_sentences,
)
from app.llm.client import generate_structured
from app.schemas.coach import (
    AnalysisLLMResult,
    AnalysisResult,
    SentenceDiagnostic,
)
from app.schemas.report import ReportRequest


ANALYSIS_SYSTEM_PROMPT = """
你是 Social Lab 的 AnalysisAgent。

你全权负责报告中的分析内容，包括：
1. 逐句诊断；
2. 需求合理性；
3. 主要影响因素；
4. 优势与劣势；
5. 核心瓶颈；
6. 关键风险；
7. 下一步建议；
8. 应避免的表达。

逐句诊断要求：
- 覆盖系统提供的每个 SentenceUnit；
- 分析句子功能、正负作用、清晰度、压力、共情、具体性；
- 说明目标人物可能如何理解；
- 给出优点、缺点和修改方向。

需求合理性必须覆盖：
- goal_legitimacy
- feasibility
- cost_to_target
- reciprocity
- consent_and_boundary
- timing
- information_completeness

“主要影响因素”要求：
- 只描述当前已存在的事实、状态和作用；
- 必须给出方向、重要性、原话证据和实际影响；
- 不得在影响因素中写下一步建议；
- 不得包含 improvement_action；
- 行动建议只能写入 next_step_advice；
- 禁止把预测概率当作影响因素。

约束：
- sentence_id 必须来自输入；
- evidence_quote 必须来自对话原文；
- 必须区分“需求是否合理”和“表达方式是否合理”；
- 信息不足时使用 insufficient_information 或条件性判断；
- 不得编造事实；
- 不输出 Markdown，只输出符合 AnalysisLLMResult 的 JSON。
""".strip()


def _json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
    )


def _build_prompt(
    request: ReportRequest,
    units: list[dict[str, Any]],
    features: dict[str, Any],
) -> str:
    return f"""
【场景】
{request.scenario}

【用户目标】
{request.goal}

【理想结果】
{request.outcome or '未提供'}

【目标人物画像】
{_json(request.persona.model_dump())}

【完整对话】
{_json([
    message.model_dump()
    for message in request.messages
])}

【逐句单元】
{_json(units)}

【StateAgent 量化特征】
{_json(features)}

请完成：
- 所有逐句单元的诊断；
- 需求合理性七维分析；
- 2 到 6 个主要影响因素；
- 优势与劣势；
- 核心瓶颈与关键风险；
- 独立的 next_step_advice；
- 独立的 do_not_say。

影响因素只能描述“现在是什么、造成什么影响”，
不能夹带“下一步应该怎么做”。
""".strip()


class AnalysisAgent:
    async def run(
        self,
        request: ReportRequest,
    ) -> AnalysisResult:
        units = split_user_sentences(request)
        features = build_dynamics_features(request)

        result = await generate_structured(
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            user_prompt=_build_prompt(
                request,
                [
                    unit.model_dump()
                    for unit in units
                ],
                features.model_dump(),
            ),
            output_model=AnalysisLLMResult,
            temperature=0.15,
        )

        unit_map = {
            unit.sentence_id: unit
            for unit in units
        }

        cleaned: list[SentenceDiagnostic] = []

        for diagnostic in result.sentence_diagnostics:
            unit = unit_map.get(
                diagnostic.sentence_id
            )
            if unit is None:
                continue

            diagnostic.evidence_quote = (
                exact_or_nearest_quote(
                    diagnostic.evidence_quote,
                    [unit],
                )
            )
            cleaned.append(diagnostic)

        diagnosed_ids = {
            item.sentence_id
            for item in cleaned
        }

        for unit in units:
            if unit.sentence_id in diagnosed_ids:
                continue

            cleaned.append(
                SentenceDiagnostic(
                    sentence_id=unit.sentence_id,
                    evidence_quote=unit.text,
                    function="other",
                    effect="neutral",
                    clarity=50,
                    pressure=50,
                    empathy=50,
                    specificity=50,
                    target_interpretation=(
                        "该句缺少充分的结构化判断，"
                        "需要结合上下文人工复核。"
                    ),
                    advantage=(
                        "保留了用户原始表达。"
                    ),
                    disadvantage=(
                        "模型未返回充分诊断。"
                    ),
                    recommended_change=(
                        "补充更具体的背景、请求与可接受选项。"
                    ),
                )
            )

        cleaned.sort(
            key=lambda item: (
                unit_map[item.sentence_id].turn_index,
                unit_map[item.sentence_id].sentence_index,
            )
        )

        influence_factors = sorted(
            result.influence_factors,
            key=lambda item: item.importance,
            reverse=True,
        )[:6]

        strengths = [
            item.title
            for item in result.advantages[:6]
        ] or [
            "用户愿意主动表达沟通目标。"
        ]

        problems = [
            item.title
            for item in result.disadvantages[:6]
        ] or [
            result.primary_bottleneck
        ]

        return AnalysisResult(
            sentence_diagnostics=cleaned,
            reasonability=result.reasonability,
            influence_factors=influence_factors,
            advantages=result.advantages,
            disadvantages=result.disadvantages,
            primary_bottleneck=(
                result.primary_bottleneck.strip()
            ),
            key_risks=[
                item.strip()
                for item in result.key_risks
                if item.strip()
            ][:6],
            next_step_advice=(
                result.next_step_advice.strip()
            ),
            do_not_say=[
                item.strip()
                for item in result.do_not_say
                if item.strip()
            ][:6],
            strengths=strengths,
            problems=problems,
            sentence_units=units,
        )
