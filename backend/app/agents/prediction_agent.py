from __future__ import annotations

import json
from typing import Any

from app.agents.coach_metrics import (
    build_dynamics_features,
    confidence_from_features,
)
from app.llm.client import generate_structured
from app.schemas.coach import PredictionLLMResult, PredictionResult
from app.schemas.report import ReportRequest


PREDICTION_SYSTEM_PROMPT = """
你是 Social Lab 的 PredictionAgent。

你的职责严格限制为两部分：
1. 预测本轮沟通成功率；
2. 预测当前最可能出现的沟通结果。

系统会提供由 StateAgent 多轮量化指标计算得到的 quantitative_baseline。
你不能凭感觉重新生成最终概率，只能结合完整对话、目标人物回复和画像，
对该基线做 -12 到 +12 的有限校正。

你可以输出概率判断依据，但不得输出：
- 主要影响因素列表；
- 优势或劣势分析；
- 风险清单；
- 下一步建议；
- 改写建议；
- improvement_action；
- do_not_say。

约束：
- model_adjustment 只能在 -12 到 +12；
- likely_outcome 只描述当前最可能发生的结果；
- probability_reasoning 只解释成功率与结果预测依据；
- 不把模拟预测说成现实必然；
- 量化指标和对话证据冲突时，应降低校正幅度；
- 不输出 Markdown，只输出符合 PredictionLLMResult 的 JSON。
""".strip()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _build_prompt(
    request: ReportRequest,
    features: dict[str, Any],
) -> str:
    messages = [
        message.model_dump()
        for message in request.messages
    ]

    return f"""
【场景】
{request.scenario}

【沟通目标】
{request.goal}

【理想结果】
{request.outcome or '未提供'}

【目标人物画像】
{_json(request.persona.model_dump())}

【完整对话】
{_json(messages)}

【StateAgent 量化特征】
{_json(features)}

请只输出：
- model_adjustment
- likely_outcome
- probability_reasoning

quantitative_baseline 是最终概率锚点。
你只负责有限校正与结果预测，不负责分析或建议。
""".strip()


class PredictionAgent:
    async def run(
        self,
        request: ReportRequest,
    ) -> PredictionResult:
        features = build_dynamics_features(request)

        llm_result = await generate_structured(
            system_prompt=PREDICTION_SYSTEM_PROMPT,
            user_prompt=_build_prompt(
                request,
                features.model_dump(),
            ),
            output_model=PredictionLLMResult,
            temperature=0.1,
        )

        confidence, confidence_score = (
            confidence_from_features(features)
        )

        adjustment = max(
            -12,
            min(12, int(llm_result.model_adjustment)),
        )

        final_probability = max(
            0,
            min(
                100,
                features.quantitative_baseline + adjustment,
            ),
        )

        if features.turn_count == 0:
            final_probability = min(
                final_probability,
                50,
            )
            confidence = "low"
            confidence_score = min(
                confidence_score,
                25,
            )

        return PredictionResult(
            baseline_probability=(
                features.quantitative_baseline
            ),
            model_adjustment=adjustment,
            success_probability=final_probability,
            confidence=confidence,
            confidence_score=confidence_score,
            likely_outcome=(
                llm_result.likely_outcome.strip()
            ),
            probability_reasoning=(
                llm_result.probability_reasoning.strip()
            ),
            features=features,
        )
