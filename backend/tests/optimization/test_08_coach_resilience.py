from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class LLMClientError(Exception):
    pass


class _FailPrediction:
    async def run(self, request):
        raise LLMClientError("prediction unavailable")


class _GoodAnalysis:
    async def run(self, *, request):
        return "analysis-ok"


class _GoodRewrite:
    async def run(self, *, request, prediction, analysis):
        assert prediction == "prediction-fallback"
        assert analysis == "analysis-ok"
        return "rewrite-ok"


class _Assembler:
    def run(self, *, request, prediction, analysis, rewrite):
        return {
            "prediction": prediction,
            "analysis": analysis,
            "rewrite": rewrite,
        }


@pytest.mark.asyncio
async def test_one_report_subagent_failure_does_not_destroy_report(monkeypatch) -> None:
    import app.agents.coach_agent as module

    monkeypatch.setattr(
        module,
        "fallback_prediction",
        lambda agent, request: "prediction-fallback",
    )

    coach = module.CoachAgent(
        prediction_agent=_FailPrediction(),
        analysis_agent=_GoodAnalysis(),
        rewrite_agent=_GoodRewrite(),
        report_assembler=_Assembler(),
    )
    result = await coach.run(MagicMock(name="ReportRequest"))
    assert result == {
        "prediction": "prediction-fallback",
        "analysis": "analysis-ok",
        "rewrite": "rewrite-ok",
    }
