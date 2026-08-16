# Social Lab Prompt Management Architecture

## Goal

Prompt wording should not be scattered across Agent implementations. Each LLM call must be traceable to one prompt key and one prompt version.

## Layers

```text
app/agents/*
    business flow / deterministic rules / fallback
            |
            v
app/prompts/*
    PromptDefinition
    - key
    - version
    - system_prompt
    - user_builder
    - temperature
            |
            v
app/llm/client.py
    provider/model/transport/structured output
```

`PromptRegistry` is deliberately a catalog, not a dependency injector and not an LLM client.

## Naming

Use domain-oriented stable keys:

```text
persona.create
state.evaluate
safety.check
strategy.guidance
evaluation.audit
memory.extract
report.analysis
report.prediction
report.rewrite
simulation.turn_state
simulation.decision
simulation.response_generation
simulation.consistency
```

Keys describe responsibility. Versions describe behavior revisions.

## Version rule

A version must change when a modification can alter model behavior, for example:

- system instruction changes;
- user prompt layout changes materially;
- evidence priority changes;
- output interpretation constraints change;
- temperature changes.

Formatting-only Python refactors that render exactly the same prompt do not require a version bump.

## Runtime metadata

Use `prompt_registry.metadata()` for inventory and observability. Avoid logging full rendered prompts in production because prompts can contain user/persona/session data. Prefer logging:

```text
prompt_key
prompt_version
temperature
trace_id
session_id
turn_id
latency
success/degraded/failure
```

## Compatibility

`app.agents.prompts` and `app.agents.simulation.prompts` are compatibility shims. Existing code may import them while migration is ongoing, but new code should import definitions from `app.prompts.<domain>`.

## Future extensions

The current registry is intentionally code-defined. If Prompt experimentation is needed later, add a separate override layer rather than letting Agents read YAML/DB/environment state directly. A safe progression is:

```text
code default PromptDefinition
        ↓
validated experiment override
        ↓
rendered immutable prompt snapshot
        ↓
LLM call + prompt key/version recorded in metrics
```

This keeps production fallback deterministic and makes rollback straightforward.
