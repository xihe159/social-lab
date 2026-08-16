from __future__ import annotations

import re
from pathlib import Path


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_legacy_prompt_shims_still_import() -> None:
    from app.agents.prompts import (
        PERSONA_SYSTEM_PROMPT,
        STRATEGY_PROMPT_VERSION,
        build_persona_user_prompt,
    )
    from app.agents.simulation.prompts import (
        SIMULATION_PROMPT_VERSION,
        TURN_STATE_ANALYZER_SYSTEM_PROMPT,
    )

    assert PERSONA_SYSTEM_PROMPT
    assert STRATEGY_PROMPT_VERSION
    assert callable(build_persona_user_prompt)
    assert SIMULATION_PROMPT_VERSION
    assert TURN_STATE_ANALYZER_SYSTEM_PROMPT


def test_agents_no_longer_own_system_prompt_literals() -> None:
    backend = _backend_root()
    agents_root = backend / "app/agents"
    pattern = re.compile(r'^[A-Z][A-Z0-9_]*SYSTEM_PROMPT\s*=\s*"""', re.MULTILINE)
    offenders: list[str] = []
    for path in agents_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            offenders.append(str(path.relative_to(backend)))
    assert offenders == [], "Inline system prompts remain:\n" + "\n".join(offenders)


def test_known_inline_prompt_builders_are_removed() -> None:
    backend = _backend_root()
    expected_absent = {
        "app/agents/analysis_agent.py": "def _build_prompt(",
        "app/agents/prediction_agent.py": "def _build_prompt(",
        "app/agents/rewrite_agent.py": "def _build_prompt(",
        "app/agents/state_agent.py": "def _build_prompt(",
        "app/agents/memory_agent.py": "def _build_extractor_prompt(",
    }
    offenders: list[str] = []
    for relative, marker in expected_absent.items():
        path = backend / relative
        if path.exists() and marker in path.read_text(encoding="utf-8"):
            offenders.append(relative)
    assert offenders == [], "Inline prompt builders remain:\n" + "\n".join(offenders)
