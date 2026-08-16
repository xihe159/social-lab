from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from app.agents.evaluation_agent import EvaluationAgent
from app.agents.strategy_agent import StrategyAgent
from app.agents.simulation.context_builder import SimulationContextBuilder
from app.agents.simulation.response_generator import ResponseGenerator
from app.agents.simulation.simulation_decision_engine import SimulationDecisionEngine
from app.agents.simulation.turn_state_analyzer import TurnStateAnalyzer
from app.services.agent_runtime_metrics import AgentRuntimeMetricsStore, agent_runtime_metrics_store
from app.services.evaluation_execution_policy import EvaluationExecutionPolicy
from app.services.evidence_retriever import EvidenceRetriever
from app.services.simulation_adjustment_manager import SimulationAdjustmentManager, simulation_adjustment_manager
from app.services.simulation_turn_store import SimulationTurnStore, simulation_turn_store


@dataclass(slots=True)
class SimulationPipelineServices:
    strategy_agent: StrategyAgent
    turn_state_analyzer: TurnStateAnalyzer
    simulation_decision_engine: SimulationDecisionEngine
    response_generator: ResponseGenerator
    context_builder: SimulationContextBuilder
    evaluation_agent: EvaluationAgent
    turn_store: SimulationTurnStore
    adjustment_manager: SimulationAdjustmentManager
    evaluation_execution_policy: EvaluationExecutionPolicy
    runtime_metrics: AgentRuntimeMetricsStore
    background_tasks: set[asyncio.Task[None]] = field(default_factory=set)

    @classmethod
    def build_default(
        cls,
        *,
        strategy_agent: StrategyAgent | None = None,
        turn_state_analyzer: TurnStateAnalyzer | None = None,
        simulation_decision_engine: SimulationDecisionEngine | None = None,
        response_generator: ResponseGenerator | None = None,
        evidence_retriever: EvidenceRetriever | None = None,
        context_builder: SimulationContextBuilder | None = None,
        evaluation_agent: EvaluationAgent | None = None,
        turn_store: SimulationTurnStore | None = None,
        adjustment_manager: SimulationAdjustmentManager | None = None,
        evaluation_execution_mode: str | None = None,
        runtime_metrics: AgentRuntimeMetricsStore | None = None,
    ) -> "SimulationPipelineServices":
        retriever = evidence_retriever or EvidenceRetriever()
        return cls(
            strategy_agent=strategy_agent or StrategyAgent(mode="active"),
            turn_state_analyzer=turn_state_analyzer or TurnStateAnalyzer(),
            simulation_decision_engine=simulation_decision_engine or SimulationDecisionEngine(),
            response_generator=response_generator or ResponseGenerator(),
            context_builder=context_builder or SimulationContextBuilder(retriever),
            evaluation_agent=evaluation_agent or EvaluationAgent(),
            turn_store=turn_store or simulation_turn_store,
            adjustment_manager=adjustment_manager or simulation_adjustment_manager,
            evaluation_execution_policy=EvaluationExecutionPolicy(evaluation_execution_mode),
            runtime_metrics=runtime_metrics or agent_runtime_metrics_store,
        )
