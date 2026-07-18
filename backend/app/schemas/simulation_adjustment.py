from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SimulationAdjustmentSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )


class SimulationAdjustmentProfile(SimulationAdjustmentSchema):
    """Evaluation-derived controls that are temporary to one simulation session."""

    session_id: str = Field(min_length=1, max_length=120)
    style_adjustments: list[str]
    strategy_adjustments: list[str]
    source_evaluation_ids: list[str]
    expires_after_turns: int = Field(ge=1, le=10)

    @field_validator(
        "style_adjustments",
        "strategy_adjustments",
        "source_evaluation_ids",
    )
    @classmethod
    def keep_lists_bounded(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = str(value).strip()
            if item and item not in cleaned:
                cleaned.append(item[:200])
        return cleaned[:8]


class SessionAdjustmentMeta(SimulationAdjustmentSchema):
    """Safe API metadata; adjustment text stays inside the agent pipeline."""

    applied: bool = False
    activated_this_turn: bool = False
    style_adjustment_count: int = Field(default=0, ge=0, le=8)
    strategy_adjustment_count: int = Field(default=0, ge=0, le=8)
    remaining_turns: int = Field(default=0, ge=0, le=10)
