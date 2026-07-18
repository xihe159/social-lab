from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


BASELINE_CASES_PATH = Path(__file__).with_name(
    "strategy_evaluation_baseline_cases.json"
)


class BaselineModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RelationshipCondition(BaselineModel):
    trust_tier: Literal["low", "medium", "high"]
    conflict_tier: Literal["low", "medium", "high"]
    repeated_pressure: bool


class ExpectedBehavior(BaselineModel):
    semantic_behavior: Literal[
        "answer",
        "acknowledge",
        "clarify",
        "accept",
        "refuse",
        "set_boundary",
        "defer",
        "no_reply",
        "end_conversation",
    ]
    allowed_current_actions: list[str] = Field(min_length=1)
    reply_length: Literal["very_short", "short", "medium"]
    max_abs_state_delta: float = Field(gt=0, le=0.25)
    requires_evidence_refs: bool
    silent: bool
    extreme_action_allowed: bool


class BaselineCase(BaselineModel):
    case_id: str = Field(pattern=r"^se_baseline_\d{3}$")
    category: str
    persona_id: str
    scenario: Literal["advisor", "work", "relationship"]
    context_summary: str
    relationship: RelationshipCondition
    user_message: str = Field(min_length=1)
    expected: ExpectedBehavior


class BaselineCatalog(BaselineModel):
    schema_version: str
    baseline_id: str
    personas: list[str]
    required_categories: list[str]
    cases: list[BaselineCase] = Field(min_length=30)

    @model_validator(mode="after")
    def validate_catalog(self) -> "BaselineCatalog":
        case_ids = [item.case_id for item in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("baseline case_id values must be unique")

        categories = {item.category for item in self.cases}
        missing_categories = set(self.required_categories) - categories
        if missing_categories:
            raise ValueError(
                f"baseline categories missing: {sorted(missing_categories)}"
            )

        persona_ids = {item.persona_id for item in self.cases}
        missing_personas = set(self.personas) - persona_ids
        if missing_personas:
            raise ValueError(
                f"baseline personas missing: {sorted(missing_personas)}"
            )

        return self


class BaselineObservation(BaselineModel):
    case_id: str
    system_version: str
    reply: str
    selected_action: str
    persona_consistency: int = Field(ge=0, le=100)
    relationship_continuity: int = Field(ge=0, le=100)
    style_consistency: int = Field(ge=0, le=100)
    human_overall: int = Field(ge=0, le=100)
    latency_ms: int = Field(ge=0)
    evidence_refs: list[str]
    notes: list[str] = Field(default_factory=list)


class BaselineSummary(BaselineModel):
    baseline_id: str
    system_version: str
    case_count: int
    persona_consistency: float
    relationship_continuity: float
    style_consistency: float
    human_overall: float
    average_latency_ms: float
    p95_latency_ms: int
    action_contract_rate: float
    silent_contract_rate: float
    evidence_contract_rate: float


def load_baseline_catalog(
    path: Path = BASELINE_CASES_PATH,
) -> BaselineCatalog:
    return BaselineCatalog.model_validate_json(path.read_text(encoding="utf-8"))


def summarize_observations(
    observations: list[BaselineObservation],
    *,
    catalog: BaselineCatalog | None = None,
) -> BaselineSummary:
    catalog = catalog or load_baseline_catalog()
    expected_ids = {item.case_id for item in catalog.cases}
    observation_ids = [item.case_id for item in observations]

    if len(observation_ids) != len(set(observation_ids)):
        raise ValueError("observations contain duplicate case_id values")
    if set(observation_ids) != expected_ids:
        missing = sorted(expected_ids - set(observation_ids))
        unexpected = sorted(set(observation_ids) - expected_ids)
        raise ValueError(
            f"observations must cover the fixed baseline; missing={missing}, "
            f"unexpected={unexpected}"
        )

    versions = {item.system_version for item in observations}
    if len(versions) != 1:
        raise ValueError("all observations must use one system_version")

    case_by_id = {item.case_id: item for item in catalog.cases}
    action_passes = 0
    silent_checks = 0
    silent_passes = 0
    evidence_checks = 0
    evidence_passes = 0

    for observation in observations:
        expected = case_by_id[observation.case_id].expected
        if observation.selected_action in expected.allowed_current_actions:
            action_passes += 1

        if expected.silent:
            silent_checks += 1
            if not observation.reply.strip():
                silent_passes += 1

        if expected.requires_evidence_refs:
            evidence_checks += 1
            if observation.evidence_refs:
                evidence_passes += 1

    latencies = sorted(item.latency_ms for item in observations)
    p95_index = max(0, math.ceil(len(latencies) * 0.95) - 1)

    return BaselineSummary(
        baseline_id=catalog.baseline_id,
        system_version=versions.pop(),
        case_count=len(observations),
        persona_consistency=_average(
            item.persona_consistency for item in observations
        ),
        relationship_continuity=_average(
            item.relationship_continuity for item in observations
        ),
        style_consistency=_average(
            item.style_consistency for item in observations
        ),
        human_overall=_average(item.human_overall for item in observations),
        average_latency_ms=_average(item.latency_ms for item in observations),
        p95_latency_ms=latencies[p95_index],
        action_contract_rate=round(action_passes / len(observations), 4),
        silent_contract_rate=(
            round(silent_passes / silent_checks, 4) if silent_checks else 1.0
        ),
        evidence_contract_rate=(
            round(evidence_passes / evidence_checks, 4)
            if evidence_checks
            else 1.0
        ),
    )


def load_observations(path: Path) -> list[BaselineObservation]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [BaselineObservation.model_validate(item) for item in payload]


def _average(values) -> float:
    items = list(values)
    if not items:
        return 0.0
    return round(sum(items) / len(items), 2)
