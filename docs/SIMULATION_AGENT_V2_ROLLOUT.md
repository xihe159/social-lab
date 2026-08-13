# SimulationAgent V2 rollout

This document records the implementation baseline for the phased V2 upgrade.
The public API and frontend contract remain unchanged during Phase 0.

## Current `/api/session/message` call chain

1. `app.api.session.send_message`
2. `SessionOrchestrator.handle_message`
3. `SafetyAgent.run`
4. Version-selected `SimulationAgent.run`
5. `StateAgent.run`, with the SimulationAgent delta as fallback
6. `MemoryAgent.run`, with the previous memory as fallback
7. Existing `SessionMessageResponse`

## Phase 0 version behavior

- `SIMULATION_AGENT_VERSION=v1` selects the preserved V1 implementation.
- `SIMULATION_AGENT_VERSION=v2` remains a compatibility alias for the current
  V2 implementation.
- `SIMULATION_AGENT_VERSION=v2.1` explicitly selects the repaired V2.1 path.
- V1 and V2.1 are independent implementations; V2.1 never mutates V1.
- Missing or invalid values safely select V1.

## Rollback

Set `SIMULATION_AGENT_VERSION=v1` and restart the backend service. No frontend,
request schema, response schema, or stored data migration is required.

## Phase 1 data foundation

- `PersonaModelV2` separates basic profile, stable behavioral dimensions,
  communication style, dyadic profile, behavior patterns, and evidence summary.
- `SimulationState` separates relationship, short-term emotion, and conversation
  progress for each anonymous simulation session.
- The legacy persona adapter converts the current 0-100 relationship model into
  validated 0.0-1.0 V2 values without changing the V1 API contract.
- Initial state creation copies the dyadic relationship into an independent
  session state and starts short-term emotion and conversation progress neutral.

## Phase 2 turn decision engine

> 2026-07-29 V2.1 correction: Strategy no longer owns the final action. The
> active chain is TurnStateAnalyzer → Strategy Guidance → Simulation Decision
> Engine → Response Generator.

- TurnStateAnalyzer produces intent, observable behavior, persona triggers,
  risks and bounded state deltas, but never chooses accept/refuse or tone.
- Strategy produces one to three advisory response hypotheses with normalized
  probabilities, evidence and a recommended direction.
- Simulation Decision Engine combines Persona, Memory, updated relationship
  state, history, current semantics and Guidance, and owns the final action.
- Normal-turn deltas are clamped to +/-0.15. Only recognized severe events can
  use the +/-0.25 limit.
- Relationship, emotion, and conversation state are updated without mutating the
  previous snapshot; short-term emotional values decay by 10% each turn.
- The engine is isolated from `/api/session/message` until the response generator
  is implemented in Phase 3.

## Phase 3 response generation and integration

- V2.1 runs TurnStateAnalyzer, advisory Strategy, Simulation Decision Engine,
  then Response Generator.
- The generator must preserve the selected action and applies response-length
  limits after structured output validation.
- `/api/session/message` keeps its existing visible reply contract and adds an
  optional V2 state snapshot for transparent multi-turn continuity.
- The frontend carries anonymous persona/session IDs and the V2 state without
  changing the chat UI.
- StateAgent remains active for communication Dynamics and confirmed risk
  supplements. In V2/V2.1 it does not overwrite Simulation's relationship state;
  V1 orchestration is unchanged.

## Phase 4 response actions and no-reply behavior

- The decision contract supports all nine PRD actions, including defer, read
  without reply, and conversation end.
- Silent actions skip Response Generator and return a formal status event rather
  than fabricated dialogue text.
- Conversation end may include a final target message and disables further user
  input while preserving reset and report actions.
- The frontend renders no-reply events as centered status chips, not target chat
  bubbles, and continues to support V1 responses without an action payload.

## Phase 5 chat record analyzer

- The serial pipeline normalizes user/target roles and timestamps, removes system
  notices, merges consecutive messages, preserves original text, and marks
  missing-message boundaries.
- Conversation Episode Builder groups interactions before learning behavior; a
  single message is never treated as a permanent personality trait.
- Style, relationship, trigger-response, fact, and uncertainty analyzers produce
  evidence-linked conclusions with bounded confidence.
- Persona Compiler overlays real-chat communication style, dyadic characteristics,
  behavior patterns, and evidence summary onto Persona Model V2.
- `/api/persona/create` returns `chat_analysis` and `persona_v2`; the frontend
  displays the analysis and carries the compiled persona into V2 simulation.
- Invalid or unidentifiable records do not produce invented chat analysis, and
  the V1-compatible persona response remains available.

## Phase 6 evidence retrieval

- Phase 5 output is registered in bounded, replaceable Episode and Evidence
  stores keyed by anonymous persona ID.
- Each turn builds a retrieval query from the current topic, observable user
  behavior, conflict indicators, and current simulation state.
- Lightweight concept, keyword, behavior, state, confidence, and recency signals
  rank a high-signal Top K slice; repeated delay requests prioritize historical
  delay Episodes over unrelated interactions.
- Records with fewer than three Episodes fall back to the summarized Persona to
  avoid overfitting sparse evidence.
- Context Builder injects selected target-language Episode samples into Response
  Generator. Strategy consumes the Persona snapshot, behavior patterns and
  Session Memory; the full chat log is never sent to either model on every turn.
- `/api/session/message` exposes evidence IDs, Episode IDs, retrieval mode, and
  scores for debugging without returning raw historical chat in metadata.

## Phase 7 consistency evaluator

- Evaluator scores persona, dyadic, style, emotional, evidence, and reaction
  proportionality consistency; it does not roleplay or change the decided action.
- A deterministic trigger runs the optional model call only for low decision
  confidence, major relationship changes, high conflict, sensitive actions, or
  obvious reply-length, emoji, and formality mismatches.
- Normal responses keep the standard Decision + Generation two-call path.
- Ordinary low scores are recorded without regeneration. Only persona
  violations, confirmed Memory contradictions, invented Persona traits,
  action/text contradictions, or ungrounded Guidance deviation may trigger one
  synchronous correction. No second evaluation loop is allowed.
- Evaluator failure never blocks the initial reply. Session metadata and logs
  record trigger reasons, scores, issues, retry count, and failure status.

## Phase 8 evaluation and release baseline

- Three fixed personas cover a direct responsibility-oriented advisor, a gentle
  conflict-avoidant friend, and a sensitive intimate partner.
- Six deterministic regression suites cover counterfactual user behavior,
  counterfactual personas, longitudinal state, chat evidence, no reply, and
  overreaction.
- Structured output performs exactly one JSON repair. Decision failure preserves
  the previous state and uses a neutral normal policy; Generator retries once
  before an action-aligned deterministic fallback; Evaluator failure remains
  non-blocking.
- A bounded metadata-only Turn Store records state, action, confidence, evidence
  IDs, and evaluator status. User and target text are stored only as SHA-256
  digests and lengths.
- The machine-readable quality baseline declares all eight PRD dimensions and
  offline/live release gates. Offline tests do not substitute for staging model
  quality and latency measurement.
- Local development uses `/`; production builds retain `/social-lab/` for GitHub
  Pages.

## Strategy / Evaluation V2.1 ownership update

- StrategyAgent owns advisory Guidance only. Simulation Decision Engine owns the
  final Response Policy and may deviate when Persona or context evidence supports
  the decision.
- EvaluationAgent V2 is the only active semantic quality evaluator in the V2
  main path. Its target is character fidelity, not politeness or persuasion.
- Feedback is bounded to one Strategy replan or one Simulation regeneration.
  Only the final candidate reaches the Turn Store and MemoryAgent.
- Session learning uses bounded numeric style preferences only. It cannot alter
  Persona, relationship state, warmth, final action, or helping intent.

## V2.1 release gate

- Keep `SIMULATION_AGENT_VERSION=v1` as the default and rollback path.
- Run paired human review on all 36 fixed cases before changing the default.
- Required gates: V2.1 win rate at least 55%, Persona consistency not below V1,
  hard-error rate at most 3%, and ordinary-turn Evaluation non-intervention at
  least 85%.
