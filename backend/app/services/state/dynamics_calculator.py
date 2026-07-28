from __future__ import annotations

from app.schemas.dynamics import (
    ConversationDynamics,
    ConversationDynamicsDelta,
)
from app.schemas.state import StateEvaluateRequest
from app.services.state.constants import (
    ATMOSPHERE_REFUSAL_WORDS,
    DYNAMIC_FIELDS,
    DYNAMIC_FIELD_NAMES,
    EXPLICIT_STOP_WORDS,
)
from app.services.state.utils import (
    clean_text,
    clamp,
    contains_any,
    number,
    truncate,
)


class DynamicsCalculator:
    """负责动态基线、最终指标、标签和控制建议的确定性计算。"""

    def build_initial(
        self,
        request: StateEvaluateRequest,
    ) -> ConversationDynamics:
        state = request.current_state.model_dump()
        trust = number(state.get("trust"), 50)
        respect = number(state.get("respect"), 50)
        affinity = number(state.get("affinity"), 50)
        emotional_raw = number(state.get("emotional"), 0)
        emotional_0_100 = clamp(
            round((emotional_raw + 100) / 2),
            0,
            100,
        )

        atmosphere = clamp(
            round(
                0.30 * trust
                + 0.25 * respect
                + 0.20 * affinity
                + 0.25 * emotional_0_100
            ),
            25,
            75,
        )
        repairability = clamp(
            round(
                0.35 * trust
                + 0.35 * respect
                + 0.30 * emotional_0_100
            ),
            30,
            80,
        )
        pressure = 30 if request.scenario in {"advisor", "work"} else 25

        values = {
            "atmosphere_score": atmosphere,
            "pace_score": 55,
            "pressure_level": pressure,
            "clarity_score": 50,
            "responsiveness_score": 50,
            "progress_score": 35,
            "repairability_score": repairability,
            "boundary_score": 60,
        }

        rhythm_label = self.derive_rhythm_label(values)
        atmosphere_label = self.derive_atmosphere_label(
            values=values,
            target_reply="",
        )

        return ConversationDynamics(
            **values,
            rhythm_label=rhythm_label,
            atmosphere_label=atmosphere_label,
            recommended_next_move="clarify",
            dynamics_reason=(
                "首次评估使用关系状态生成保守基线，"
                "后续将根据每轮对话逐步更新。"
            ),
        )

    def rebuild(
        self,
        *,
        baseline: ConversationDynamics,
        delta: ConversationDynamicsDelta,
        request: StateEvaluateRequest,
        model_reason: str,
    ) -> ConversationDynamics:
        values: dict[str, int] = {}
        for field_name in DYNAMIC_FIELDS:
            values[field_name] = clamp(
                getattr(baseline, field_name)
                + getattr(delta, field_name),
                0,
                100,
            )

        rhythm_label = self.derive_rhythm_label(values)
        atmosphere_label = self.derive_atmosphere_label(
            values=values,
            target_reply=request.target_reply,
        )
        recommended_next_move = self.derive_next_move(
            values=values,
            rhythm_label=rhythm_label,
            atmosphere_label=atmosphere_label,
        )
        reason = self.build_reason(
            values=values,
            delta=delta,
            model_reason=model_reason,
        )

        return ConversationDynamics(
            **values,
            rhythm_label=rhythm_label,
            atmosphere_label=atmosphere_label,
            recommended_next_move=recommended_next_move,
            dynamics_reason=reason,
        )

    def derive_rhythm_label(
        self,
        values: dict[str, int],
    ) -> str:
        pressure = values["pressure_level"]
        pace = values["pace_score"]
        progress = values["progress_score"]

        if pressure >= 75:
            return "too_fast"
        if pressure >= 58:
            return "slightly_fast"
        if pace <= 32 and progress <= 30:
            return "stalled"
        if pace < 48:
            return "slightly_slow"
        return "balanced"

    def derive_atmosphere_label(
        self,
        *,
        values: dict[str, int],
        target_reply: str,
    ) -> str:
        atmosphere = values["atmosphere_score"]
        pressure = values["pressure_level"]
        target_lower = target_reply.lower()

        explicit_stop = contains_any(
            target_lower,
            EXPLICIT_STOP_WORDS,
        )
        explicit_refusal = contains_any(
            target_lower,
            ATMOSPHERE_REFUSAL_WORDS,
        )

        if explicit_stop or atmosphere < 20:
            return "blocked"
        if explicit_refusal or atmosphere < 35 or pressure >= 78:
            return "defensive"
        if atmosphere < 50 or pressure >= 62:
            return "tense"
        if (
            atmosphere >= 76
            and pressure <= 35
            and values["progress_score"] >= 55
        ):
            return "warm"
        if atmosphere >= 64 and pressure <= 48:
            return "safe"
        return "neutral"

    def derive_next_move(
        self,
        *,
        values: dict[str, int],
        rhythm_label: str,
        atmosphere_label: str,
    ) -> str:
        if atmosphere_label == "blocked":
            return "pause"
        if values["boundary_score"] < 38:
            return "set_boundary"
        if (
            atmosphere_label in {"defensive", "tense"}
            or values["repairability_score"] < 45
        ):
            return "repair"
        if (
            rhythm_label in {"too_fast", "slightly_fast"}
            or values["pressure_level"] > 58
        ):
            return "slow_down"
        if (
            values["clarity_score"] < 52
            or values["responsiveness_score"] < 48
        ):
            return "clarify"
        if values["progress_score"] < 85:
            return "advance"
        return "clarify"

    def build_control_suggestions(
        self,
        dynamics: ConversationDynamics,
    ) -> list[str]:
        mapping = {
            "advance": [
                "保持当前低压力节奏，只推进一个明确的小步骤。",
                "继续回应对方已表达的条件，不要同时增加多个请求。",
            ],
            "clarify": [
                "补齐一个最关键的背景、时间点或责任安排。",
                "先回应目标人物当前最明确的顾虑，再继续推进目标。",
            ],
            "slow_down": [
                "减少催促和连续追问，为对方保留考虑时间。",
                "本轮不要要求立即承诺，只确认是否愿意继续讨论。",
            ],
            "repair": [
                "先承认对方的不适或顾虑，再说明事实和补救方向。",
                "避免立即辩解或重复原请求。",
            ],
            "set_boundary": [
                "明确双方可接受和不可接受的范围。",
                "保留拒绝与暂停空间，避免用关系或情绪施压。",
            ],
            "pause": [
                "停止继续推进当前请求，等待新的明确沟通信号。",
                "不要重复联系或用更强语气迫使对方回应。",
            ],
        }
        return mapping[dynamics.recommended_next_move][:3]

    def build_reason(
        self,
        *,
        values: dict[str, int],
        delta: ConversationDynamicsDelta,
        model_reason: str,
    ) -> str:
        del values  # 保留参数以便后续把最终值加入解释。

        changes = sorted(
            (
                (field_name, getattr(delta, field_name))
                for field_name in DYNAMIC_FIELDS
                if getattr(delta, field_name) != 0
            ),
            key=lambda item: abs(item[1]),
            reverse=True,
        )[:3]

        change_text = "、".join(
            (
                f"{DYNAMIC_FIELD_NAMES[field]}"
                f"{'上升' if value > 0 else '下降'}"
                f"{abs(value)}"
            )
            for field, value in changes
        )

        summary = (
            f"本轮主要变化为：{change_text}。"
            if change_text
            else "本轮各项动态指标整体保持稳定。"
        )

        cleaned_model_reason = truncate(
            clean_text(model_reason, default=""),
            max_length=220,
        )
        if cleaned_model_reason:
            summary = f"{summary}{cleaned_model_reason}"

        return truncate(summary, max_length=360)
