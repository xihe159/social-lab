from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


EvaluationExecutionMode = Literal["development_sync", "production_hybrid"]
EvaluationRunMode = Literal["synchronous", "background", "not_run"]


class RuntimeMetricSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class AgentRuntimeMetric(RuntimeMetricSchema):
    trace_id: str
    session_id: str
    turn_id: str
    agent: str
    version: str
    run_mode: EvaluationRunMode | Literal["pipeline"] = "pipeline"
    latency_ms: int = Field(ge=0)
    success: bool
    correction_applied: bool = False
    score_delta: int | None = Field(default=None, ge=-100, le=100)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )
    )


class AgentMetricSummary(RuntimeMetricSchema):
    agent: str
    version: str
    run_mode: str
    call_count: int = Field(ge=0)
    success_count: int = Field(ge=0)
    success_rate: float = Field(ge=0.0, le=1.0)
    average_latency_ms: int = Field(ge=0)
    p95_latency_ms: int = Field(ge=0)
    correction_count: int = Field(ge=0)
    correction_improved_count: int = Field(ge=0)


class RuntimeMetricsSnapshot(RuntimeMetricSchema):
    total_records: int = Field(ge=0)
    summaries: list[AgentMetricSummary]

