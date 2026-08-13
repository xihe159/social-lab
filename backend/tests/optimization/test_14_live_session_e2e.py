from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.skipif(
    os.getenv("SOCIAL_LAB_RUN_LIVE_LLM") != "1",
    reason="Set SOCIAL_LAB_RUN_LIVE_LLM=1 to run live LLM E2E tests.",
)


def _payload() -> dict:
    return {
        "scenario": "social",
        "goal": "练习自然、尊重边界地邀请朋友周末喝咖啡",
        "outcome": "表达邀请，同时允许对方轻松拒绝",
        "role": "朋友",
        "relation": "普通朋友",
        "persona": {
            "title": "友好但比较忙的朋友",
            "style": "自然、简洁、边界感清晰",
            "speed": "正常",
            "focus": "是否有时间，以及邀请是否让人有压力",
            "risk": "连续施压或把拒绝理解成关系问题",
            "strategy": "简洁回应，明确自己的时间和意愿",
            "state": {
                "trust": 62,
                "respect": 68,
                "familiarity": 58,
                "affinity": 60,
                "authority": 20,
                "emotional": 18,
            },
        },
        "messages": [],
        "user_message": "这周末如果你有空，要不要一起喝杯咖啡？没空也完全没关系。",
    }


def test_live_session_message_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIMULATION_AGENT_VERSION", "v3")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("EVALUATION_EXECUTION_MODE", "development_sync")

    # Import after environment overrides so settings/factories see canary configuration.
    from app.main import app

    with TestClient(app) as client:
        response = client.post("/api/session/message", json=_payload())

    assert response.status_code == 200, response.text
    body = response.json()

    assert body["target_message"]["role"] == "target"
    assert isinstance(body["target_message"]["content"], str)

    simulation = body["simulation"]
    assert isinstance(simulation["reply"], str)
    assert isinstance(simulation["risk_flags"], list)
    assert isinstance(simulation["state_delta"], dict)

    state = body["updated_state"]
    assert set(("trust", "respect", "familiarity", "affinity", "authority", "emotional")) <= set(state)


def test_live_session_does_not_return_provider_error_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIMULATION_AGENT_VERSION", "v3")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("EVALUATION_EXECUTION_MODE", "development_sync")

    from app.main import app

    with TestClient(app) as client:
        response = client.post("/api/session/message", json=_payload())

    # A normal canary should succeed; this assertion also guards the public API
    # against accidentally exposing provider-level exception details.
    assert response.status_code == 200, response.text
    text = response.text.lower()
    assert "api key" not in text
    assert "traceback" not in text
    assert "openai" not in text
