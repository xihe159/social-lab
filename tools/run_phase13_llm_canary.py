from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


class CanaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    message: str = Field(min_length=1, max_length=80)


def _base_url_label(value: str | None) -> str:
    if not value:
        return "OpenAI default"
    # The base URL is operational metadata; never print keys/query strings.
    return value.split("?", 1)[0]


async def main() -> int:
    from app.agents.failure_policies import DIRECT_AGENT_REQUIRED
    from app.core.agent_failure import AgentExecutionError, run_agent_call
    from app.core.config import get_settings
    from app.llm.client import close_async_client, generate_structured
    from app.prompts.catalog import prompt_registry
    from app.schemas.safety import SafetyCheckRequest, SafetyCheckResponse

    print("=" * 72)
    print("PHASE 13: Live LLM Canary")
    print("=" * 72)

    settings = get_settings()
    try:
        settings.get_llm_api_key()
    except ValueError as exc:
        print(f"FAIL  LLM credential is not configured: {exc}")
        return 2

    print(f"Python : {sys.executable}")
    print(f"Backend: {BACKEND}")
    print(f"Model  : {settings.llm_model_id}")
    print(f"Base   : {_base_url_label(getattr(settings, 'llm_base_url', None))}")
    print("Key    : configured (redacted)")
    print()

    try:
        # Canary A isolates provider connectivity + strict structured output.
        started = time.perf_counter()
        direct = await generate_structured(
            system_prompt=(
                "You are a connectivity canary. Return only the requested JSON. "
                "Do not include Markdown or extra fields."
            ),
            user_prompt='Return status="ok" and a very short message confirming connectivity.',
            output_model=CanaryResponse,
            temperature=0,
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        assert direct.status == "ok"
        print(f"PASS  Direct structured LLM call ({elapsed_ms} ms)")

        # Canary B exercises PromptRegistry + the shared failure runtime + structured output.
        request = SafetyCheckRequest(
            context="session_message",
            scenario="social",
            goal="练习礼貌地邀请朋友周末喝咖啡",
            outcome="对方可以自由接受或拒绝",
            role="朋友",
            relation="普通朋友",
            habit="",
            chatLog="",
            persona=None,
            messages=[],
            user_message="这周末有空一起喝杯咖啡吗？没空也没关系。",
            current_memory=None,
        )
        rendered = prompt_registry.render(
            "safety.check",
            payload=request.model_dump(),
        )
        assert rendered.key == "safety.check"
        assert rendered.version
        assert rendered.system_prompt.strip()
        assert rendered.user_prompt.strip()
        print(
            "PASS  PromptRegistry render "
            f"({rendered.key}@{rendered.version}, temp={rendered.temperature})"
        )

        started = time.perf_counter()
        outcome = await run_agent_call(
            agent="phase13_safety_canary",
            policy=DIRECT_AGENT_REQUIRED,
            call=lambda: generate_structured(
                system_prompt=rendered.system_prompt,
                user_prompt=rendered.user_prompt,
                output_model=SafetyCheckResponse,
                temperature=rendered.temperature,
            ),
            trace_id="phase13-live-canary",
        )
        safety = outcome.require_value()
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        assert outcome.ok
        assert isinstance(safety.allowed, bool)
        assert safety.risk_level in {"none", "low", "medium", "high"}
        assert safety.action in {"allow", "warn", "block", "rewrite"}
        print(f"PASS  PromptRegistry -> FailureRuntime -> LLM ({elapsed_ms} ms)")
        print(
            "INFO  Safety canary result: "
            f"allowed={safety.allowed}, risk_level={safety.risk_level}, action={safety.action}"
        )

        print()
        print("PHASE 13 PASSED")
        print("Live LLM calls used: 2")
        return 0
    except AgentExecutionError as exc:
        failure = exc.failure
        print(
            "FAIL  Shared failure runtime caught a live LLM failure: "
            f"kind={failure.kind.value}, mode={failure.mode.value}, "
            f"exception_type={failure.exception_type}"
        )
        return 3
    except Exception as exc:
        print(f"FAIL  {type(exc).__name__}: {exc}")
        return 1
    finally:
        await close_async_client()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
