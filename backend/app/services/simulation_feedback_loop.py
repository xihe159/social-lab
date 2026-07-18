from __future__ import annotations

from dataclasses import dataclass

from app.schemas.evaluation import (
    EvaluationVerdict,
    FeedbackAction,
    SimulationEvaluationResponse,
)
from app.schemas.feedback import InternalCorrection


MAX_FEEDBACK_CORRECTIONS = 1


@dataclass(frozen=True)
class FeedbackPlan:
    action: FeedbackAction
    strategy_correction: InternalCorrection | None = None
    simulation_correction: InternalCorrection | None = None


class SimulationFeedbackLoop:
    """Choose one correction route; it never generates or evaluates content."""

    max_corrections = MAX_FEEDBACK_CORRECTIONS

    def plan(
        self,
        evaluation: SimulationEvaluationResponse,
        *,
        corrections_used: int,
    ) -> FeedbackPlan:
        if corrections_used >= self.max_corrections:
            return FeedbackPlan(action=FeedbackAction.NONE)

        if evaluation.verdict == EvaluationVerdict.REVISE_SIMULATION:
            if evaluation.correction_for_simulation is None:
                return FeedbackPlan(action=FeedbackAction.NONE)
            return FeedbackPlan(
                action=FeedbackAction.REVISE_SIMULATION,
                simulation_correction=evaluation.correction_for_simulation,
            )

        if evaluation.verdict == EvaluationVerdict.REPLAN_AND_REGENERATE:
            if evaluation.correction_for_strategy is not None:
                return FeedbackPlan(
                    action=FeedbackAction.REPLAN_AND_REGENERATE,
                    strategy_correction=evaluation.correction_for_strategy,
                    simulation_correction=evaluation.correction_for_simulation,
                )
            if evaluation.correction_for_simulation is not None:
                return FeedbackPlan(
                    action=FeedbackAction.REVISE_SIMULATION,
                    simulation_correction=evaluation.correction_for_simulation,
                )

        return FeedbackPlan(action=FeedbackAction.NONE)
