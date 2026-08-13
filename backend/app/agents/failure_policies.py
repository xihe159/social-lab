from __future__ import annotations

from app.core.agent_failure import AgentFailureMode, AgentFailurePolicy

# Session pipeline ---------------------------------------------------------
# Safety's deterministic rule engine is handled before the LLM enrichment.
# A failure of that rule engine itself is REQUIRED; its LLM enrichment may use
# the rule result as a safe degraded fallback (see PolicySafetyAgent).
SESSION_SAFETY_REQUIRED = AgentFailurePolicy(AgentFailureMode.REQUIRED)
SAFETY_LLM_ENRICHMENT_DEGRADED = AgentFailurePolicy(
    AgentFailureMode.DEGRADED,
    fallback_name="deterministic_rule_result",
    timeout_seconds=8.0,
    fallback_on_unexpected=True,
)
SESSION_SIMULATION_REQUIRED = AgentFailurePolicy(AgentFailureMode.REQUIRED)
SESSION_STATE_DEGRADED = AgentFailurePolicy(
    AgentFailureMode.DEGRADED,
    fallback_name="simulation_agent_state_delta",
)
SESSION_MEMORY_DEGRADED = AgentFailurePolicy(
    AgentFailureMode.DEGRADED,
    fallback_name="previous_memory",
)

# Report pipeline ----------------------------------------------------------
REPORT_PREDICTION_DEGRADED = AgentFailurePolicy(
    AgentFailureMode.DEGRADED,
    fallback_name="deterministic_prediction",
)
REPORT_ANALYSIS_DEGRADED = AgentFailurePolicy(
    AgentFailureMode.DEGRADED,
    fallback_name="neutral_sentence_analysis",
)
REPORT_REWRITE_DEGRADED = AgentFailurePolicy(
    AgentFailureMode.DEGRADED,
    fallback_name="safe_default_rewrite",
)

# Simulation internals ----------------------------------------------------
# Core persona response ownership is REQUIRED. Strategy and evaluation are
# auxiliary: strategy may fall back to neutral guidance; audit may be skipped.
SIMULATION_CORE_REQUIRED = AgentFailurePolicy(AgentFailureMode.REQUIRED)
STRATEGY_ADVISORY_DEGRADED = AgentFailurePolicy(
    AgentFailureMode.DEGRADED,
    fallback_name="neutral_strategy_guidance",
    fallback_on_unexpected=True,
)
EVALUATION_AUDIT_BEST_EFFORT = AgentFailurePolicy(
    AgentFailureMode.BEST_EFFORT,
    fallback_name="skip_evaluation_audit",
    fallback_on_unexpected=True,
)

# V2 pipeline stages. Turn analysis / strategy / decision have deterministic
# fallbacks in the pipeline. Final natural-language generation is REQUIRED once
# the deterministic generator fallback is exhausted by GenerationStage itself.
TURN_ANALYSIS_DEGRADED = AgentFailurePolicy(
    AgentFailureMode.DEGRADED,
    fallback_name="neutral_turn_state",
)
SIMULATION_DECISION_DEGRADED = AgentFailurePolicy(
    AgentFailureMode.DEGRADED,
    fallback_name="guidance_based_decision",
)
GENERATION_FIRST_ATTEMPT_BEST_EFFORT = AgentFailurePolicy(
    AgentFailureMode.BEST_EFFORT,
    fallback_name="retry_generation_once",
    fallback_on_unexpected=True,
)
GENERATION_FINAL_DEGRADED = AgentFailurePolicy(
    AgentFailureMode.DEGRADED,
    fallback_name="deterministic_response_template",
    fallback_on_unexpected=True,
)

# Direct API calls ---------------------------------------------------------
# When a user explicitly requests one Agent endpoint, that Agent is the product
# of the request. Returning an invented fallback as if it were the requested
# model output would hide an outage, so direct endpoints stay REQUIRED.
DIRECT_AGENT_REQUIRED = AgentFailurePolicy(AgentFailureMode.REQUIRED)
