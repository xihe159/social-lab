from __future__ import annotations

from app.agents import failure_policies as policies
from app.core.agent_failure import AgentFailureMode


def test_session_failure_modes() -> None:
    assert policies.SESSION_SAFETY_REQUIRED.mode is AgentFailureMode.REQUIRED
    assert policies.SESSION_SIMULATION_REQUIRED.mode is AgentFailureMode.REQUIRED
    assert policies.SESSION_STATE_DEGRADED.mode is AgentFailureMode.DEGRADED
    assert policies.SESSION_MEMORY_DEGRADED.mode is AgentFailureMode.DEGRADED


def test_report_failure_modes() -> None:
    assert policies.REPORT_PREDICTION_DEGRADED.mode is AgentFailureMode.DEGRADED
    assert policies.REPORT_ANALYSIS_DEGRADED.mode is AgentFailureMode.DEGRADED
    assert policies.REPORT_REWRITE_DEGRADED.mode is AgentFailureMode.DEGRADED


def test_simulation_internal_failure_modes() -> None:
    assert policies.SIMULATION_CORE_REQUIRED.mode is AgentFailureMode.REQUIRED
    assert policies.STRATEGY_ADVISORY_DEGRADED.mode is AgentFailureMode.DEGRADED
    assert policies.EVALUATION_AUDIT_BEST_EFFORT.mode is AgentFailureMode.BEST_EFFORT
    assert policies.TURN_ANALYSIS_DEGRADED.mode is AgentFailureMode.DEGRADED
    assert policies.SIMULATION_DECISION_DEGRADED.mode is AgentFailureMode.DEGRADED
    assert policies.GENERATION_FIRST_ATTEMPT_BEST_EFFORT.mode is AgentFailureMode.BEST_EFFORT
    assert policies.GENERATION_FINAL_DEGRADED.mode is AgentFailureMode.DEGRADED


def test_direct_agent_api_remains_required() -> None:
    assert policies.DIRECT_AGENT_REQUIRED.mode is AgentFailureMode.REQUIRED


def test_expected_fallback_names_are_stable() -> None:
    assert policies.SESSION_STATE_DEGRADED.fallback_name == "simulation_agent_state_delta"
    assert policies.SESSION_MEMORY_DEGRADED.fallback_name == "previous_memory"
    assert policies.STRATEGY_ADVISORY_DEGRADED.fallback_name == "neutral_strategy_guidance"
    assert policies.EVALUATION_AUDIT_BEST_EFFORT.fallback_name == "skip_evaluation_audit"
