from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

import app.agents.simulation_agent_v3_resilient as module


@pytest.mark.asyncio
async def test_strategy_grace_starts_after_core_not_at_task_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = object()

    async def strategy_call():
        # Total task lifetime is longer than the grace configured below.
        # It should still succeed because part of that lifetime overlaps the core.
        await asyncio.sleep(0.06)
        return sentinel

    monkeypatch.setattr(module, "STRATEGY_GRACE_SECONDS", 0.04)

    task = asyncio.create_task(strategy_call())
    # Simulate time spent waiting for Simulation core.
    await asyncio.sleep(0.035)

    outcome = await module._await_strategy_after_core(
        strategy_task=task,
        strategy_request=MagicMock(),
        trace_id="trace-test",
    )

    assert outcome.ok is True
    assert outcome.value is sentinel


@pytest.mark.asyncio
async def test_strategy_timeout_degrades_and_cancels_unfinished_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fallback = object()

    async def strategy_call():
        await asyncio.sleep(1)
        return object()

    monkeypatch.setattr(module, "STRATEGY_GRACE_SECONDS", 0.01)
    monkeypatch.setattr(
        module,
        "fallback_strategy_guidance",
        lambda request: fallback,
    )

    task = asyncio.create_task(strategy_call())
    outcome = await module._await_strategy_after_core(
        strategy_task=task,
        strategy_request=MagicMock(),
        trace_id="trace-test",
    )

    assert outcome.degraded is True
    assert outcome.value is fallback
    assert task.done() is True


def test_development_sync_evaluation_meta_is_visible() -> None:
    result = MagicMock()
    result.evaluation_id = "eval-1"
    result.simulation_success_score = 88
    result.verdict = "accept"
    result.failure_attribution = "none"
    result.hard_errors = []

    meta = module._sync_evaluation_meta(result)

    assert meta.evaluated is True
    assert meta.execution_mode == "synchronous"
    assert meta.background_scheduled is False
    assert meta.initial_score == 88
    assert meta.final_score == 88


def test_failed_best_effort_sync_audit_is_not_reported_as_success() -> None:
    meta = module._sync_evaluation_meta(None)

    assert meta.evaluated is False
    assert meta.execution_mode == "synchronous"
    assert meta.evaluator_failed is True
    assert meta.final_evaluator_failed is True
