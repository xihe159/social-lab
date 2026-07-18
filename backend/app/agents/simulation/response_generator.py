from __future__ import annotations

from app.agents.simulation.prompts import (
    RESPONSE_GENERATOR_SYSTEM_PROMPT,
    SIMULATION_PROMPT_VERSION,
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

    prompt_version = SIMULATION_PROMPT_VERSION

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
            generated.response_text = _default_response(
                policy.action,
                strategy_action=request.strategy_action,
            )

        generated.response_text = _enforce_strategy_semantics(
            generated.response_text,
            strategy_action=request.strategy_action,
        )
        if _has_style_adjustment(request, "两句以内"):
            generated.response_text = _keep_sentence_limit(
                generated.response_text,
                limit=2,
            )

        max_length = {
            "short": 80,
            "medium": 240,
            "long": 500,
        }[policy.reply_length]

        if policy.action == "REPLY_BRIEF":
            max_length = min(max_length, 60)
        elif policy.action == "REPLY_COLD":
            max_length = min(max_length, 100)
        elif policy.action == "SET_BOUNDARY":
            max_length = min(max_length, 100)
        elif policy.action == "END_CONVERSATION":
            max_length = min(max_length, 120)

        generated.response_text = _truncate(generated.response_text, max_length)
        if policy.action == "ASK_CLARIFICATION":
            generated.response_text = _keep_one_question(generated.response_text)
        return generated


def _default_response(action: str, *, strategy_action: str | None = None) -> str:
    if strategy_action == "refuse":
        return "这件事我不能答应。"
    if strategy_action == "accept":
        return "可以。"
    if strategy_action == "accept_with_condition":
        return "可以，但需要先把条件确认清楚。"
    if strategy_action == "partial_accept":
        return "我只能接受其中一部分。"
    return {
        "REPLY_BRIEF": "知道了。",
        "REPLY_COLD": "我知道了，之后再说。",
        "ASK_CLARIFICATION": "你先把具体情况说清楚。",
        "SET_BOUNDARY": "这件事我暂时不想继续讨论。",
        "CONFRONT": "你现在的表达方式有问题。",
        "END_CONVERSATION": "这件事先到这里吧，我不想继续讨论了。",
    }.get(action, "我知道了，你继续说。")


def build_fallback_response(
    policy: ResponsePolicy,
    *,
    strategy_action: str | None = None,
) -> GeneratedResponse:
    """Deterministic final fallback after the single generator retry fails."""

    if policy.action in {"DEFER_REPLY", "READ_NO_REPLY"}:
        text = ""
    else:
        text = _default_response(policy.action, strategy_action=strategy_action)
    return GeneratedResponse(response_text=text, response_action=policy.action)


def _enforce_strategy_semantics(
    value: str,
    *,
    strategy_action: str | None,
) -> str:
    if strategy_action != "refuse":
        return value

    refusal_markers = ("不能", "不行", "没法", "不同意", "不答应", "拒绝", "不可以")
    acceptance_markers = ("可以", "没问题", "答应", "同意", "当然")
    has_refusal = any(marker in value for marker in refusal_markers)
    contradicts_refusal = any(marker in value for marker in acceptance_markers)
    if contradicts_refusal and not has_refusal:
        return "这件事我不能答应。"
    return value


def _keep_one_question(value: str) -> str:
    question_positions = [
        index for index, char in enumerate(value) if char in {"?", "？"}
    ]
    if len(question_positions) <= 1:
        return value
    return value[: question_positions[0] + 1].strip()


def _has_style_adjustment(
    request: ResponseGenerationInput,
    marker: str,
) -> bool:
    profile = request.simulation_adjustments
    return bool(
        profile
        and any(marker in adjustment for adjustment in profile.style_adjustments)
    )


def _keep_sentence_limit(value: str, *, limit: int) -> str:
    sentence_ends = {"。", "！", "？", "!", "?"}
    completed = 0
    for index, char in enumerate(value):
        if char not in sentence_ends:
            continue
        completed += 1
        if completed >= limit:
            return value[: index + 1].strip()
    return value


def _truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "…"
