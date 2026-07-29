from __future__ import annotations

from dataclasses import dataclass

from app.schemas.prediction import OutcomeState, PredictionContext
from app.services.prediction.utils import clamp_float, contains_any


@dataclass(frozen=True, slots=True)
class GuardrailResult:
    score: float
    reason: str | None


class PredictionGuardrails:
    """处理明确拒绝、接受、高压、低边界等确定性上下限。"""

    def apply(
        self,
        *,
        score: float,
        context: PredictionContext,
        outcome_state: OutcomeState,
    ) -> GuardrailResult:
        original = score
        reasons: list[str] = []
        dynamics = context.current_dynamics

        if context.user_turn_count == 0:
            score = min(score, 45.0)
            reasons.append("没有有效用户表达")
        if context.target_turn_count == 0:
            score = min(score, 58.0)
            reasons.append("没有目标人物回应")

        explicit_stop = contains_any(
            context.last_target_message,
            ["不要再", "别再", "不想继续", "到此为止", "停止联系", "end this"],
        )
        if explicit_stop or (
            dynamics is not None and dynamics.atmosphere_label == "blocked"
        ):
            score = min(score, 20.0)
            reasons.append("目标人物已表现出终止沟通或阻断信号")
        elif outcome_state == "refuse":
            score = min(score, 35.0)
            reasons.append("目标人物已明确拒绝")
        elif outcome_state == "no_response":
            score = min(score, 40.0)
            reasons.append("当前结果为不回应或冷处理")
        elif outcome_state == "conditional_accept":
            score = clamp_float(score, 52.0, 78.0)
            reasons.append("目标人物只表现出条件性接受")
        elif outcome_state == "accept":
            concrete_action = contains_any(
                context.last_target_message,
                ["时间", "明天", "今天", "周", "发我", "提交", "安排", "就这样", "确认"],
            )
            floor = 72.0 if concrete_action else 62.0
            score = max(score, floor)
            reasons.append("目标人物已给出接受信号")

        if dynamics is not None:
            if dynamics.pressure_level >= 80:
                score = min(score, 40.0)
                reasons.append("当前沟通压力过高")
            elif dynamics.pressure_level >= 70:
                score = min(score, 48.0)
                reasons.append("当前沟通压力明显偏高")

            if dynamics.boundary_score <= 25:
                score = min(score, 35.0)
                reasons.append("边界健康度过低")

            if (
                dynamics.progress_score >= 80
                and dynamics.atmosphere_score >= 65
                and outcome_state not in {"refuse", "no_response"}
            ):
                score = max(score, 68.0)
                reasons.append("目标推进与对话氛围均处于高位")

        score = clamp_float(score, 0.0, 100.0)
        reason = "；".join(dict.fromkeys(reasons)) if reasons else None
        if abs(score - original) < 0.5:
            reason = None
        return GuardrailResult(score=score, reason=reason)
