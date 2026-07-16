from __future__ import annotations

from app.agents.simulation.prompts import (
    RESPONSE_GENERATOR_SYSTEM_PROMPT,
    build_response_generation_prompt,
)
from app.llm.client import generate_structured
from app.schemas.simulation_generation import (
    GeneratedResponse,
    ResponseGenerationInput,
)
from app.schemas.simulation_decision import ResponsePolicy


class ResponseGenerator:
    """Turn a fixed response policy into the target person's visible message."""

    async def run(self, request: ResponseGenerationInput) -> GeneratedResponse:
        generated = await generate_structured(
            system_prompt=RESPONSE_GENERATOR_SYSTEM_PROMPT,
            user_prompt=build_response_generation_prompt(request),
            output_model=GeneratedResponse,
            temperature=0.55,
        )
        return self.post_process(generated=generated, request=request)

    def post_process(
        self,
        *,
        generated: GeneratedResponse,
        request: ResponseGenerationInput,
    ) -> GeneratedResponse:
        policy = request.response_policy

        # The generator is a renderer, not a second decision-maker.
        generated.response_action = policy.action
        if policy.action in {"DEFER_REPLY", "READ_NO_REPLY"}:
            generated.response_text = ""
            return generated

        generated.response_text = generated.response_text.strip()
        if not generated.response_text:
            generated.response_text = _default_response(policy.action)

        max_length = {
            "short": 80,
            "medium": 240,
            "long": 500,
        }[policy.reply_length]

        if policy.action == "REPLY_BRIEF":
            max_length = min(max_length, 60)
        elif policy.action == "REPLY_COLD":
            max_length = min(max_length, 140)
        elif policy.action == "END_CONVERSATION":
            max_length = min(max_length, 120)

        generated.response_text = _truncate(generated.response_text, max_length)
        return generated


def _default_response(action: str) -> str:
    return {
        "REPLY_BRIEF": "知道了。",
        "REPLY_COLD": "我知道了，之后再说。",
        "ASK_CLARIFICATION": "你先把具体情况说清楚。",
        "SET_BOUNDARY": "这件事我暂时不想继续讨论。",
        "CONFRONT": "你现在的表达方式有问题。",
        "END_CONVERSATION": "这件事先到这里吧，我不想继续讨论了。",
    }.get(action, "我知道了，你继续说。")


def build_fallback_response(policy: ResponsePolicy) -> GeneratedResponse:
    """Deterministic final fallback after the single generator retry fails."""

    if policy.action in {"DEFER_REPLY", "READ_NO_REPLY"}:
        text = ""
    else:
        text = _default_response(policy.action)
    return GeneratedResponse(response_text=text, response_action=policy.action)


def _truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "…"
