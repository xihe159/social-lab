# SimulationAgentV2 Pipeline Refactor

## Goal

Turn `SimulationAgentV2` from a workflow controller into a compatibility facade over a small, explicit pipeline.

## New ownership model

```text
SessionOrchestrator
  Safety -> Simulation -> State -> Memory
                 |
                 v
        SimulationAgentV2 (facade)
                 |
                 v
        SimulationPipeline.run()
                 |
                 +-- PrepareStage
                 +-- TurnAnalysisStage
                 +-- StrategyStage
                 +-- DecisionStage
                 +-- GenerationStage
                 +-- EvaluationAuditStage
                 +-- AssemblyStage
                 +-- PersistenceStage
```

### Stage responsibilities

| Stage | Owns | Must not own |
|---|---|---|
| Prepare | IDs, PersonaV2 adaptation, state bootstrap, evidence context, temporary adjustment input | LLM decision |
| TurnAnalysis | user intent/behavior interpretation and state update | visible reply |
| Strategy | non-binding guidance | final action |
| Decision | target-person response policy | surface wording |
| Generation | wording under a fixed response policy | state/action changes |
| EvaluationAudit | quality audit and bounded cross-turn learning | current-turn rewrite/replan |
| Assembly | API compatibility mapping | model calls |
| Persistence | privacy-safe turn record and metrics | business decisions |

## Important semantic change

Old V2 could run:

```text
Generate -> Evaluate -> Revise/Replan -> Generate -> Evaluate
```

The refactor deliberately removes current-turn evaluator intervention. The current reply becomes fixed after `GenerationStage`; Evaluation can only audit it and contribute bounded temporary adjustments to later turns.

This matches the response-ownership principle already adopted by the repository's V3: one component owns the visible reaction, while Strategy is advisory and Evaluation is audit-only.

## Version routing

Production remains `v3`.

- `SIMULATION_AGENT_VERSION=v2` -> still resolves to `v3`
- `SIMULATION_AGENT_VERSION=v2.1` -> still resolves to `v3`
- `SIMULATION_AGENT_VERSION=v2_pipeline` -> explicitly runs the refactored V2 pipeline for QA/A-B testing

Do not change production to `v2_pipeline` before regression tests and latency/quality comparison.

## Extension examples

### Replace only the Decision stage

Create a new class implementing:

```python
class MyDecisionStage:
    name = "persona_decision_v2"

    async def execute(self, context):
        ...
        return context
```

Then build another stage tuple. No `SimulationAgentV2` subclass is necessary.

### Insert a candidate reranker

Place a new stage between `DecisionStage` and `GenerationStage` if it changes policy, or between `GenerationStage` and `EvaluationAuditStage` if it only chooses among already-generated candidates.

### Add tracing

Prefer a stage wrapper or pipeline-level hook rather than adding logging branches to every Agent.
