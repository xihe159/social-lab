"""Compatibility shim for Simulation prompt imports.

All prompt content/version metadata now lives in :mod:`app.prompts.simulation`.
"""

from app.prompts.simulation import (
    CONSISTENCY_EVALUATOR_SYSTEM_PROMPT,
    CONSISTENCY_PROMPT_VERSION,
    RESPONSE_GENERATOR_SYSTEM_PROMPT,
    SIMULATION_DECISION_PROMPT_VERSION,
    SIMULATION_DECISION_SYSTEM_PROMPT,
    SIMULATION_PROMPT_VERSION,
    TURN_DECISION_PROMPT_VERSION,
    TURN_DECISION_SYSTEM_PROMPT,
    TURN_STATE_ANALYZER_SYSTEM_PROMPT,
    TURN_STATE_PROMPT_VERSION,
    build_consistency_evaluation_prompt,
    build_response_generation_prompt,
    build_simulation_decision_prompt,
    build_turn_decision_prompt,
    build_turn_state_analysis_prompt,
)

__all__ = [
    "SIMULATION_PROMPT_VERSION",
    "TURN_STATE_PROMPT_VERSION",
    "SIMULATION_DECISION_PROMPT_VERSION",
    "TURN_DECISION_PROMPT_VERSION",
    "CONSISTENCY_PROMPT_VERSION",
    "TURN_STATE_ANALYZER_SYSTEM_PROMPT",
    "SIMULATION_DECISION_SYSTEM_PROMPT",
    "TURN_DECISION_SYSTEM_PROMPT",
    "RESPONSE_GENERATOR_SYSTEM_PROMPT",
    "CONSISTENCY_EVALUATOR_SYSTEM_PROMPT",
    "build_turn_state_analysis_prompt",
    "build_simulation_decision_prompt",
    "build_turn_decision_prompt",
    "build_response_generation_prompt",
    "build_consistency_evaluation_prompt",
]
