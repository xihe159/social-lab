from __future__ import annotations

import inspect


def test_coach_agent_uses_shared_failure_runtime() -> None:
    import app.agents.coach_agent as module

    source = inspect.getsource(module.CoachAgent.run)
    assert "run_agent_call" in source
    assert "REPORT_PREDICTION_DEGRADED" in inspect.getsource(module)
    assert "REPORT_ANALYSIS_DEGRADED" in inspect.getsource(module)
    assert "REPORT_REWRITE_DEGRADED" in inspect.getsource(module)


def test_session_orchestrator_reports_degraded_status() -> None:
    from app.services.session.orchestrator import SessionOrchestrator

    source = inspect.getsource(SessionOrchestrator.handle_message)
    assert "context.degraded" in source, (
        "SessionOrchestrator still reports every non-blocked request as success. "
        "Wire Agent failures into SessionExecutionContext.degraded first."
    )
    assert 'status="degraded"' in source or "status='degraded'" in source


def test_session_context_tracks_failures() -> None:
    from app.services.session.context import SessionExecutionContext

    annotations = getattr(SessionExecutionContext, "__annotations__", {})
    assert "failures" in annotations, (
        "SessionExecutionContext must collect AgentFailure records so HTTP 200 can still be marked degraded."
    )
    assert hasattr(SessionExecutionContext, "degraded"), (
        "SessionExecutionContext needs a degraded property derived from failures."
    )


def test_state_and_memory_stages_use_shared_failure_runtime() -> None:
    from app.services.session.stages.memory_stage import MemoryStage
    from app.services.session.stages.state_stage import StateStage

    state_source = inspect.getsource(StateStage.execute)
    memory_source = inspect.getsource(MemoryStage.execute)
    assert "run_agent_call" in state_source, (
        "StateStage still owns local try/except fallback logic instead of AgentFailurePolicy."
    )
    assert "run_agent_call" in memory_source, (
        "MemoryStage still owns local try/except fallback logic instead of AgentFailurePolicy."
    )
