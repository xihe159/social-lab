from __future__ import annotations

import logging
from collections.abc import Callable, Iterable

from app.schemas.session import SessionMessageRequest, SessionMessageResponse

from .context import SimulationPipelineContext
from .services import SimulationPipelineServices
from .stages import (
    AssemblyStage,
    DecisionStage,
    EvaluationAuditStage,
    GenerationStage,
    PersistenceStage,
    PrepareStage,
    SimulationPipelineStage,
    StrategyStage,
    TurnAnalysisStage,
)

logger = logging.getLogger(__name__)


class SimulationPipeline:
    """
    Small workflow engine for one simulation turn.

    It intentionally knows only stage order. It does not know Persona semantics,
    response policy rules, evaluation rules, or persistence details.
    """

    def __init__(self, stages: Iterable[SimulationPipelineStage]) -> None:
        self.stages = tuple(stages)
        if not self.stages:
            raise ValueError("SimulationPipeline requires at least one stage")

    async def run(
        self,
        request: SessionMessageRequest,
        *,
        defer_background: Callable[..., None] | None = None,
    ) -> SessionMessageResponse:
        context = SimulationPipelineContext(
            request=request,
            defer_background=defer_background,
        )
        for stage in self.stages:
            logger.debug(
                "simulation_pipeline_stage_started",
                extra={
                    "stage": stage.name,
                    "trace_id": context.trace_id or None,
                    "session_id": context.session_id or None,
                },
            )
            context = await stage.execute(context)
        return context.require_response()


def build_default_simulation_pipeline(
    services: SimulationPipelineServices,
) -> SimulationPipeline:
    """
    Canonical V2 pipeline.

    Stage order is the only orchestration policy kept in one place. Future variants
    can replace a single stage or create a different ordered list without subclassing
    SimulationAgentV2.
    """

    return SimulationPipeline(
        (
            PrepareStage(services),
            TurnAnalysisStage(services),
            StrategyStage(services),
            DecisionStage(services),
            GenerationStage(services),
            EvaluationAuditStage(services),
            AssemblyStage(services),
            PersistenceStage(services),
        )
    )
