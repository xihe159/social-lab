from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _read_json(url: str) -> tuple[int, dict]:
    with urlopen(url, timeout=2.0) as response:  # noqa: S310 - localhost test only
        return int(response.status), json.loads(response.read().decode("utf-8"))


@pytest.fixture(scope="module")
def live_server():
    backend = _backend_root()
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend) + os.pathsep + env.get("PYTHONPATH", "")

    log_file = tempfile.NamedTemporaryFile(mode="w+b", delete=False)
    log_path = Path(log_file.name)
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=backend,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

    try:
        deadline = time.monotonic() + 25.0
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break
            try:
                status, body = _read_json(f"{base_url}/health")
                if status == 200 and body.get("status") == "ok":
                    yield base_url, process
                    return
            except (URLError, TimeoutError, ConnectionError):
                pass
            time.sleep(0.25)

        log_file.flush()
        text = log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Uvicorn failed to start.\n{text}")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        log_file.close()
        try:
            log_path.unlink()
        except OSError:
            pass


def test_live_health_endpoint(live_server) -> None:
    base_url, process = live_server
    status, body = _read_json(f"{base_url}/health")
    assert status == 200
    assert body.get("status") == "ok"
    assert process.poll() is None


def test_live_root_endpoint(live_server) -> None:
    base_url, process = live_server
    status, body = _read_json(f"{base_url}/")
    assert status == 200
    assert isinstance(body, dict)
    assert process.poll() is None


def test_live_openapi_contains_core_routes(live_server) -> None:
    base_url, process = live_server
    status, body = _read_json(f"{base_url}/openapi.json")
    assert status == 200
    assert body.get("openapi")
    paths = body.get("paths", {})
    for path in (
        "/health",
        "/api/persona/create",
        "/api/session/message",
        "/api/session/report",
        "/api/session/strategy",
        "/api/session/evaluate",
    ):
        assert path in paths
    assert process.poll() is None
