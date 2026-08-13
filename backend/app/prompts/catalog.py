from __future__ import annotations

from .base import PromptRegistry
from .memory import MEMORY_EXTRACTOR_PROMPT
from .persona import PERSONA_PROMPT
from .report import ANALYSIS_PROMPT, PREDICTION_PROMPT, REWRITE_PROMPT
from .session import (
    COACH_REPORT_PROMPT,
    MEMORY_LEGACY_PROMPT,
    SAFETY_PROMPT,
    SIMULATION_LEGACY_PROMPT,
    STATE_PROMPT,
)
from .simulation import (
    CONSISTENCY_PROMPT,
    RESPONSE_GENERATION_PROMPT,
    SIMULATION_DECISION_PROMPT,
    TURN_DECISION_PROMPT,
    TURN_STATE_PROMPT,
)
from .strategy import EVALUATION_PROMPT, STRATEGY_PROMPT


def build_prompt_registry() -> PromptRegistry:
    registry = PromptRegistry()
    for definition in (
        PERSONA_PROMPT,
        SIMULATION_LEGACY_PROMPT,
        COACH_REPORT_PROMPT,
        STATE_PROMPT,
        MEMORY_LEGACY_PROMPT,
        SAFETY_PROMPT,
        STRATEGY_PROMPT,
        EVALUATION_PROMPT,
        TURN_STATE_PROMPT,
        SIMULATION_DECISION_PROMPT,
        TURN_DECISION_PROMPT,
        RESPONSE_GENERATION_PROMPT,
        CONSISTENCY_PROMPT,
        ANALYSIS_PROMPT,
        PREDICTION_PROMPT,
        REWRITE_PROMPT,
        MEMORY_EXTRACTOR_PROMPT,
    ):
        registry.register(definition)
    return registry


prompt_registry = build_prompt_registry()
