from __future__ import annotations

from app.agents.simulation.decision_engine import apply_simulation_state_delta
from app.agents.simulation.prompts import (
    TURN_STATE_ANALYZER_SYSTEM_PROMPT,
    TURN_STATE_PROMPT_VERSION,
    build_turn_state_analysis_prompt,
)
from app.llm.client import generate_structured
from app.schemas.simulation_decision import SimulationStateDelta
from app.schemas.turn_state import (
    TurnStateAnalysis,
    TurnStateAnalysisRequest,
    TurnStateAnalysisResult,
)


_MAJOR_EVENTS = {
    "severe_insult",
    "major_deception",
    "serious_boundary_violation",
    "严重侮辱",
    "重大欺骗",
    "严重边界侵犯",
}


class TurnStateAnalyzer:
    """Understand user behavior and state impact without choosing a reply."""

    prompt_version = TURN_STATE_PROMPT_VERSION

    async def run(
        self,
        request: TurnStateAnalysisRequest,
    ) -> TurnStateAnalysisResult:
        analysis = await generate_structured(
            system_prompt=TURN_STATE_ANALYZER_SYSTEM_PROMPT,
            user_prompt=build_turn_state_analysis_prompt(request),
            output_model=TurnStateAnalysis,
            temperature=0.2,
        )
        return self.post_process(analysis=analysis, request=request)

    def post_process(
        self,
        *,
        analysis: TurnStateAnalysis,
        request: TurnStateAnalysisRequest,
    ) -> TurnStateAnalysisResult:
        major = bool(
            {item.strip().lower() for item in analysis.detected_events}
            & _MAJOR_EVENTS
        )
        limit = 0.25 if major else 0.15
        for field_name in type(analysis.state_delta).model_fields:
            value = float(getattr(analysis.state_delta, field_name))
            setattr(
                analysis.state_delta,
                field_name,
                round(max(-limit, min(limit, value)), 3),
            )

        simulation_delta = SimulationStateDelta(
            **analysis.state_delta.model_dump()
        )
        updated_state = apply_simulation_state_delta(
            state=request.current_state,
            delta=simulation_delta,
        )
        return TurnStateAnalysisResult(
            analysis=analysis,
            updated_state=updated_state,
        )
