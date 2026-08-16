from __future__ import annotations

import argparse
import re
from pathlib import Path


SYSTEM_BLOCK = r'\n{{0,2}}{name}\s*=\s*"""[\s\S]*?"""\.strip\(\)\s*\n'


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Could not find expected text for {label}")
    return text.replace(old, new, 1)


def regex_replace_once(text: str, pattern: str, replacement: str, *, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count == 0:
        return text
    return updated


def ensure_import(text: str, *, anchor: str, import_line: str, label: str) -> str:
    if import_line in text:
        return text
    return replace_once(text, anchor, anchor + import_line + "\n", label=label)



def patch_persona(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = ensure_import(
        text,
        anchor="from app.llm.client import generate_structured\n",
        import_line="from app.prompts.persona import PERSONA_PROMPT",
        label="persona prompt definition import",
    )
    text = text.replace(
        "output_model=PersonaDraftResponse,\n        )",
        "output_model=PersonaDraftResponse,\n            temperature=PERSONA_PROMPT.temperature,\n        )",
    )
    path.write_text(text, encoding="utf-8")


def patch_safety(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = ensure_import(
        text,
        anchor="from app.llm.client import LLMClientError, generate_structured\n",
        import_line="from app.prompts.session import SAFETY_PROMPT",
        label="safety prompt definition import",
    )
    text = text.replace(
        "output_model=SafetyCheckResponse,\n            )",
        "output_model=SafetyCheckResponse,\n                temperature=SAFETY_PROMPT.temperature,\n            )",
    )
    path.write_text(text, encoding="utf-8")


def patch_simulation_v1(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = ensure_import(
        text,
        anchor="from app.llm.client import generate_structured\n",
        import_line="from app.prompts.session import SIMULATION_LEGACY_PROMPT",
        label="simulation v1 prompt definition import",
    )
    text = text.replace("temperature=0.55,", "temperature=SIMULATION_LEGACY_PROMPT.temperature,")
    path.write_text(text, encoding="utf-8")

def patch_analysis(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = ensure_import(
        text,
        anchor="from app.llm.client import LLMClientError, generate_structured\n",
        import_line="from app.prompts.report import ANALYSIS_PROMPT, build_analysis_user_prompt",
        label="analysis prompt import",
    )
    text = regex_replace_once(
        text,
        SYSTEM_BLOCK.format(name="ANALYSIS_SYSTEM_PROMPT"),
        "\n",
        label="ANALYSIS_SYSTEM_PROMPT",
    )
    text = text.replace("system_prompt=ANALYSIS_SYSTEM_PROMPT,", "system_prompt=ANALYSIS_PROMPT.system_prompt,")
    text = text.replace("user_prompt=self._build_prompt(", "user_prompt=build_analysis_user_prompt(")
    text = text.replace("temperature=0.15,", "temperature=ANALYSIS_PROMPT.temperature,")
    text = regex_replace_once(
        text,
        r'\n    def _build_prompt\([\s\S]*?\n    @staticmethod\n    def _trace_payload',
        "\n    @staticmethod\n    def _trace_payload",
        label="AnalysisAgent._build_prompt",
    )
    # Current main uses _pretty only in the removed prompt builder.
    text = regex_replace_once(
        text,
        r'\n    @staticmethod\n    def _pretty\(value: Any\) -> str:[\s\S]*?\Z',
        "\n",
        label="AnalysisAgent._pretty",
    )
    path.write_text(text, encoding="utf-8")


def patch_prediction(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = ensure_import(
        text,
        anchor="from app.llm.client import generate_structured\n",
        import_line="from app.prompts.report import PREDICTION_PROMPT, build_prediction_user_prompt",
        label="prediction prompt import",
    )
    text = regex_replace_once(
        text,
        SYSTEM_BLOCK.format(name="PREDICTION_SYSTEM_PROMPT"),
        "\n",
        label="PREDICTION_SYSTEM_PROMPT",
    )
    text = text.replace("system_prompt=PREDICTION_SYSTEM_PROMPT,", "system_prompt=PREDICTION_PROMPT.system_prompt,")
    text = text.replace(
        "user_prompt=self._build_prompt(request, context),",
        "user_prompt=build_prediction_user_prompt(request=request, context=context),",
    )
    text = text.replace("temperature=0.15,", "temperature=PREDICTION_PROMPT.temperature,")
    text = regex_replace_once(
        text,
        r'\n    def _build_prompt\([\s\S]*?\n    @staticmethod\n    def _snapshot_to_dynamics',
        "\n    @staticmethod\n    def _snapshot_to_dynamics",
        label="PredictionAgent._build_prompt",
    )
    path.write_text(text, encoding="utf-8")


def patch_rewrite(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = ensure_import(
        text,
        anchor="from app.llm.client import generate_structured\n",
        import_line="from app.prompts.report import REWRITE_PROMPT, build_rewrite_user_prompt",
        label="rewrite prompt import",
    )
    text = regex_replace_once(
        text,
        SYSTEM_BLOCK.format(name="REWRITE_SYSTEM_PROMPT"),
        "\n",
        label="REWRITE_SYSTEM_PROMPT",
    )
    text = text.replace("system_prompt=REWRITE_SYSTEM_PROMPT,", "system_prompt=REWRITE_PROMPT.system_prompt,")
    text = text.replace("user_prompt=self._build_prompt(", "user_prompt=build_rewrite_user_prompt(")
    text = text.replace("temperature=0.25,", "temperature=REWRITE_PROMPT.temperature,")
    text = regex_replace_once(
        text,
        r'\n    def _build_prompt\([\s\S]*?\n    @staticmethod\n    def _default_rewrite',
        "\n    @staticmethod\n    def _default_rewrite",
        label="RewriteAgent._build_prompt",
    )
    path.write_text(text, encoding="utf-8")


def patch_memory(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = ensure_import(
        text,
        anchor="from app.llm.client import generate_structured\n",
        import_line="from app.prompts.memory import MEMORY_EXTRACTOR_PROMPT, build_memory_extractor_user_prompt",
        label="memory prompt import",
    )
    text = regex_replace_once(
        text,
        SYSTEM_BLOCK.format(name="MEMORY_EXTRACTOR_SYSTEM_PROMPT"),
        "\n",
        label="MEMORY_EXTRACTOR_SYSTEM_PROMPT",
    )
    text = regex_replace_once(
        text,
        r'\ndef _build_extractor_prompt\(request: MemoryUpdateRequest\) -> str:[\s\S]*?\n# =========================================================\n# 3\. MemoryExtractor',
        "\n# =========================================================\n# 3. MemoryExtractor",
        label="_build_extractor_prompt",
    )
    text = text.replace(
        "system_prompt=MEMORY_EXTRACTOR_SYSTEM_PROMPT,",
        "system_prompt=MEMORY_EXTRACTOR_PROMPT.system_prompt,",
    )
    text = text.replace(
        "user_prompt=_build_extractor_prompt(request),",
        "user_prompt=build_memory_extractor_user_prompt(request),",
    )
    text = text.replace("temperature=0.2,", "temperature=MEMORY_EXTRACTOR_PROMPT.temperature,")
    path.write_text(text, encoding="utf-8")


def patch_state(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "from app.agents.prompts import STATE_SYSTEM_PROMPT, build_state_user_prompt",
        "from app.prompts.session import STATE_PROMPT, build_state_user_prompt",
    )
    text = text.replace("system_prompt=STATE_SYSTEM_PROMPT,", "system_prompt=STATE_PROMPT.system_prompt,")
    text = text.replace("user_prompt=self._build_prompt(payload),", "user_prompt=build_state_user_prompt(payload),")
    text = text.replace(
        "output_model=StateEvaluationResponse,\n        )",
        "output_model=StateEvaluationResponse,\n            temperature=STATE_PROMPT.temperature,\n        )",
    )
    text = regex_replace_once(
        text,
        r'\n    def _build_prompt\(self, payload: dict\) -> str:[\s\S]*?\n    # ------------------------------------------------------------------',
        "\n    # ------------------------------------------------------------------",
        label="StateAgent._build_prompt",
    )
    path.write_text(text, encoding="utf-8")


def patch_strategy(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = ensure_import(
        text,
        anchor="from app.llm.client import generate_structured\n",
        import_line="from app.prompts.strategy import STRATEGY_PROMPT",
        label="strategy prompt definition import",
    )
    text = text.replace("temperature=0.2,", "temperature=STRATEGY_PROMPT.temperature,")
    path.write_text(text, encoding="utf-8")


def patch_evaluation(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old_import = "from app.agents.prompts import EVALUATION_SYSTEM_PROMPT, build_evaluation_user_prompt"
    new_import = "from app.prompts.strategy import (\n    EVALUATION_PROMPT,\n    EVALUATION_PROMPT_VERSION,\n    EVALUATION_SYSTEM_PROMPT,\n    build_evaluation_user_prompt,\n)"
    if new_import not in text:
        text = replace_once(text, old_import, new_import, label="evaluation prompt import")
    text = re.sub(r'^EVALUATION_PROMPT_VERSION\s*=\s*"[^"]+"\s*\n', "", text, count=1, flags=re.MULTILINE)
    text = text.replace("temperature=0.1,", "temperature=EVALUATION_PROMPT.temperature,")
    path.write_text(text, encoding="utf-8")


def patch_sim_component(path: Path, *, prompt_symbol: str, temperature: str) -> None:
    text = path.read_text(encoding="utf-8")
    import_line = f"from app.prompts.simulation import {prompt_symbol}"
    text = ensure_import(
        text,
        anchor="from app.llm.client import generate_structured\n",
        import_line=import_line,
        label=f"{path.name} prompt definition import",
    )
    text = text.replace(
        f"temperature={temperature},",
        f"temperature={prompt_symbol}.temperature,",
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Move active Social Lab prompt ownership to app.prompts and centralize prompt metadata"
    )
    parser.add_argument("backend", type=Path, help="Path to social-lab/backend")
    args = parser.parse_args()

    backend = args.backend.resolve()
    agents = backend / "app" / "agents"
    simulation = agents / "simulation"

    paths = {
        "persona": agents / "persona_agent.py",
        "safety": agents / "safety_agent.py",
        "simulation_v1": agents / "simulation_agent.py",
        "analysis": agents / "analysis_agent.py",
        "prediction": agents / "prediction_agent.py",
        "rewrite": agents / "rewrite_agent.py",
        "memory": agents / "memory_agent.py",
        "state": agents / "state_agent.py",
        "strategy": agents / "strategy_agent.py",
        "evaluation": agents / "evaluation_agent.py",
        "turn_state": simulation / "turn_state_analyzer.py",
        "simulation_decision": simulation / "simulation_decision_engine.py",
        "turn_decision": simulation / "decision_engine.py",
        "response_generator": simulation / "response_generator.py",
        "consistency": simulation / "consistency_evaluator.py",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise SystemExit("Missing expected files:\n" + "\n".join(missing))

    patch_persona(paths["persona"])
    patch_safety(paths["safety"])
    patch_simulation_v1(paths["simulation_v1"])
    patch_analysis(paths["analysis"])
    patch_prediction(paths["prediction"])
    patch_rewrite(paths["rewrite"])
    patch_memory(paths["memory"])
    patch_state(paths["state"])
    patch_strategy(paths["strategy"])
    patch_evaluation(paths["evaluation"])

    patch_sim_component(paths["turn_state"], prompt_symbol="TURN_STATE_PROMPT", temperature="0.2")
    patch_sim_component(paths["simulation_decision"], prompt_symbol="SIMULATION_DECISION_PROMPT", temperature="0.3")
    patch_sim_component(paths["turn_decision"], prompt_symbol="TURN_DECISION_PROMPT", temperature="0.25")
    patch_sim_component(paths["response_generator"], prompt_symbol="RESPONSE_GENERATION_PROMPT", temperature="0.55")
    patch_sim_component(paths["consistency"], prompt_symbol="CONSISTENCY_PROMPT", temperature="0.1")

    print("Prompt migration applied successfully.")
    print("Run: python -m compileall app tests")
    print("Then: pytest -q tests/test_prompt_registry.py")
    print("Inventory: python ../tools/prompt_inventory.py  # from backend, adjust path if needed")


if __name__ == "__main__":
    main()
