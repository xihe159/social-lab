# SimulationAgent V2 quality baseline

This document is the release gate for the completed Phase 0–8 upgrade.

## Fixed evaluation personas

1. Persona A: strong, direct, responsibility-oriented advisor.
2. Persona B: gentle friend with high conflict avoidance.
3. Persona C: sensitive partner in an intimate relationship.

The executable fixtures live in `backend/evaluation/fixtures.py` and must remain
stable when comparing future model, prompt, or retrieval changes.

## Required regression suites

1. Counterfactual User: polite and rude requests to the same persona must differ
   in state delta, response action, and reply.
2. Counterfactual Persona: the same message must produce distinct behavior
   signatures for Personas A, B, and C.
3. Longitudinal State: three positive turns, three pressure turns, and one
   apology must change state continuously without resetting it.
4. Chat Evidence: real chat must affect reply length, wording patterns,
   trigger-response behavior, and evidence retrieval.
5. No Reply: normal, cold, deferred, read-without-reply, and conversation-end
   behavior must remain distinct and persona-appropriate.
6. Overreaction: mild rudeness must not cause an unbounded relationship collapse;
   extreme actions in low conflict must trigger consistency review.

Run the offline gate:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='backend'
python -m unittest discover -s backend/tests -v
npm run build
```

## Quality dimensions

- Persona Differentiation: behavioral distance across fixed personas.
- Interaction Sensitivity: change between polite, accountable, pressuring, and
  blaming user messages.
- Longitudinal Consistency: bounded, continuous multi-turn state movement.
- Style Similarity: reply length, formality, emoji, punctuation, and phrasing.
- Evidence Grounding: relevant REAL_CHAT Episode usage and absence of unsupported
  evidence claims.
- Response Action Accuracy: agreement between selected action and visible UI
  behavior.
- Overreaction Rate: frequency of disproportionate extreme action after mild
  events.
- Latency: p50 and p95 end-to-end session response duration.

The machine-readable gates are in `backend/evaluation/quality_baseline.json`.

## Staging gate before enabling V2

Offline regression validates contracts and deterministic safety boundaries. It
does not measure live model quality or network latency. Before setting
`SIMULATION_AGENT_VERSION=v2` in production:

1. Run all six suites against the deployed staging model.
2. Review persona differentiation, style similarity, evidence grounding,
   response action accuracy, and overreaction rate.
3. Capture p50 and p95 latency from session logs.
4. Confirm normal turns use two LLM calls and Evaluator remains conditional.
5. Confirm logs and Turn Store contain no raw sensitive conversation text.
6. Keep `SIMULATION_AGENT_VERSION=v1` available for immediate rollback.

## Definition of Done audit

- Persona Model V2 exists and separates traits, style, dyadic profile, patterns,
  and evidence summary.
- Dynamic Simulation State persists relationship, emotion, and conversation state.
- Each turn performs analysis, state update, and action selection before language
  generation.
- Cold, brief, boundary, no-reply, and conversation-end actions are supported.
- Real chat produces communication style, behavior patterns, and REAL_CHAT evidence.
- Simulation-only inferences never enter the real evidence store.
- State changes continuously across turns with bounded deltas and emotional decay.
- Fixed personas expose distinct behavioral signatures for the same message.
- Consistency Evaluator runs only when triggered and can retry generation once.
- Regression, build, privacy, recovery, rollback, and staging gates are documented.
