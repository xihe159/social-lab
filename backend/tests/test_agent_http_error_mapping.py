from app.api.error_handling import to_agent_http_exception
from app.core.agent_failure import (
    AgentExecutionError,
    AgentFailure,
    AgentFailureKind,
    AgentFailureMode,
)


def _error(kind: AgentFailureKind) -> AgentExecutionError:
    return AgentExecutionError(
        AgentFailure(
            agent="StrategyAgent",
            mode=AgentFailureMode.REQUIRED,
            kind=kind,
            fallback=None,
            exception_type="SecretProviderError",
            elapsed_ms=42,
        )
    )


def test_timeout_maps_to_504_without_exception_message() -> None:
    http = to_agent_http_exception(_error(AgentFailureKind.TIMEOUT))
    assert http.status_code == 504
    assert http.detail["failure_kind"] == "timeout"
    assert "SecretProviderError" not in str(http.detail)


def test_llm_maps_to_502() -> None:
    http = to_agent_http_exception(_error(AgentFailureKind.LLM))
    assert http.status_code == 502
    assert http.detail["retryable"] is True


def test_unexpected_maps_to_500_and_not_retryable() -> None:
    http = to_agent_http_exception(_error(AgentFailureKind.UNEXPECTED))
    assert http.status_code == 500
    assert http.detail["retryable"] is False
