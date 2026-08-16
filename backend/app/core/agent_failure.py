from __future__ import annotations

import asyncio
import inspect
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

try:
    from pydantic import ValidationError
except ImportError:  # pragma: no cover - only useful for isolated tooling
    ValidationError = ()  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)
T = TypeVar("T")


class AgentFailureMode(str, Enum):
    """Operational importance of one Agent call in one specific workflow."""

    REQUIRED = "required"
    DEGRADED = "degraded"
    BEST_EFFORT = "best_effort"


class AgentFailureKind(str, Enum):
    LLM = "llm"
    TIMEOUT = "timeout"
    INVALID_OUTPUT = "invalid_output"
    UNEXPECTED = "unexpected"


@dataclass(frozen=True, slots=True)
class AgentFailurePolicy:
    mode: AgentFailureMode
    fallback_name: str | None = None
    timeout_seconds: float | None = None
    fallback_on_unexpected: bool = False


@dataclass(frozen=True, slots=True)
class AgentFailure:
    agent: str
    mode: AgentFailureMode
    kind: AgentFailureKind
    fallback: str | None
    exception_type: str
    elapsed_ms: int

    def safe_dict(self) -> dict[str, object]:
        """No prompts, user text, provider payloads, or exception messages."""
        return {
            "agent": self.agent,
            "mode": self.mode.value,
            "kind": self.kind.value,
            "fallback": self.fallback,
            "exception_type": self.exception_type,
            "elapsed_ms": self.elapsed_ms,
        }


@dataclass(slots=True)
class AgentCallOutcome(Generic[T]):
    value: T | None
    failure: AgentFailure | None = None
    skipped: bool = False

    @property
    def degraded(self) -> bool:
        return self.failure is not None and not self.skipped

    @property
    def ok(self) -> bool:
        return self.failure is None

    def require_value(self) -> T:
        if self.value is None:
            raise RuntimeError("Agent call outcome has no value")
        return self.value


class AgentExecutionError(RuntimeError):
    """Stable orchestration-level error; the original exception stays chained."""

    def __init__(self, failure: AgentFailure) -> None:
        self.failure = failure
        super().__init__(
            f"{failure.agent} failed ({failure.kind.value}, {failure.mode.value})"
        )


def classify_agent_exception(exc: BaseException) -> AgentFailureKind:
    # Import lazily so this runtime stays easy to unit-test and does not create
    # a core -> LLM startup dependency.
    try:
        from app.llm.client import LLMClientError
    except Exception:  # pragma: no cover - only applies outside the full app
        LLMClientError = ()  # type: ignore[assignment,misc]

    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return AgentFailureKind.TIMEOUT
    if LLMClientError and isinstance(exc, LLMClientError):
        return AgentFailureKind.LLM
    # Useful for isolated tests and wrappers around the LLM package.
    if exc.__class__.__name__ == "LLMClientError":
        return AgentFailureKind.LLM
    if ValidationError and isinstance(exc, ValidationError):
        return AgentFailureKind.INVALID_OUTPUT
    return AgentFailureKind.UNEXPECTED


async def _resolve_fallback(
    fallback: Callable[[], T | Awaitable[T]],
) -> T:
    value = fallback()
    if inspect.isawaitable(value):
        return await value
    return value


async def run_agent_call(
    *,
    agent: str,
    policy: AgentFailurePolicy,
    call: Callable[[], Awaitable[T]],
    fallback: Callable[[], T | Awaitable[T]] | None = None,
    trace_id: str | None = None,
    on_failure: Callable[[AgentFailure], None] | None = None,
) -> AgentCallOutcome[T]:
    """
    Execute one Agent call under a single failure contract.

    Deliberately does *not* retry. The LLM client already owns provider retry /
    structured-output repair; orchestration retries would multiply calls and
    create unpredictable latency/cost.
    """

    started_at = time.perf_counter()
    try:
        coroutine = call()
        if policy.timeout_seconds is not None:
            value = await asyncio.wait_for(
                coroutine,
                timeout=policy.timeout_seconds,
            )
        else:
            value = await coroutine
        return AgentCallOutcome(value=value)
    except asyncio.CancelledError:
        # Cancellation is control flow, not a business failure. Never turn a
        # disconnected request or shutdown into a fake fallback success.
        raise
    except Exception as exc:
        failure = AgentFailure(
            agent=agent,
            mode=policy.mode,
            kind=classify_agent_exception(exc),
            fallback=policy.fallback_name,
            exception_type=type(exc).__name__,
            elapsed_ms=round((time.perf_counter() - started_at) * 1000),
        )
        if on_failure is not None:
            on_failure(failure)

        logger.exception(
            "agent_call_failed",
            extra={
                "trace_id": trace_id,
                **failure.safe_dict(),
            },
        )

        if policy.mode is AgentFailureMode.REQUIRED:
            raise AgentExecutionError(failure) from exc

        # Operational failures may degrade. Programming/invariant failures are
        # fatal by default so resilience does not silently hide broken code.
        # Auxiliary audit/advisory policies can explicitly opt into continuing.
        if (
            failure.kind is AgentFailureKind.UNEXPECTED
            and not policy.fallback_on_unexpected
        ):
            raise AgentExecutionError(failure) from exc

        if policy.mode is AgentFailureMode.BEST_EFFORT:
            return AgentCallOutcome(
                value=None,
                failure=failure,
                skipped=True,
            )

        if fallback is None:
            raise AgentExecutionError(failure) from exc

        try:
            fallback_value = await _resolve_fallback(fallback)
        except asyncio.CancelledError:
            raise
        except Exception as fallback_exc:
            logger.exception(
                "agent_fallback_failed",
                extra={
                    "trace_id": trace_id,
                    **failure.safe_dict(),
                    "fallback_exception_type": type(fallback_exc).__name__,
                },
            )
            # A DEGRADED call is only resilient if its deterministic fallback is
            # valid. A broken fallback is a programming/invariant error.
            fallback_failure = AgentFailure(
                agent=agent,
                mode=AgentFailureMode.REQUIRED,
                kind=AgentFailureKind.UNEXPECTED,
                fallback=policy.fallback_name,
                exception_type=type(fallback_exc).__name__,
                elapsed_ms=round((time.perf_counter() - started_at) * 1000),
            )
            raise AgentExecutionError(fallback_failure) from fallback_exc

        return AgentCallOutcome(
            value=fallback_value,
            failure=failure,
            skipped=False,
        )
