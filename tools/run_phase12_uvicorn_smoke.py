from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def _find_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _get_json(url: str, timeout: float = 2.0) -> tuple[int, object]:
    try:
        with urlopen(url, timeout=timeout) as response:  # noqa: S310 - local smoke test only
            status = int(response.status)
            raw = response.read().decode("utf-8")
            return status, json.loads(raw)
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body: object = json.loads(raw)
        except json.JSONDecodeError:
            body = raw
        return int(exc.code), body


def _wait_until_ready(base_url: str, process: subprocess.Popen[bytes], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Uvicorn exited early with code {process.returncode}")
        try:
            status, body = _get_json(f"{base_url}/health")
            if status == 200 and isinstance(body, dict) and body.get("status") == "ok":
                return
        except (URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
        time.sleep(0.25)
    if last_error is not None:
        raise TimeoutError(f"Uvicorn did not become ready within {timeout:.1f}s: {last_error}")
    raise TimeoutError(f"Uvicorn did not become ready within {timeout:.1f}s")


def _assert_route(base_url: str, path: str, *, required_keys: tuple[str, ...] = ()) -> object:
    status, body = _get_json(f"{base_url}{path}")
    if status != 200:
        raise AssertionError(f"GET {path} returned HTTP {status}: {body!r}")
    if required_keys:
        if not isinstance(body, dict):
            raise AssertionError(f"GET {path} did not return a JSON object: {body!r}")
        missing = [key for key in required_keys if key not in body]
        if missing:
            raise AssertionError(f"GET {path} missing keys {missing}: {body!r}")
    print(f"PASS  GET {path} -> 200")
    return body


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 12: live Uvicorn HTTP smoke test")
    parser.add_argument("--backend", type=Path, default=None, help="Path to backend directory")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="0 chooses a free local port")
    parser.add_argument("--startup-timeout", type=float, default=25.0)
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    project_root = script_path.parents[1]
    backend = (args.backend or (project_root / "backend")).resolve()
    if not (backend / "app" / "main.py").exists():
        raise SystemExit(f"Could not find backend/app/main.py under: {backend}")

    host = args.host
    port = args.port or _find_free_port(host)
    base_url = f"http://{host}:{port}"

    print("=" * 72)
    print("PHASE 12: Live Uvicorn + HTTP smoke test")
    print("=" * 72)
    print(f"Python : {sys.executable}")
    print(f"Backend: {backend}")
    print(f"URL    : {base_url}")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend) + os.pathsep + env.get("PYTHONPATH", "")

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
        "--log-level",
        "info",
    ]

    log_file = tempfile.NamedTemporaryFile(
        mode="w+b",
        prefix="social_lab_phase12_",
        suffix=".log",
        delete=False,
    )
    log_path = Path(log_file.name)
    process: subprocess.Popen[bytes] | None = None

    try:
        process = subprocess.Popen(
            command,
            cwd=backend,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        _wait_until_ready(base_url, process, args.startup_timeout)
        print("PASS  Uvicorn started and /health became ready")

        health = _assert_route(base_url, "/health", required_keys=("status",))
        if isinstance(health, dict) and health.get("status") != "ok":
            raise AssertionError(f"/health status must be 'ok': {health!r}")

        _assert_route(base_url, "/")
        openapi = _assert_route(base_url, "/openapi.json", required_keys=("openapi", "info", "paths"))
        if not isinstance(openapi, dict):
            raise AssertionError("OpenAPI response must be a JSON object")

        paths = openapi.get("paths", {})
        required_paths = {
            "/health",
            "/api/persona/create",
            "/api/session/message",
            "/api/session/report",
            "/api/session/strategy",
            "/api/session/evaluate",
        }
        missing_paths = sorted(required_paths - set(paths))
        if missing_paths:
            raise AssertionError(f"OpenAPI missing core routes: {missing_paths}")
        print(f"PASS  OpenAPI contains {len(required_paths)} required core routes")

        if process.poll() is not None:
            raise AssertionError(f"Uvicorn exited unexpectedly with code {process.returncode}")
        print("PASS  Uvicorn process remained alive through all requests")
        print("\nPHASE 12 PASSED")
        return 0
    except Exception as exc:
        print(f"\nPHASE 12 FAILED: {exc}", file=sys.stderr)
        return_code = 1
        return return_code
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        log_file.flush()
        log_file.close()
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                print("\n--- Uvicorn log ---")
                print(text)
            try:
                log_path.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
