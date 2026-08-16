from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from app.agents.evaluation_agent import EvaluationAgent
from app.agents.strategy_agent import StrategyAgent
from app.agents.simulation.context_builder import SimulationContextBuilder
from app.agents.simulation.response_generator import ResponseGenerator
from app.agents.simulation.simulation_decision_engine import SimulationDecisionEngine
from app.agents.simulation.turn_state_analyzer import TurnStateAnalyzer
from app.agents.simulation.pipeline import (
    SimulationPipeline,
    SimulationPipelineServices,
    build_default_simulation_pipeline,
)
from app.schemas.session import SessionMessageRequest, SessionMessageResponse
from app.services.agent_runtime_metrics import AgentRuntimeMetricsStore
from app.services.evidence_retriever import EvidenceRetriever
from app.services.simulation_adjustment_manager import SimulationAdjustmentManager
from app.services.simulation_turn_store import SimulationTurnStore

logger = logging.getLogger(__name__)


class SimulationAgentV2:
    """
    Compatibility facade over the V2 simulation pipeline.

    Old V2 was itself the workflow engine. This class now owns only dependency
    injection and delegates one turn to SimulationPipeline.

    Evaluation is audit-only for the current turn. It may feed bounded temporary
    adjustments into later turns, but it cannot replace the reply that the persona
    decision/generation stages already produced.
    """

    version = "v2.6-pipeline-audit"

    def __init__(
        self,
        strategy_agent: StrategyAgent | None = None,
        turn_state_analyzer: TurnStateAnalyzer | None = None,
        simulation_decision_engine: SimulationDecisionEngine | None = None,
        response_generator: ResponseGenerator | None = None,
        evidence_retriever: EvidenceRetriever | None = None,
        context_builder: SimulationContextBuilder | None = None,
        evaluation_agent: EvaluationAgent | None = None,
        feedback_loop: Any | None = None,
        turn_store: SimulationTurnStore | None = None,
        adjustment_manager: SimulationAdjustmentManager | None = None,
        evaluation_execution_mode: str | None = None,
        runtime_metrics: AgentRuntimeMetricsStore | None = None,
        pipeline: SimulationPipeline | None = None,
    ) -> None:
        if feedback_loop is not None:
            logger.warning(
                "simulation_v2_feedback_loop_argument_is_deprecated",
                extra={
                    "reason": (
                        "Evaluation is audit-only; current-turn rewrite/replan was removed "
                        "to keep response ownership single and deterministic."
                    )
                },
            )

        self.services = SimulationPipelineServices.build_default(
            strategy_agent=strategy_agent,
            turn_state_analyzer=turn_state_analyzer,
            simulation_decision_engine=simulation_decision_engine,
            response_generator=response_generator,
            evidence_retriever=evidence_retriever,
            context_builder=context_builder,
            evaluation_agent=evaluation_agent,
            turn_store=turn_store,
            adjustment_manager=adjustment_manager,
            evaluation_execution_mode=evaluation_execution_mode,
            runtime_metrics=runtime_metrics,
        )
        self.pipeline = pipeline or build_default_simulation_pipeline(self.services)

    async def run(
        self,
        request: SessionMessageRequest,
        *,
        defer_background: Callable[..., None] | None = None,
    ) -> SessionMessageResponse:
        return await self.pipeline.run(
            request,
            defer_background=defer_background,
        )
