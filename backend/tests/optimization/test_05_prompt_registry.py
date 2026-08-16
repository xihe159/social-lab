from __future__ import annotations

import pytest

from app.prompts import prompt_registry
from app.prompts.base import PromptDefinition, PromptRegistry


EXPECTED_PROMPTS = {
    "persona.create",
    "simulation.reply.legacy",
    "report.coach.legacy",
    "state.evaluate",
    "memory.update.legacy",
    "safety.check",
    "strategy.guidance",
    "evaluation.audit",
    "simulation.turn_state",
    "simulation.decision",
    "simulation.turn_decision",
    "simulation.response_generation",
    "simulation.consistency",
    "report.analysis",
    "report.prediction",
    "report.rewrite",
    "memory.extract",
}


def test_registry_contains_all_expected_prompts() -> None:
    assert set(prompt_registry.keys()) == EXPECTED_PROMPTS


def test_every_prompt_has_complete_metadata() -> None:
    for definition in prompt_registry.definitions():
        assert definition.key.strip()
        assert definition.version.strip()
        assert definition.system_prompt.strip()
        assert callable(definition.user_builder)
        assert 0.0 <= definition.temperature <= 2.0


def test_prompt_registry_rejects_duplicate_keys() -> None:
    registry = PromptRegistry()
    definition = PromptDefinition(
        key="test.prompt",
        version="v1",
        system_prompt="system",
        user_builder=lambda **_: "user",
    )
    registry.register(definition)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(definition)


def test_prompt_render_preserves_runtime_metadata() -> None:
    registry = PromptRegistry()
    registry.register(
        PromptDefinition(
            key="test.render",
            version="v7",
            system_prompt=" system ",
            user_builder=lambda *, name: f" hello {name} ",
            temperature=0.25,
        )
    )
    rendered = registry.render("test.render", name="Social Lab")
    assert rendered.key == "test.render"
    assert rendered.version == "v7"
    assert rendered.system_prompt == " system "
    assert rendered.user_prompt == "hello Social Lab"
    assert rendered.temperature == 0.25


def test_known_temperatures_are_centralized() -> None:
    expected = {
        "report.analysis": 0.15,
        "report.prediction": 0.15,
        "report.rewrite": 0.25,
        "memory.extract": 0.2,
        "strategy.guidance": 0.2,
        "evaluation.audit": 0.1,
        "simulation.turn_state": 0.2,
        "simulation.decision": 0.3,
        "simulation.turn_decision": 0.25,
        "simulation.response_generation": 0.55,
        "simulation.consistency": 0.1,
    }
    actual = {key: prompt_registry.get(key).temperature for key in expected}
    assert actual == expected
