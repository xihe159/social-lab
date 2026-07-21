from __future__ import annotations

import asyncio
import logging
import time

from app.agents.analysis_agent import AnalysisAgent
from app.agents.prediction_agent import PredictionAgent
from app.agents.rewrite_agent import RewriteAgent
from app.schemas.analysis import ConversationProcessAnalysis
from app.schemas.prediction import PredictionResult
from app.schemas.report import ReportRequest, ReportResponse
from app.schemas.rewrite import RewriteResult


logger = logging.getLogger(__name__)


class ReportAssembler:
    """
    确定性组装报告，保持三个 Agent 的职责边界。

    - PredictionAgent：成功评分、结果和影响因素；
    - AnalysisAgent：逐句观察、状态归因和评价；
    - RewriteAgent：全部改进、改写和下一步。
    """

    def run(
        self,
        *,
        request: ReportRequest,
        prediction: PredictionResult,
        analysis: ConversationProcessAnalysis,
        rewrite: RewriteResult,
    ) -> ReportResponse:
        return ReportResponse(
            success_probability=prediction.success_probability,
            probability_low=prediction.probability_low,
            probability_high=prediction.probability_high,
            confidence_score=prediction.confidence_score,
            confidence=prediction.confidence,
            evidence_sufficiency=prediction.evidence_sufficiency,
            likely_outcome=prediction.likely_outcome,
            probability_reasoning=prediction.probability_reasoning,
            outcome_distribution=prediction.outcome_distribution,
            main_influence_factors=prediction.main_influence_factors,
            prediction_trace=prediction.calculation_trace,
            calibration_version=prediction.calibration_version,

            conversation_analysis=analysis,
            strengths=analysis.strengths,
            problems=analysis.problems,
            key_risks=self._merge_key_risks(
                analysis=analysis,
                prediction=prediction,
            ),

            suggested_rewrite=rewrite.suggested_rewrite,
            sentence_rewrites=rewrite.sentence_rewrites,
            rewrite_variants=rewrite.variants,
            next_step_advice=rewrite.next_step_advice,
            do_not_say=rewrite.do_not_say,
        )

    @staticmethod
    def _merge_key_risks(
        *,
        analysis: ConversationProcessAnalysis,
        prediction: PredictionResult,
    ) -> list[str]:
        risks = list(analysis.key_risks)

        for factor in prediction.main_influence_factors:
            if (
                factor.direction == "negative"
                and factor.importance >= 4
            ):
                risks.append(
                    f"{factor.factor_name}明显拉低模拟成功评分："
                    f"{factor.explanation}"
                )

        cleaned: list[str] = []
        for risk in risks:
            item = risk.strip()
            if item and item not in cleaned:
                cleaned.append(item[:300])
        return cleaned[:6]


class CoachAgent:
    """
    报告编排入口。

    执行顺序：
    1. PredictionAgent；
    2. AnalysisAgent；
    3. RewriteAgent；
    4. ReportAssembler。
    """

    def __init__(self) -> None:
        self.prediction_agent = PredictionAgent()
        self.analysis_agent = AnalysisAgent()
        self.rewrite_agent = RewriteAgent()
        self.report_assembler = ReportAssembler()

    async def run(
        self,
        request: ReportRequest,
    ) -> ReportResponse:
        started = time.perf_counter()

        parallel_phase = time.perf_counter()
        prediction, analysis = await asyncio.gather(
            self.prediction_agent.run(request),
            self.analysis_agent.run(request=request),
        )
        logger.info(
            "PredictionAgent and AnalysisAgent finished in %.2fs",
            time.perf_counter() - parallel_phase,
        )

        phase = time.perf_counter()
        rewrite = await self.rewrite_agent.run(
            request=request,
            prediction=prediction,
            analysis=analysis,
        )
        logger.info(
            "RewriteAgent finished in %.2fs",
            time.perf_counter() - phase,
        )

        report = self.report_assembler.run(
            request=request,
            prediction=prediction,
            analysis=analysis,
            rewrite=rewrite,
        )

        logger.info(
            "CoachAgent report finished in %.2fs",
            time.perf_counter() - started,
        )
        return report
