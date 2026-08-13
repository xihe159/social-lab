from __future__ import annotations

import asyncio
import unittest

from app.core.agent_failure import (
    AgentExecutionError,
    AgentFailureKind,
    AgentFailureMode,
    AgentFailurePolicy,
    run_agent_call,
)


class FakeLLMClientError(RuntimeError):
    pass


# Keep the production classifier robust to wrappers with the canonical name.
FakeLLMClientError.__name__ = "LLMClientError"


class AgentFailureRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_required_failure_escalates(self) -> None:
        async def fail() -> str:
            raise FakeLLMClientError("provider details must not be surfaced")

        with self.assertRaises(AgentExecutionError) as caught:
            await run_agent_call(
                agent="SimulationAgent",
                policy=AgentFailurePolicy(AgentFailureMode.REQUIRED),
                call=fail,
            )
        self.assertEqual(caught.exception.failure.kind, AgentFailureKind.LLM)
        self.assertEqual(caught.exception.failure.mode, AgentFailureMode.REQUIRED)

    async def test_degraded_operational_failure_returns_deterministic_fallback(self) -> None:
        async def fail() -> str:
            raise FakeLLMClientError("provider unavailable")

        outcome = await run_agent_call(
            agent="StateAgent",
            policy=AgentFailurePolicy(
                AgentFailureMode.DEGRADED,
                fallback_name="simulation_state_delta",
            ),
            call=fail,
            fallback=lambda: "fallback-state",
        )
        self.assertEqual(outcome.require_value(), "fallback-state")
        self.assertTrue(outcome.degraded)
        self.assertFalse(outcome.skipped)
        self.assertEqual(outcome.failure.kind, AgentFailureKind.LLM)

    async def test_unexpected_failure_escalates_by_default_even_when_degraded(self) -> None:
        async def fail() -> str:
            raise RuntimeError("programming bug")

        with self.assertRaises(AgentExecutionError) as caught:
            await run_agent_call(
                agent="StateAgent",
                policy=AgentFailurePolicy(
                    AgentFailureMode.DEGRADED,
                    fallback_name="state_delta",
                ),
                call=fail,
                fallback=lambda: "fallback",
            )
        self.assertEqual(caught.exception.failure.kind, AgentFailureKind.UNEXPECTED)

    async def test_best_effort_failure_is_skipped(self) -> None:
        async def fail() -> str:
            raise RuntimeError("audit unavailable")

        outcome = await run_agent_call(
            agent="EvaluationAgent",
            policy=AgentFailurePolicy(
                AgentFailureMode.BEST_EFFORT,
                fallback_on_unexpected=True,
            ),
            call=fail,
        )
        self.assertIsNone(outcome.value)
        self.assertTrue(outcome.skipped)

    async def test_cancelled_error_is_never_swallowed(self) -> None:
        async def cancel() -> str:
            raise asyncio.CancelledError()

        with self.assertRaises(asyncio.CancelledError):
            await run_agent_call(
                agent="MemoryAgent",
                policy=AgentFailurePolicy(
                    AgentFailureMode.DEGRADED,
                    fallback_name="previous_memory",
                ),
                call=cancel,
                fallback=lambda: "fallback",
            )

    async def test_timeout_is_classified(self) -> None:
        async def slow() -> str:
            await asyncio.sleep(0.1)
            return "late"

        outcome = await run_agent_call(
            agent="StrategyAgent",
            policy=AgentFailurePolicy(
                AgentFailureMode.DEGRADED,
                fallback_name="neutral_strategy",
                timeout_seconds=0.001,
            ),
            call=slow,
            fallback=lambda: "neutral",
        )
        self.assertEqual(outcome.require_value(), "neutral")
        self.assertEqual(outcome.failure.kind, AgentFailureKind.TIMEOUT)

    async def test_broken_fallback_escalates(self) -> None:
        async def fail() -> str:
            raise RuntimeError("primary")

        def broken_fallback() -> str:
            raise ValueError("fallback invariant broken")

        with self.assertRaises(AgentExecutionError) as caught:
            await run_agent_call(
                agent="PredictionAgent",
                policy=AgentFailurePolicy(
                    AgentFailureMode.DEGRADED,
                    fallback_name="deterministic_prediction",
                    fallback_on_unexpected=True,
                ),
                call=fail,
                fallback=broken_fallback,
            )
        self.assertEqual(caught.exception.failure.mode, AgentFailureMode.REQUIRED)


if __name__ == "__main__":
    unittest.main()
