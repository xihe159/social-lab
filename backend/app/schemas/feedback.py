from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class InternalCorrection(BaseModel):
    """Shared internal retry constraints for Strategy and Simulation."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )

    keep: list[str]
    change: list[str]
    must_not: list[str]

    @field_validator("keep", "change", "must_not")
    @classmethod
    def clean_items(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = str(value).strip()
            if item and item not in cleaned:
                cleaned.append(item[:240])
        return cleaned[:8]
