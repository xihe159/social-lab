from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_supported_python_version() -> None:
    assert sys.version_info >= (3, 10), (
        "Social Lab uses Python 3.10+ syntax (PEP 604 unions, slots dataclasses)."
    )


def test_app_package_is_importable() -> None:
    module = importlib.import_module("app")
    assert module is not None


def test_previous_optimization_files_exist() -> None:
    backend = _backend_root()
    required = [
        "app/agents/simulation/pipeline/__init__.py",
        "app/agents/simulation/pipeline/context.py",
        "app/agents/simulation/pipeline/runner.py",
        "app/agents/simulation/pipeline/services.py",
        "app/agents/simulation/pipeline/runtime.py",
        "app/agents/simulation/pipeline/stages.py",
        "app/agents/simulation/pipeline/utils.py",
        "app/core/agent_failure.py",
        "app/agents/failure_policies.py",
        "app/prompts/__init__.py",
        "app/prompts/base.py",
        "app/prompts/catalog.py",
    ]
    missing = [item for item in required if not (backend / item).is_file()]
    assert not missing, "Missing optimized files:\n" + "\n".join(missing)


def test_no_pipeline_module_directory_name_collision() -> None:
    backend = _backend_root()
    package_dir = backend / "app/agents/simulation/pipeline"
    module_file = backend / "app/agents/simulation/pipeline.py"
    assert package_dir.is_dir(), "simulation/pipeline must be a package directory"
    assert not module_file.exists(), (
        "Do not keep both simulation/pipeline.py and simulation/pipeline/. "
        "They create ambiguous imports."
    )
