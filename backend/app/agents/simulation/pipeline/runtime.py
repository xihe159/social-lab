from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.schemas.runtime_metrics import AgentRuntimeMetric
from app.services.agent_runtime_metrics import AgentRuntimeMetricsStore

logger = logging.getLogger(__name__)
T = TypeVar("T")


def prompt_version(component, attribute: str, fallback: str) -> str:
    value = getattr(component, attribute, fallback)
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def record_runtime_metric(
    store: AgentRuntimeMetricsStore,
    *,
    trace_id: str,
    session_id: str,
    turn_id: str,
    agent: str,
    version: str,
    run_mode: str,
    started_at: float,
    success: bool,
    correction_applied: bool = False,
    score_delta: int | None = None,
) -> None:
    try:
        store.record(
            AgentRuntimeMetric(
                trace_id=trace_id,
                session_id=session_id,
                turn_id=turn_id,
                agent=agent,
                version=version,
                run_mode=run_mode,
                latency_ms=max(0, int((time.perf_counter() - started_at) * 1000)),
                success=success,
                correction_applied=correction_applied,
                score_delta=score_delta,
            )
        )
    except Exception:
        logger.exception(
            "agent_runtime_metric_record_failed_without_blocking_response",
            extra={"trace_id": trace_id, "session_id": session_id, "turn_id": turn_id, "agent": agent},
        )


async def measured_call(
    store: AgentRuntimeMetricsStore,
    *,
    trace_id: str,
    session_id: str,
    turn_id: str,
    agent: str,
    version: str,
    run_mode: str,
    call: Callable[[], Awaitable[T]],
) -> T:
    started_at = time.perf_counter()
    try:
        result = await call()
    except BaseException:
        record_runtime_metric(
            store,
            trace_id=trace_id,
            session_id=session_id,
            turn_id=turn_id,
            agent=agent,
            version=version,
            run_mode=run_mode,
            started_at=started_at,
            success=False,
        )
        raise
    record_runtime_metric(
        store,
        trace_id=trace_id,
        session_id=session_id,
        turn_id=turn_id,
        agent=agent,
        version=version,
        run_mode=run_mode,
        started_at=started_at,
        success=True,
    )
    return result
