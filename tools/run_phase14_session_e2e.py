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
from urllib.request import Request, urlopen


def _find_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _request_json(
    method: str,
    url: str,
    *,
    payload: dict | None = None,
    timeout: float = 90.0,
) -> tuple[int, object]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, headers=headers, method=method)  # noqa: S310 - localhost canary
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - localhost canary
            raw = response.read().decode("utf-8")
            return int(response.status), json.loads(raw) if raw else None
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
            status, body = _request_json("GET", f"{base_url}/health", timeout=2.0)
            if status == 200 and isinstance(body, dict) and body.get("status") == "ok":
                return
        except (URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
        time.sleep(0.25)
    if last_error:
        raise TimeoutError(f"Uvicorn did not become ready: {last_error}")
    raise TimeoutError("Uvicorn did not become ready")


def _payload() -> dict:
    # Deliberately benign and compact: this canary should exercise the normal path,
    # not safety blocking or evidence-dataset behavior.
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
                "emotional": 18
            }
        },
        "messages": [],
        "user_message": "这周末如果你有空，要不要一起喝杯咖啡？没空也完全没关系。"
    }


def _assert_session_response(body: object) -> dict:
    if not isinstance(body, dict):
        raise AssertionError(f"Session response must be an object, got {type(body).__name__}")

    required = {"target_message", "simulation", "updated_state"}
    missing = sorted(required - set(body))
    if missing:
        raise AssertionError(f"Session response missing required fields: {missing}")

    target = body["target_message"]
    if not isinstance(target, dict):
        raise AssertionError("target_message must be an object")
    if target.get("role") != "target":
        raise AssertionError(f"target_message.role must be 'target': {target!r}")
    if not isinstance(target.get("content"), str):
        raise AssertionError("target_message.content must be a string")

    simulation = body["simulation"]
    if not isinstance(simulation, dict):
        raise AssertionError("simulation must be an object")
    for key in ("reply", "attitude", "emotion", "perceived_user_tone", "state_delta", "risk_flags"):
        if key not in simulation:
            raise AssertionError(f"simulation missing field: {key}")

    state = body["updated_state"]
    if not isinstance(state, dict):
        raise AssertionError("updated_state must be an object")
    for key in ("trust", "respect", "familiarity", "affinity", "authority", "emotional"):
        if key not in state:
            raise AssertionError(f"updated_state missing field: {key}")

    return body


def _safe_meta(body: dict) -> None:
    # Print only bounded operational metadata. Do not dump prompts, memory, or full response payloads.
    target = body.get("target_message") or {}
    content = target.get("content") if isinstance(target, dict) else None
    print(f"INFO  target reply chars: {len(content) if isinstance(content, str) else 0}")

    strategy = body.get("strategy_meta")
    if isinstance(strategy, dict):
        print(
            "INFO  strategy: "
            f"final_action={strategy.get('final_action') or strategy.get('simulation_action')}, "
            f"fallback_used={strategy.get('fallback_used')}"
        )

    evaluation = body.get("evaluation_meta")
    if isinstance(evaluation, dict):
        print(
            "INFO  evaluation: "
            f"evaluated={evaluation.get('evaluated')}, "
            f"fallback_used={evaluation.get('fallback_used')}"
        )

    runtime = body.get("runtime_meta")
    if isinstance(runtime, dict):
        keys = sorted(runtime.keys())
        print(f"INFO  runtime_meta fields: {', '.join(keys)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 14: live /api/session/message E2E canary")
    parser.add_argument("--backend", type=Path, default=None)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--startup-timeout", type=float, default=30.0)
    parser.add_argument("--request-timeout", type=float, default=120.0)
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    project_root = script_path.parents[1]
    backend = (args.backend or (project_root / "backend")).resolve()
    if not (backend / "app/main.py").exists():
        raise SystemExit(f"Could not find backend/app/main.py under: {backend}")

    host = args.host
    port = args.port or _find_free_port(host)
    base_url = f"http://{host}:{port}"

    print("=" * 72)
    print("PHASE 14: Live /api/session/message end-to-end canary")
    print("=" * 72)
    print(f"Python : {sys.executable}")
    print(f"Backend: {backend}")
    print(f"URL    : {base_url}")
    print("Mode   : v3 + development_sync")
    print("LLM    : live calls will be used")
    print()

    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend) + os.pathsep + env.get("PYTHONPATH", "")
    env["SIMULATION_AGENT_VERSION"] = "v3"
    env["APP_ENV"] = "development"
    env["EVALUATION_EXECUTION_MODE"] = "development_sync"

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
        prefix="social_lab_phase14_",
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
        print("PASS  Uvicorn ready")

        payload = _payload()
        started = time.perf_counter()
        status, body = _request_json(
            "POST",
            f"{base_url}/api/session/message",
            payload=payload,
            timeout=args.request_timeout,
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000)

        if status != 200:
            raise AssertionError(f"POST /api/session/message returned HTTP {status}: {body!r}")
        print(f"PASS  POST /api/session/message -> 200 ({elapsed_ms} ms)")

        parsed = _assert_session_response(body)
        print("PASS  SessionMessageResponse required contract")
        _safe_meta(parsed)

        # Verify the server is still healthy after the expensive request.
        health_status, health = _request_json("GET", f"{base_url}/health", timeout=3.0)
        if health_status != 200 or not isinstance(health, dict) or health.get("status") != "ok":
            raise AssertionError(f"Server unhealthy after session request: {health_status} {health!r}")
        if process.poll() is not None:
            raise AssertionError(f"Uvicorn exited after session request with code {process.returncode}")
        print("PASS  Server remained healthy after live session turn")

        print()
        print("PHASE 14 PASSED")
        return 0
    except Exception as exc:
        print(f"\nPHASE 14 FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
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
