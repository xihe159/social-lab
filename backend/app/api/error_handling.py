from __future__ import annotations

from fastapi import HTTPException

from app.core.agent_failure import AgentExecutionError, AgentFailureKind


def to_agent_http_exception(exc: AgentExecutionError) -> HTTPException:
    """Map internal Agent failures to a stable, non-sensitive API contract."""
    failure = exc.failure
    if failure.kind is AgentFailureKind.TIMEOUT:
        status_code = 504
        message = f"{failure.agent} 响应超时，请稍后重试。"
    elif failure.kind in {AgentFailureKind.LLM, AgentFailureKind.INVALID_OUTPUT}:
        status_code = 502
        message = f"{failure.agent} 暂时无法提供有效结果，请稍后重试。"
    else:
        status_code = 500
        message = f"{failure.agent} 处理失败。"
    return HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "agent": failure.agent,
            "failure_kind": failure.kind.value,
            "retryable": failure.kind in {AgentFailureKind.LLM, AgentFailureKind.TIMEOUT},
        },
    )
