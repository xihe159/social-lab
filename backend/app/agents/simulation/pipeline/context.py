from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.core.agent_failure import AgentFailure

from app.schemas.evaluation import SessionEvaluationMeta
from app.schemas.session import SessionMessageRequest, SessionMessageResponse
from app.schemas.simulation_decision import DecisionMessage, TurnDecisionResult
from app.schemas.simulation_generation import GeneratedResponse, ResponseGenerationInput
from app.schemas.simulation_guidance import SimulationDecisionOutput
from app.schemas.simulation_state import SimulationState
from app.schemas.strategy import TargetResponseGuidance, TargetResponseStrategyRequest
from app.schemas.turn_state import TurnStateAnalysisResult


@dataclass(slots=True)
class PipelineRuntimeFlags:
    """Only operational facts belong here; business state stays in schemas."""

    turn_state_fallback_used: bool = False
    strategy_fallback_used: bool = False
    decision_fallback_used: bool = False
    generator_retry_count: int = 0
    generator_fallback_used: bool = False
    evaluation_call_count: int = 0


@dataclass(slots=True)
class SimulationCandidate:
    """Immutable-enough handoff between Decide -> Generate -> Audit stages."""

    strategy_guidance: TargetResponseGuidance
    simulation_decision: SimulationDecisionOutput
    decision_result: TurnDecisionResult
    generation_input: ResponseGenerationInput | None
    generated: GeneratedResponse


@dataclass(slots=True)
class SimulationPipelineContext:
    """
    Explicit per-turn state shared by pipeline stages.

    The old SimulationAgentV2 kept these values as local variables in a ~500 line
    run() method. Making them explicit gives every stage a narrow contract and makes
    individual stages replaceable/testable without re-running the full workflow.
    """

    request: SessionMessageRequest
    defer_background: Callable[..., None] | None = None
    pipeline_started_at: float = field(default_factory=time.perf_counter)

    persona_id: str = ""
    session_id: str = ""
    trace_id: str = ""
    turn_id: str = ""

    persona_v2: Any = None
    current_state: SimulationState | None = None
    recent_turns: list[DecisionMessage] = field(default_factory=list)
    evidence_context: Any = None
    retrieval: Any = None

    adjustment_context: Any = None
    active_adjustments: Any = None
    resulting_adjustments: Any = None
    adjustment_observation: Any = None
    adjustment_remaining_turns: int = 0

    turn_state_result: TurnStateAnalysisResult | None = None
    strategy_request: TargetResponseStrategyRequest | None = None
    strategy_guidance: TargetResponseGuidance | None = None
    simulation_decision: SimulationDecisionOutput | None = None
    decision_result: TurnDecisionResult | None = None
    generation_input: ResponseGenerationInput | None = None
    generated: GeneratedResponse | None = None
    candidate: SimulationCandidate | None = None

    evaluation_meta: SessionEvaluationMeta = field(default_factory=SessionEvaluationMeta)
    response: SessionMessageResponse | None = None
    flags: PipelineRuntimeFlags = field(default_factory=PipelineRuntimeFlags)
    failures: list[AgentFailure] = field(default_factory=list)

    def record_failure(self, failure: AgentFailure) -> None:
        self.failures.append(failure)

    @property
    def degraded(self) -> bool:
        return bool(self.failures)

    def require_current_state(self) -> SimulationState:
        if self.current_state is None:
            raise RuntimeError("PrepareStage did not populate current_state")
        return self.current_state

    def require_turn_state(self) -> TurnStateAnalysisResult:
        if self.turn_state_result is None:
            raise RuntimeError("TurnAnalysisStage did not populate turn_state_result")
        return self.turn_state_result

    def require_strategy_request(self) -> TargetResponseStrategyRequest:
        if self.strategy_request is None:
            raise RuntimeError("StrategyStage did not populate strategy_request")
        return self.strategy_request

    def require_strategy_guidance(self) -> TargetResponseGuidance:
        if self.strategy_guidance is None:
            raise RuntimeError("StrategyStage did not populate strategy_guidance")
        return self.strategy_guidance

    def require_decision(self) -> TurnDecisionResult:
        if self.decision_result is None:
            raise RuntimeError("DecisionStage did not populate decision_result")
        return self.decision_result

    def require_generated(self) -> GeneratedResponse:
        if self.generated is None:
            raise RuntimeError("GenerationStage did not populate generated")
        return self.generated

    def require_response(self) -> SessionMessageResponse:
        if self.response is None:
            raise RuntimeError("AssemblyStage did not populate response")
        return self.response
