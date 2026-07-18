from __future__ import annotations

import logging
import math
from collections import deque
from threading import RLock

from app.schemas.runtime_metrics import (
    AgentMetricSummary,
    AgentRuntimeMetric,
    RuntimeMetricsSnapshot,
)


logger = logging.getLogger(__name__)


class AgentRuntimeMetricsStore:
    """Bounded in-process metrics with aggregate-only API snapshots."""

    def __init__(self, *, max_records: int = 5000) -> None:
        self._records: deque[AgentRuntimeMetric] = deque(
            maxlen=max(1, max_records)
        )
        self._lock = RLock()

    def record(self, metric: AgentRuntimeMetric) -> None:
        with self._lock:
            self._records.append(metric.model_copy(deep=True))
        logger.info(
            "agent_runtime_metric",
            extra=metric.model_dump(mode="json"),
        )

    def snapshot(self) -> RuntimeMetricsSnapshot:
        with self._lock:
            records = [item.model_copy(deep=True) for item in self._records]

        grouped: dict[tuple[str, str, str], list[AgentRuntimeMetric]] = {}
        for record in records:
            key = (record.agent, record.version, record.run_mode)
            grouped.setdefault(key, []).append(record)

        summaries: list[AgentMetricSummary] = []
        for (agent, version, run_mode), items in sorted(grouped.items()):
            latencies = sorted(item.latency_ms for item in items)
            success_count = sum(1 for item in items if item.success)
            correction_items = [item for item in items if item.correction_applied]
            summaries.append(
                AgentMetricSummary(
                    agent=agent,
                    version=version,
                    run_mode=run_mode,
                    call_count=len(items),
                    success_count=success_count,
                    success_rate=round(success_count / len(items), 4),
                    average_latency_ms=round(sum(latencies) / len(latencies)),
                    p95_latency_ms=latencies[
                        max(0, math.ceil(len(latencies) * 0.95) - 1)
                    ],
                    correction_count=len(correction_items),
                    correction_improved_count=sum(
                        1
                        for item in correction_items
                        if item.score_delta is not None and item.score_delta > 0
                    ),
                )
            )
        return RuntimeMetricsSnapshot(
            total_records=len(records),
            summaries=summaries,
        )

    def clear(self) -> None:
        with self._lock:
            self._records.clear()


agent_runtime_metrics_store = AgentRuntimeMetricsStore()

