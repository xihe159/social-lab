from __future__ import annotations

from typing import Any

from app.agents.failure_policies import (
    SAFETY_LLM_ENRICHMENT_DEGRADED,
    SESSION_SAFETY_REQUIRED,
)
from app.core.agent_failure import run_agent_call
from app.schemas.safety import SafetyCheckRequest
from app.services.session.context import SessionExecutionContext
from app.services.session.policies import build_blocked_response, should_block
from app.services.session.telemetry import SessionTelemetry


class SafetyStage:
    """规则安全检查是 REQUIRED；LLM enrichment 失败时安全地退回规则结果。"""

    def __init__(self, agent: Any, telemetry: SessionTelemetry):
        self.agent = agent
        self.telemetry = telemetry

    async def execute(self, context: SessionExecutionContext) -> SessionExecutionContext:
        request = context.request
        safety_request = SafetyCheckRequest(
            context="session_message",
            scenario=request.scenario,
            goal=request.goal,
            outcome=request.outcome,
            persona=request.persona,
            messages=request.messages,
            user_message=request.user_message,
            current_memory=request.memory,
        )
        started_at = self.telemetry.agent_started(
            context,
            agent="SafetyAgent",
            context="session_message",
            message_count=len(request.messages),
            has_memory=request.memory is not None,
            user_message_length=len(request.user_message),
        )

        # New policy-aware implementation: deterministic rule check first, then
        # degradable LLM enrichment. The fallback cannot make a rule-detected risk safer.
        if hasattr(self.agent, "rule_check") and hasattr(self.agent, "enrich"):
            rule_result = self.agent.rule_check(safety_request)
            if rule_result.risk_level == "high" or rule_result.action == "block":
                result = rule_result
            else:
                outcome = await run_agent_call(
                    agent="SafetyAgent.LLMEnrichment",
                    policy=SAFETY_LLM_ENRICHMENT_DEGRADED,
                    call=lambda: self.agent.enrich(
                        safety_request,
                        rule_result=rule_result,
                    ),
                    fallback=lambda: rule_result,
                    trace_id=context.trace_id,
                    on_failure=context.record_failure,
                )
                result = outcome.require_value()
        else:
            # Compatibility path for injected test doubles / legacy SafetyAgent.
            outcome = await run_agent_call(
                agent="SafetyAgent",
                policy=SESSION_SAFETY_REQUIRED,
                call=lambda: self.agent.run(safety_request),
                trace_id=context.trace_id,
                on_failure=context.record_failure,
            )
            result = outcome.require_value()

        context.safety_result = result
        self.telemetry.agent_finished(
            context,
            agent="SafetyAgent",
            started_at=started_at,
            status="degraded" if any(f.agent.startswith("SafetyAgent") for f in context.failures) else "success",
            allowed=result.allowed,
            action=result.action,
            risk_level=result.risk_level,
            risk_types=result.risk_types,
            should_redact=result.should_redact,
            redacted_fields=result.redacted_fields,
        )
        if should_block(result):
            context.response = build_blocked_response(request=request, safety_result=result)
            context.state_delta = context.response.simulation.state_delta
            context.risk_flags = list(context.response.simulation.risk_flags)
            context.blocked = True
        return context
