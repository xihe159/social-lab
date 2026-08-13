from __future__ import annotations

import asyncio

import pytest

from app.core.agent_failure import (
    AgentExecutionError,
    AgentFailureKind,
    AgentFailureMode,
    AgentFailurePolicy,
    run_agent_call,
)


class LLMClientError(Exception):
    """Name intentionally matches the runtime classifier without calling a real LLM."""


async def _raise_llm() -> int:
    raise LLMClientError("provider payload must never leak into safe failure metadata")


async def _raise_unexpected() -> int:
    raise TypeError("programming bug")


@pytest.mark.asyncio
async def test_required_failure_raises_stable_execution_error() -> None:
    with pytest.raises(AgentExecutionError) as captured:
        await run_agent_call(
            agent="RequiredAgent",
            policy=AgentFailurePolicy(AgentFailureMode.REQUIRED),
            call=_raise_llm,
        )
    assert captured.value.failure.kind is AgentFailureKind.LLM
    assert captured.value.failure.mode is AgentFailureMode.REQUIRED


@pytest.mark.asyncio
async def test_degraded_llm_failure_uses_fallback() -> None:
    outcome = await run_agent_call(
        agent="StateAgent",
        policy=AgentFailurePolicy(
            AgentFailureMode.DEGRADED,
            fallback_name="previous_state",
        ),
        call=_raise_llm,
        fallback=lambda: 42,
    )
    assert outcome.value == 42
    assert outcome.degraded is True
    assert outcome.skipped is False
    assert outcome.failure is not None
    assert outcome.failure.kind is AgentFailureKind.LLM


@pytest.mark.asyncio
async def test_best_effort_failure_is_skipped() -> None:
    outcome = await run_agent_call(
        agent="EvaluationAgent",
        policy=AgentFailurePolicy(
            AgentFailureMode.BEST_EFFORT,
            fallback_name="skip_audit",
        ),
        call=_raise_llm,
    )
    assert outcome.value is None
    assert outcome.skipped is True
    assert outcome.failure is not None


@pytest.mark.asyncio
async def test_timeout_is_classified() -> None:
    async def slow() -> int:
        await asyncio.sleep(0.05)
        return 1

    outcome = await run_agent_call(
        agent="SlowAgent",
        policy=AgentFailurePolicy(
            AgentFailureMode.DEGRADED,
            fallback_name="timeout_fallback",
            timeout_seconds=0.001,
        ),
        call=slow,
        fallback=lambda: 9,
    )
    assert outcome.value == 9
    assert outcome.failure is not None
    assert outcome.failure.kind is AgentFailureKind.TIMEOUT


@pytest.mark.asyncio
async def test_unexpected_failure_is_fatal_by_default() -> None:
    with pytest.raises(AgentExecutionError) as captured:
        await run_agent_call(
            agent="BuggyAgent",
            policy=AgentFailurePolicy(
                AgentFailureMode.DEGRADED,
                fallback_name="fallback",
            ),
            call=_raise_unexpected,
            fallback=lambda: 1,
        )
    assert captured.value.failure.kind is AgentFailureKind.UNEXPECTED


@pytest.mark.asyncio
async def test_auxiliary_policy_can_opt_in_to_unexpected_fallback() -> None:
    outcome = await run_agent_call(
        agent="AdvisoryAgent",
        policy=AgentFailurePolicy(
            AgentFailureMode.DEGRADED,
            fallback_name="neutral_advice",
            fallback_on_unexpected=True,
        ),
        call=_raise_unexpected,
        fallback=lambda: "neutral",
    )
    assert outcome.value == "neutral"
    assert outcome.degraded is True


@pytest.mark.asyncio
async def test_broken_fallback_escalates() -> None:
    def broken_fallback() -> int:
        raise ValueError("fallback invariant broken")

    with pytest.raises(AgentExecutionError) as captured:
        await run_agent_call(
            agent="DegradedAgent",
            policy=AgentFailurePolicy(
                AgentFailureMode.DEGRADED,
                fallback_name="broken",
            ),
            call=_raise_llm,
            fallback=broken_fallback,
        )
    assert captured.value.failure.mode is AgentFailureMode.REQUIRED
    assert captured.value.failure.kind is AgentFailureKind.UNEXPECTED


@pytest.mark.asyncio
async def test_cancelled_error_is_never_converted_to_fallback() -> None:
    async def cancelled() -> int:
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await run_agent_call(
            agent="CancelledAgent",
            policy=AgentFailurePolicy(
                AgentFailureMode.DEGRADED,
                fallback_name="must_not_run",
                fallback_on_unexpected=True,
            ),
            call=cancelled,
            fallback=lambda: 123,
        )
