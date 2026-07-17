from __future__ import annotations

import asyncio
import logging
import time

from app.agents.analysis_agent import AnalysisAgent
from app.agents.prediction_agent import PredictionAgent
from app.agents.rewrite_agent import RewriteAgent
from app.schemas.coach import (
    AnalysisResult,
    PredictionResult,
    RewriteResult,
)
from app.schemas.report import (
    ReportRequest,
    ReportResponse,
)


logger = logging.getLogger(__name__)


class ReportAssembler:
    """
    将三个 Agent 的结果组装成现有 ReportResponse。

    职责边界：
    - PredictionAgent → success_probability / likely_outcome；
    - AnalysisAgent → 主要影响因素、优劣势、风险、下一步建议；
    - RewriteAgent → suggested_rewrite。
    """

    def run(
        self,
        request: ReportRequest,
        prediction: PredictionResult,
        analysis: AnalysisResult,
        rewrite: RewriteResult,
    ) -> ReportResponse:
        # PredictionAgent 的报告区域只保留：
        # 1. 本轮沟通成功率；
        # 2. 当前最可能结果；
        # 3. 概率判断依据。
        #
        # 不在 likely_outcome 中拼接影响因素、行动建议或改写内容。
        likely_outcome = (
            f"{prediction.likely_outcome}\n\n"
            f"量化基线："
            f"{prediction.baseline_probability}%；"
            f"对话证据校正："
            f"{prediction.model_adjustment:+d}；"
            f"最终模拟成功率："
            f"{prediction.success_probability}%；"
            f"置信度："
            f"{prediction.confidence}"
            f"（{prediction.confidence_score}/100）。"
            f"\n\n概率判断依据："
            f"{prediction.probability_reasoning}"
        )

        # 主要影响因素完全来自 AnalysisAgent。
        # 每一项只描述：
        # - 当前因素；
        # - 正向、负向或混合作用；
        # - 重要程度；
        # - 对当前沟通造成的影响；
        # - 对话证据。
        #
        # 不在影响因素中加入下一步建议。
        factor_lines = [
            (
                f"{item.name}"
                f"（{item.direction}，"
                f"重要性 {item.importance}/5）："
                f"{item.impact}"
                + (
                    f" 证据：{item.evidence_quote}"
                    if item.evidence_quote
                    else ""
                )
            )
            for item in analysis.influence_factors[:5]
        ]

        positive_factors = [
            line
            for line, item in zip(
                factor_lines,
                analysis.influence_factors[:5],
            )
            if item.direction == "positive"
        ]

        negative_factors = [
            line
            for line, item in zip(
                factor_lines,
                analysis.influence_factors[:5],
            )
            if item.direction in {
                "negative",
                "mixed",
            }
        ]

        strengths = [
            *analysis.strengths[:4],
            *positive_factors[:2],
        ]

        problems = [
            *analysis.problems[:3],
            *negative_factors[:2],
            f"核心瓶颈：{analysis.primary_bottleneck}",
        ]

        key_risks = list(
            analysis.key_risks[:4]
        )

        reasonability = analysis.reasonability

        key_risks.append(
            f"需求合理性："
            f"{reasonability.label}"
            f"（{reasonability.overall_score}/100）。"
            f"{reasonability.summary}"
        )

        return ReportResponse(
            # PredictionAgent：成功率。
            success_probability=(
                prediction.success_probability
            ),

            # PredictionAgent：可能结果和概率判断依据。
            likely_outcome=self._truncate(
                likely_outcome,
                1800,
            ),

            # AnalysisAgent：正向影响因素和表达优势。
            strengths=self._clean_list(
                strengths,
                6,
                "能够主动表达沟通目标。",
            ),

            # AnalysisAgent：负向影响因素、表达问题和核心瓶颈。
            problems=self._clean_list(
                problems,
                6,
                "表达仍需要更具体地回应对方顾虑。",
            ),

            # AnalysisAgent：风险与需求合理性。
            key_risks=self._clean_list(
                key_risks,
                5,
                "模拟结果存在不确定性。",
            ),

            # RewriteAgent：可直接参考或复制的推荐表达。
            suggested_rewrite=self._truncate(
                rewrite.recommended.candidate.text,
                1000,
            ),

            # AnalysisAgent：下一步行动。
            #
            # 不再拼接：
            # - RewriteAgent 推荐理由；
            # - 其他候选版本；
            # - do_not_say。
            #
            # 前端可以将本字段与 suggested_rewrite
            # 放在同一张“下一步与推荐改写”卡片中展示。
            next_step_advice=self._truncate(
                analysis.next_step_advice,
                1200,
            ),
        )

    @staticmethod
    def _truncate(
        value: str,
        limit: int,
    ) -> str:
        value = (value or "").strip()

        if len(value) <= limit:
            return value

        return (
            value[: limit - 1].rstrip()
            + "…"
        )

    @staticmethod
    def _clean_list(
        values: list[str],
        limit: int,
        fallback: str,
    ) -> list[str]:
        cleaned: list[str] = []

        for value in values:
            text = str(value).strip()

            if text and text not in cleaned:
                cleaned.append(text[:260])

        if not cleaned:
            cleaned.append(fallback)

        return cleaned[:limit]


class CoachAgent:
    """
    CoachAgent 只负责编排。

    PredictionAgent 和 AnalysisAgent 相互独立，可以并行执行：
    - PredictionAgent：成功率和可能结果；
    - AnalysisAgent：完整分析与下一步策略。

    RewriteAgent 必须等待 AnalysisAgent，
    因为推荐话术需要消费分析结论。
    """

    def __init__(self) -> None:
        self.prediction_agent = PredictionAgent()
        self.analysis_agent = AnalysisAgent()
        self.rewrite_agent = RewriteAgent()
        self.assembler = ReportAssembler()

    async def run(
        self,
        request: ReportRequest,
    ) -> ReportResponse:
        started = time.perf_counter()

        # PredictionAgent 和 AnalysisAgent 互不依赖，
        # 因此并行执行，缩短报告生成时间。
        prediction_task = asyncio.create_task(
            self.prediction_agent.run(request)
        )
        analysis_task = asyncio.create_task(
            self.analysis_agent.run(request)
        )

        prediction, analysis = await asyncio.gather(
            prediction_task,
            analysis_task,
        )

        logger.info(
            "PredictionAgent and AnalysisAgent "
            "finished in %.2fs",
            time.perf_counter() - started,
        )

        rewrite_started = time.perf_counter()

        # RewriteAgent 消费 AnalysisAgent 的：
        # - 核心瓶颈；
        # - 下一步行动；
        # - 逐句诊断；
        # - 风险和避免表达；
        # 将其转换成具体推荐话术。
        rewrite = await self.rewrite_agent.run(
            request,
            analysis,
        )

        logger.info(
            "RewriteAgent finished in %.2fs",
            time.perf_counter()
            - rewrite_started,
        )

        report = self.assembler.run(
            request,
            prediction,
            analysis,
            rewrite,
        )

        logger.info(
            "CoachAgent finished in %.2fs",
            time.perf_counter() - started,
        )

        return report

