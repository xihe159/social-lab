from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.agents.failure_policies import (
    REPORT_ANALYSIS_DEGRADED,
    REPORT_PREDICTION_DEGRADED,
    REPORT_REWRITE_DEGRADED,
)
from app.agents.fallbacks import (
    fallback_analysis,
    fallback_prediction,
    fallback_rewrite,
)
from app.agents.policy_agents import PolicyAnalysisAgent
from app.agents.prediction_agent import PredictionAgent
from app.agents.rewrite_agent import RewriteAgent
from app.core.agent_failure import AgentFailure, run_agent_call
from app.schemas.analysis import ConversationProcessAnalysis
from app.schemas.prediction import PredictionResult
from app.schemas.report import ReportRequest, ReportResponse
from app.schemas.rewrite import RewriteResult

logger = logging.getLogger(__name__)


class ReportAssembler:
    """Deterministic report assembly; Agent ownership remains unchanged."""

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
            if factor.direction == "negative" and factor.importance >= 4:
                risks.append(
                    f"{factor.factor_name}明显拉低模拟成功评分：{factor.explanation}"
                )
        cleaned: list[str] = []
        for risk in risks:
            item = risk.strip()
            if item and item not in cleaned:
                cleaned.append(item[:300])
        return cleaned[:6]


class CoachAgent:
    """Resilient report pipeline.

    Prediction / Analysis / Rewrite are all DEGRADED stages. A provider outage no
    longer destroys the entire report; deterministic fallbacks preserve schema and
    make the degraded status visible in structured logs.
    """

    def __init__(
        self,
        *,
        prediction_agent: PredictionAgent | None = None,
        analysis_agent: Any | None = None,
        rewrite_agent: RewriteAgent | None = None,
        report_assembler: ReportAssembler | None = None,
    ) -> None:
        self.prediction_agent = prediction_agent or PredictionAgent()
        self.analysis_agent = analysis_agent or PolicyAnalysisAgent()
        self.rewrite_agent = rewrite_agent or RewriteAgent()
        self.report_assembler = report_assembler or ReportAssembler()

    async def run(self, request: ReportRequest) -> ReportResponse:
        started = time.perf_counter()
        failures: list[AgentFailure] = []

        prediction_call = run_agent_call(
            agent="PredictionAgent",
            policy=REPORT_PREDICTION_DEGRADED,
            call=lambda: self.prediction_agent.run(request),
            fallback=lambda: fallback_prediction(self.prediction_agent, request),
            on_failure=failures.append,
        )
        analysis_call = run_agent_call(
            agent="AnalysisAgent",
            policy=REPORT_ANALYSIS_DEGRADED,
            call=lambda: self.analysis_agent.run(request=request),
            fallback=lambda: fallback_analysis(self.analysis_agent, request),
            on_failure=failures.append,
        )

        prediction_outcome, analysis_outcome = await asyncio.gather(
            prediction_call,
            analysis_call,
        )
        prediction = prediction_outcome.require_value()
        analysis = analysis_outcome.require_value()

        rewrite_outcome = await run_agent_call(
            agent="RewriteAgent",
            policy=REPORT_REWRITE_DEGRADED,
            call=lambda: self.rewrite_agent.run(
                request=request,
                prediction=prediction,
                analysis=analysis,
            ),
            fallback=lambda: fallback_rewrite(self.rewrite_agent, request),
            on_failure=failures.append,
        )
        rewrite = rewrite_outcome.require_value()

        report = self.report_assembler.run(
            request=request,
            prediction=prediction,
            analysis=analysis,
            rewrite=rewrite,
        )
        logger.info(
            "coach_report_finished",
            extra={
                "duration_ms": round((time.perf_counter() - started) * 1000),
                "status": "degraded" if failures else "success",
                "degraded_agents": [item.agent for item in failures],
                "failure_kinds": [item.kind.value for item in failures],
            },
        )
        return report
