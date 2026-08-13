"""Compatibility shim for legacy imports.

Prompt ownership moved to :mod:`app.prompts`. New code should import definitions or
``prompt_registry`` from there. This module remains so existing agents can migrate
incrementally without a large-bang import change.
"""

from app.prompts.persona import PERSONA_SYSTEM_PROMPT, build_persona_user_prompt
from app.prompts.session import (
    COACH_SYSTEM_PROMPT,
    MEMORY_SYSTEM_PROMPT,
    SAFETY_SYSTEM_PROMPT,
    SIMULATION_SYSTEM_PROMPT,
    STATE_SYSTEM_PROMPT,
    build_memory_user_prompt,
    build_report_user_prompt,
    build_safety_user_prompt,
    build_simulation_user_prompt,
    build_state_user_prompt,
)
from app.prompts.strategy import (
    EVALUATION_PROMPT_VERSION,
    EVALUATION_SYSTEM_PROMPT,
    STRATEGY_PROMPT_VERSION,
    STRATEGY_SYSTEM_PROMPT,
    build_evaluation_user_prompt,
    build_strategy_user_prompt,
)

__all__ = [
    "PERSONA_SYSTEM_PROMPT",
    "SIMULATION_SYSTEM_PROMPT",
    "COACH_SYSTEM_PROMPT",
    "STATE_SYSTEM_PROMPT",
    "MEMORY_SYSTEM_PROMPT",
    "SAFETY_SYSTEM_PROMPT",
    "STRATEGY_PROMPT_VERSION",
    "STRATEGY_SYSTEM_PROMPT",
    "EVALUATION_PROMPT_VERSION",
    "EVALUATION_SYSTEM_PROMPT",
    "build_persona_user_prompt",
    "build_simulation_user_prompt",
    "build_report_user_prompt",
    "build_state_user_prompt",
    "build_memory_user_prompt",
    "build_safety_user_prompt",
    "build_strategy_user_prompt",
    "build_evaluation_user_prompt",
]
