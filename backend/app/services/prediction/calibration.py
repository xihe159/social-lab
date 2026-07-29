from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


CALIBRATION_VERSION = "social-lab-prediction-v2.0-rules-2026-07"

SCENARIO_PRIORS: dict[str, float] = {
    "advisor": 45.0,
    "work": 48.0,
    "social": 50.0,
}

DYNAMIC_WEIGHTS: dict[str, float] = {
    "atmosphere_score": 0.12,
    "pace_score": 0.08,
    "pressure_level": -0.16,
    "clarity_score": 0.10,
    "responsiveness_score": 0.12,
    "progress_score": 0.22,
    "repairability_score": 0.08,
    "boundary_score": 0.12,
}

RELATIONSHIP_WEIGHTS: dict[str, float] = {
    "trust": 0.05,
    "respect": 0.03,
    "familiarity": 0.02,
    "affinity": 0.03,
    "emotional": 0.04,
}

TREND_WEIGHTS: dict[str, float] = {
    "atmosphere_score": 0.08,
    "pace_score": 0.05,
    "pressure_level": -0.10,
    "clarity_score": 0.05,
    "responsiveness_score": 0.06,
    "progress_score": 0.12,
    "repairability_score": 0.05,
    "boundary_score": 0.06,
}

AUTHORITY_WEIGHTS: dict[str, float] = {
    "advisor": -0.03,
    "work": -0.02,
    "social": -0.01,
}

METRIC_LABELS: dict[str, str] = {
    "atmosphere_score": "对话氛围",
    "pace_score": "节奏健康度",
    "pressure_level": "沟通压力",
    "clarity_score": "表达清晰度",
    "responsiveness_score": "回应对方顾虑",
    "progress_score": "目标推进度",
    "repairability_score": "后续可修复性",
    "boundary_score": "边界健康度",
    "trust": "关系信任",
    "respect": "相互尊重",
    "familiarity": "关系熟悉度",
    "affinity": "关系亲近度",
    "emotional": "情绪稳定度",
}

SCENARIO_LABELS: dict[str, str] = {
    "advisor": "导师场景先验",
    "work": "职场场景先验",
    "social": "社交场景先验",
}


@dataclass(frozen=True, slots=True)
class PredictionCalibration:
    """预测规则的可替换校准参数。"""

    version: str = CALIBRATION_VERSION
    scenario_priors: Mapping[str, float] = field(
        default_factory=lambda: dict(SCENARIO_PRIORS)
    )
    dynamic_weights: Mapping[str, float] = field(
        default_factory=lambda: dict(DYNAMIC_WEIGHTS)
    )
    relationship_weights: Mapping[str, float] = field(
        default_factory=lambda: dict(RELATIONSHIP_WEIGHTS)
    )
    trend_weights: Mapping[str, float] = field(
        default_factory=lambda: dict(TREND_WEIGHTS)
    )
    authority_weights: Mapping[str, float] = field(
        default_factory=lambda: dict(AUTHORITY_WEIGHTS)
    )
    metric_labels: Mapping[str, str] = field(
        default_factory=lambda: dict(METRIC_LABELS)
    )
    scenario_labels: Mapping[str, str] = field(
        default_factory=lambda: dict(SCENARIO_LABELS)
    )

    dynamics_score_limit: float = 24.0
    relationship_score_limit: float = 12.0
    trend_score_limit: float = 8.0
    semantic_adjustment_limit: int = 8
    max_influence_factors: int = 5


DEFAULT_CALIBRATION = PredictionCalibration()
