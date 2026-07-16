from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

from pydantic import BaseModel, ValidationError


T = TypeVar("T", bound=BaseModel)


class StructuredOutputRepairError(RuntimeError):
    pass


async def validate_with_single_repair(
    *,
    content: str,
    output_model: type[T],
    repair: Callable[[str], Awaitable[str]],
) -> T:
    """Validate structured output and invoke the supplied repair exactly once."""

    try:
        return output_model.model_validate_json(content)
    except ValidationError:
        repaired_content = await repair(content)
        if not repaired_content:
            raise StructuredOutputRepairError("JSON repair returned empty content.")
        try:
            return output_model.model_validate_json(repaired_content)
        except ValidationError as exc:
            raise StructuredOutputRepairError(
                "Structured output remained invalid after one JSON repair."
            ) from exc

