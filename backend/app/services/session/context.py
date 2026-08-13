from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import uuid4

from app.core.agent_failure import AgentFailure
from app.schemas.safety import SafetyCheckResponse
from app.schemas.session import SessionMessageRequest, SessionMessageResponse, StateDelta


@dataclass(slots=True)
class SessionExecutionContext:
    """一次 /api/session/message 请求在各 Stage 之间传递的上下文。"""

    request: SessionMessageRequest
    simulation_agent_version: str
    defer_background: Callable[..., None] | None = None

    trace_id: str = field(default_factory=lambda: uuid4().hex[:8])
    started_at: float = field(default_factory=time.perf_counter)

    safety_result: SafetyCheckResponse | None = None
    response: SessionMessageResponse | None = None
    state_delta: StateDelta | None = None
    risk_flags: list[str] = field(default_factory=list)
    blocked: bool = False
    failures: list[AgentFailure] = field(default_factory=list)

    @property
    def degraded(self) -> bool:
        return bool(self.failures)

    def record_failure(self, failure: AgentFailure) -> None:
        self.failures.append(failure)

    def require_safety_result(self) -> SafetyCheckResponse:
        if self.safety_result is None:
            raise RuntimeError("SafetyStage 尚未执行或未写入结果。")
        return self.safety_result

    def require_response(self) -> SessionMessageResponse:
        if self.response is None:
            raise RuntimeError("SimulationStage 尚未执行或未写入响应。")
        return self.response

    def require_state_delta(self) -> StateDelta:
        if self.state_delta is None:
            raise RuntimeError("当前上下文尚未生成 state_delta。")
        return self.state_delta
