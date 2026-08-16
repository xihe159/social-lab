from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PHASES = [
    ("00", "环境与优化文件完整性", "test_00_environment_and_files.py"),
    ("01", "Pipeline 包导入", "test_01_pipeline_imports.py"),
    ("02", "SimulationAgentV2 Pipeline 契约", "test_02_pipeline_contract.py"),
    ("03", "统一 Agent Failure Runtime", "test_03_failure_runtime.py"),
    ("04", "失败策略矩阵", "test_04_failure_policy_matrix.py"),
    ("05", "PromptRegistry 核心", "test_05_prompt_registry.py"),
    ("06", "Prompt 迁移/兼容层", "test_06_prompt_migration_guards.py"),
    ("07", "Failure Policy 接线完整性", "test_07_failure_policy_wiring.py"),
    ("08", "CoachAgent 降级行为", "test_08_coach_resilience.py"),
    ("09", "生产 V3 Failure Policy 接线", "test_09_v3_failure_wiring.py"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-phase", default="00")
    parser.add_argument("--to-phase", default="09")
    parser.add_argument("--continue-on-failure", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    backend = repo_root / "backend"
    tests = backend / "tests" / "optimization"

    if not (backend / "app").is_dir():
        print(f"ERROR: {backend / 'app'} 不存在。请把 tools/ 放在 social-lab 项目根目录。")
        return 2

    selected = [
        item for item in PHASES
        if args.from_phase <= item[0] <= args.to_phase
    ]
    failures: list[str] = []

    for number, title, filename in selected:
        print("\n" + "=" * 72)
        print(f"PHASE {number}: {title}")
        print("=" * 72)
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            str(tests / filename),
        ]
        result = subprocess.run(command, cwd=backend, check=False)
        if result.returncode != 0:
            failures.append(number)
            print(f"\nFAILED at PHASE {number}: {title}")
            if not args.continue_on_failure:
                print("先修复本阶段，再继续下一阶段。")
                return result.returncode
        else:
            print(f"PASSED PHASE {number}: {title}")

    print("\n" + "=" * 72)
    if failures:
        print("完成，但以下阶段失败：" + ", ".join(failures))
        return 1
    print("全部阶段通过。现在可以继续执行完整 pytest -q。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
