"""
兼容旧导入路径。

旧代码：
    from app.services.prediction_calculator import PredictionCalculator

新代码也可以使用：
    from app.services.prediction import PredictionCalculator
"""

from app.services.prediction import (
    CALIBRATION_VERSION,
    DYNAMIC_WEIGHTS,
    METRIC_LABELS,
    RELATIONSHIP_WEIGHTS,
    SCENARIO_PRIORS,
    TREND_WEIGHTS,
    PredictionCalculator,
    PredictionCalibration,
)

__all__ = [
    "CALIBRATION_VERSION",
    "DYNAMIC_WEIGHTS",
    "METRIC_LABELS",
    "RELATIONSHIP_WEIGHTS",
    "SCENARIO_PRIORS",
    "TREND_WEIGHTS",
    "PredictionCalculator",
    "PredictionCalibration",
]
