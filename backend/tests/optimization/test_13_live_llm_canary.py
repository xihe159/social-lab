from __future__ import annotations

import os

import pytest
from pydantic import BaseModel, ConfigDict
from typing import Literal


pytestmark = pytest.mark.skipif(
    os.getenv("SOCIAL_LAB_RUN_LIVE_LLM") != "1",
    reason="Live LLM test is opt-in. Set SOCIAL_LAB_RUN_LIVE_LLM=1 to run it.",
)


class _CanaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok"]


@pytest.mark.asyncio
async def test_live_llm_strict_structured_output() -> None:
    from app.llm.client import close_async_client, generate_structured

    try:
        result = await generate_structured(
            system_prompt="Return only valid JSON matching the requested schema.",
            user_prompt='Return status="ok".',
            output_model=_CanaryResponse,
            temperature=0,
        )
        assert result.status == "ok"
    finally:
        await close_async_client()


@pytest.mark.asyncio
async def test_live_prompt_registry_and_failure_runtime() -> None:
    from app.agents.failure_policies import DIRECT_AGENT_REQUIRED
    from app.core.agent_failure import run_agent_call
    from app.llm.client import close_async_client, generate_structured
    from app.prompts.catalog import prompt_registry
    from app.schemas.safety import SafetyCheckRequest, SafetyCheckResponse

    request = SafetyCheckRequest(
        context="session_message",
        scenario="social",
        goal="练习礼貌地邀请朋友周末喝咖啡",
        outcome="对方可以自由接受或拒绝",
        user_message="这周末有空一起喝杯咖啡吗？没空也没关系。",
    )
    rendered = prompt_registry.render("safety.check", payload=request.model_dump())

    try:
        outcome = await run_agent_call(
            agent="phase13_pytest_safety_canary",
            policy=DIRECT_AGENT_REQUIRED,
            call=lambda: generate_structured(
                system_prompt=rendered.system_prompt,
                user_prompt=rendered.user_prompt,
                output_model=SafetyCheckResponse,
                temperature=rendered.temperature,
            ),
            trace_id="phase13-pytest-canary",
        )
        result = outcome.require_value()
        assert outcome.ok
        assert result.risk_level in {"none", "low", "medium", "high"}
        assert result.action in {"allow", "warn", "block", "rewrite"}
    finally:
        await close_async_client()
