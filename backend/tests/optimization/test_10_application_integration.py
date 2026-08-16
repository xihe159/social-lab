from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


CORE_ROUTES = {
    "/",
    "/health",
    "/api/persona/create",
    "/api/session/message",
    "/api/session/report",
    "/api/session/strategy",
    "/api/session/evaluate",
    "/api/session/metrics",
}


def _load_app() -> FastAPI:
    """Import the production app exactly as uvicorn does."""
    from app.main import app

    assert isinstance(app, FastAPI)
    return app


def test_production_app_imports_without_cycle() -> None:
    """Prompt/Pipeline/Failure-Policy refactors must coexist at app import time."""
    app = _load_app()
    assert app is not None


def test_openapi_generation_succeeds() -> None:
    """Generating OpenAPI imports/inspects every registered request/response model."""
    app = _load_app()
    schema = app.openapi()

    assert schema["openapi"]
    assert isinstance(schema.get("paths"), dict)
    assert schema["paths"]


def test_core_routes_are_still_registered() -> None:
    """Architecture refactors must not silently drop public API routes."""
    app = _load_app()
    paths = set(app.openapi()["paths"])

    missing = sorted(CORE_ROUTES - paths)
    assert not missing, "Core API routes disappeared after refactor: " + ", ".join(missing)


def test_health_endpoint_works_without_llm_call() -> None:
    app = _load_app()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "ok"
    assert payload.get("service") == "social-lab-agent-api"


def test_root_endpoint_works_without_llm_call() -> None:
    app = _load_app()

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert "version" in payload
    assert payload.get("health") == "/health"
    assert payload.get("docs") == "/docs"


def test_openapi_endpoint_is_served() -> None:
    app = _load_app()

    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("paths"), dict)
    assert CORE_ROUTES.issubset(set(payload["paths"]))
