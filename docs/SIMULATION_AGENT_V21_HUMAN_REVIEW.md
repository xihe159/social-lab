# SimulationAgent V2.1 paired human review

Use every case in
`backend/evaluation/strategy_evaluation_baseline_cases.json`. Run each case once
with `SIMULATION_AGENT_VERSION=v1` and once with `v2.1`; hide version labels and
randomize left/right order before review.

For each pair, record:

- winner: `v1`, `v2.1`, or `tie`;
- naturalness, Persona consistency, and emotional continuity on a 1–5 scale;
- whether either V2.1 output contains a hard error;
- whether Evaluation changed an ordinary V2.1 turn.

Load the completed JSON as `PairedHumanReview` records and call
`summarize_paired_reviews`. The release gate passes only when all 36 case IDs are
present and:

- V2.1 wins at least 55% of decisive comparisons (ties excluded);
- average Persona consistency is not below V1;
- V2.1 hard-error rate is at most 3%;
- Evaluation leaves at least 85% of ordinary turns unchanged.

Until all gates pass, keep `SIMULATION_AGENT_VERSION=v1` as the production
default. Human review is intentionally not replaced by automated scoring.
