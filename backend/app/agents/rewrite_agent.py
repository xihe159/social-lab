from __future__ import annotations

import json
from typing import Any

from app.agents.coach_metrics import (
    build_dynamics_features,
)
from app.llm.client import generate_structured
from app.schemas.coach import (
    AnalysisResult,
    CandidateScore,
    RankedRewrite,
    RewriteCandidatesResult,
    RewriteCritiqueResult,
    RewriteResult,
)
from app.schemas.report import ReportRequest


WRITER_SYSTEM_PROMPT = """
你是 Social Lab 的 CandidateWriterAgent。

你只负责根据 AnalysisAgent 的诊断生成用户可参考的对话候选：
- balanced：综合推荐；
- minimal_edit：尽量保留用户原话；
- warmer：更重视情绪安全和关系修复；
- firmer：更清晰地表达请求与边界，但不能威胁或施压。

每个版本必须：
1. 回应 AnalysisAgent 指出的核心瓶颈；
2. 落实 AnalysisAgent 的下一步建议；
3. 适配当前氛围、压力、节奏和修复空间；
4. 保留用户真实目标；
5. 不擅自增加承诺、事实或身份信息；
6. candidate_id 使用 balanced、minimal_edit、warmer、firmer。

你不得重新分析成功率，不得重新生成主要影响因素，
也不得输出新的 next_step_advice 或 do_not_say。
不输出 Markdown，只输出 RewriteCandidatesResult JSON。
""".strip()


CRITIC_SYSTEM_PROMPT = """
你是 Social Lab 的 RewriteCriticAgent。

你只负责独立评分每个候选话术。
评分维度：
- goal_fit
- state_fit
- naturalness
- pressure_safety
- specificity
- fidelity

重点检查：
- 是否回应 AnalysisAgent 的核心瓶颈；
- 是否落实 AnalysisAgent 的下一步建议；
- 是否与 StateAgent 当前压力、氛围和节奏匹配；
- 是否自然、可直接复制；
- 是否加入用户没有提供的事实或承诺；
- 是否存在命令、道德绑架、威胁、操控或逼迫立即表态。

必须覆盖所有 candidate_id。
不得生成成功率、影响因素或新的行动建议。
不输出 Markdown，只输出 RewriteCritiqueResult JSON。
""".strip()


_WEIGHTS = {
    "goal_fit": 0.24,
    "state_fit": 0.20,
    "naturalness": 0.14,
    "pressure_safety": 0.18,
    "specificity": 0.12,
    "fidelity": 0.12,
}


def _json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
    )


def _writer_prompt(
    request: ReportRequest,
    analysis: AnalysisResult,
    features: dict[str, Any],
) -> str:
    important_diagnostics = sorted(
        analysis.sentence_diagnostics,
        key=lambda item: (
            item.effect == "hurts",
            item.pressure,
            100 - item.clarity,
        ),
        reverse=True,
    )[:8]

    return f"""
【用户目标】
{request.goal}

【理想结果】
{request.outcome or '未提供'}

【完整对话】
{_json([
    message.model_dump()
    for message in request.messages
])}

【StateAgent 量化特征】
{_json(features)}

【AnalysisAgent 结果】
{_json({
    "reasonability": (
        analysis.reasonability.model_dump()
    ),
    "influence_factors": [
        item.model_dump()
        for item in analysis.influence_factors
    ],
    "primary_bottleneck": (
        analysis.primary_bottleneck
    ),
    "key_risks": analysis.key_risks,
    "next_step_advice": (
        analysis.next_step_advice
    ),
    "do_not_say": analysis.do_not_say,
    "important_sentence_diagnostics": [
        item.model_dump()
        for item in important_diagnostics
    ],
})}

只生成候选对话，不生成新的分析或建议字段。
""".strip()


def _critic_prompt(
    request: ReportRequest,
    analysis: AnalysisResult,
    features: dict[str, Any],
    candidates: RewriteCandidatesResult,
) -> str:
    return f"""
【用户目标】
{request.goal}

【需求合理性】
{_json(
    analysis.reasonability.model_dump()
)}

【当前量化状态】
{_json(features)}

【核心瓶颈】
{analysis.primary_bottleneck}

【AnalysisAgent 下一步建议】
{analysis.next_step_advice}

【应避免表达】
{_json(analysis.do_not_say)}

【候选话术】
{_json(candidates.model_dump())}
""".strip()


def _weighted_score(
    score: CandidateScore,
) -> float:
    value = sum(
        getattr(score, name) * weight
        for name, weight in _WEIGHTS.items()
    )

    if score.pressure_safety < 55:
        value -= 12

    if score.fidelity < 55:
        value -= 10

    return round(
        max(0.0, min(100.0, value)),
        2,
    )


class RewriteAgent:
    """候选生成、独立批评和确定性排序。"""

    async def run(
        self,
        request: ReportRequest,
        analysis: AnalysisResult,
    ) -> RewriteResult:
        features = build_dynamics_features(request)

        candidates = await generate_structured(
            system_prompt=WRITER_SYSTEM_PROMPT,
            user_prompt=_writer_prompt(
                request,
                analysis,
                features.model_dump(),
            ),
            output_model=RewriteCandidatesResult,
            temperature=0.35,
        )

        critique = await generate_structured(
            system_prompt=CRITIC_SYSTEM_PROMPT,
            user_prompt=_critic_prompt(
                request,
                analysis,
                features.model_dump(),
                candidates,
            ),
            output_model=RewriteCritiqueResult,
            temperature=0.1,
        )

        candidate_map = {
            item.candidate_id: item
            for item in candidates.candidates
        }

        ranked: list[RankedRewrite] = []

        for score in critique.scores:
            candidate = candidate_map.get(
                score.candidate_id
            )
            if candidate is None:
                continue

            ranked.append(
                RankedRewrite(
                    candidate=candidate,
                    score=_weighted_score(score),
                    recommendation_reason=(
                        score.recommendation_reason.strip()
                    ),
                )
            )

        ranked_ids = {
            item.candidate.candidate_id
            for item in ranked
        }

        for candidate in candidates.candidates:
            if candidate.candidate_id in ranked_ids:
                continue

            ranked.append(
                RankedRewrite(
                    candidate=candidate,
                    score=50.0,
                    recommendation_reason=(
                        "批评 Agent 未返回完整评分，"
                        "按保守默认分保留。"
                    ),
                )
            )

        ranked.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return RewriteResult(
            recommended=ranked[0],
            alternatives=ranked[1:],
        )
