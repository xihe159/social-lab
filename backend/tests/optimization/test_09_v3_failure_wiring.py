from __future__ import annotations

import inspect


def test_production_v3_uses_shared_failure_contract() -> None:
    from app.agents.simulation_agent_factory import create_simulation_agent

    version, agent = create_simulation_agent("v3")
    assert version == "v3"
    module = inspect.getmodule(agent.__class__)
    assert module is not None
    source = inspect.getsource(module)
    assert "run_agent_call" in source, (
        "Factory-created V3 does not use the shared AgentFailure runtime. "
        "If simulation_agent_v3_resilient.py exists, wire it into the factory or merge it into simulation_agent_v3.py."
    )
    assert "STRATEGY_ADVISORY_DEGRADED" in source
    assert "EVALUATION_AUDIT_BEST_EFFORT" in source
