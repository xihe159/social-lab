from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


PromptBuilder = Callable[..., str]


@dataclass(frozen=True, slots=True)
class PromptDefinition:
    """Immutable prompt metadata owned by the prompt layer."""

    key: str
    version: str
    system_prompt: str
    user_builder: PromptBuilder
    temperature: float = 0.3
    description: str = ""

    def render(self, **kwargs: Any) -> "RenderedPrompt":
        return RenderedPrompt(
            key=self.key,
            version=self.version,
            system_prompt=self.system_prompt,
            user_prompt=self.user_builder(**kwargs).strip(),
            temperature=self.temperature,
        )


@dataclass(frozen=True, slots=True)
class RenderedPrompt:
    key: str
    version: str
    system_prompt: str
    user_prompt: str
    temperature: float


class PromptRegistry:
    """Single source of truth for prompt discovery and runtime rendering."""

    def __init__(self) -> None:
        self._definitions: dict[str, PromptDefinition] = {}

    def register(self, definition: PromptDefinition) -> PromptDefinition:
        key = definition.key.strip()
        if not key:
            raise ValueError("Prompt key must not be empty")
        if key in self._definitions:
            raise ValueError(f"Prompt already registered: {key}")
        if not definition.version.strip():
            raise ValueError(f"Prompt version must not be empty: {key}")
        if not definition.system_prompt.strip():
            raise ValueError(f"System prompt must not be empty: {key}")
        self._definitions[key] = definition
        return definition

    def get(self, key: str) -> PromptDefinition:
        try:
            return self._definitions[key]
        except KeyError as exc:
            known = ", ".join(sorted(self._definitions))
            raise KeyError(f"Unknown prompt '{key}'. Known prompts: {known}") from exc

    def render(self, key: str, **kwargs: Any) -> RenderedPrompt:
        return self.get(key).render(**kwargs)

    def keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._definitions))

    def definitions(self) -> tuple[PromptDefinition, ...]:
        return tuple(self._definitions[key] for key in self.keys())

    def metadata(self) -> list[dict[str, Any]]:
        return [
            {
                "key": item.key,
                "version": item.version,
                "temperature": item.temperature,
                "description": item.description,
            }
            for item in self.definitions()
        ]
