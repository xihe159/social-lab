from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    backend = root / "backend"

    print("=" * 72)
    print("PHASE 14B: V3 runtime semantics regression")
    print("=" * 72)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/optimization/test_14b_v3_runtime_semantics.py",
    ]
    completed = subprocess.run(command, cwd=backend, env=env)
    if completed.returncode:
        print("\nPHASE 14B FAILED")
        return completed.returncode

    print("\nPHASE 14B PASSED")
    print("Next: rerun tools/run_phase14_session_e2e.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
