from __future__ import annotations

from typing import Iterable

from app.agents.prompts import STATE_SYSTEM_PROMPT, build_state_user_prompt
from app.llm.client import generate_structured
from app.schemas.dynamics import (
    ConversationDynamics,
    ConversationDynamicsDelta,
)
from app.schemas.session import StateDelta
from app.schemas.state import StateEvaluateRequest, StateEvaluationResponse


_DYNAMIC_FIELDS = (
    "atmosphere_score",
    "pace_score",
    "pressure_level",
    "clarity_score",
    "responsiveness_score",
    "progress_score",
    "repairability_score",
    "boundary_score",
)


class StateAgent:
    """
    评估单轮沟通对关系状态和对话动态的影响。

    设计原则：
    1. LLM 负责语义判断和初始 delta；
    2. 规则层负责明显信号护栏；
    3. updated_dynamics 始终由 current_dynamics + dynamics_delta 重建；
    4. 标签和 recommended_next_move 由确定性逻辑生成，避免字段互相矛盾。
    """

    async def run(self, request: StateEvaluateRequest) -> StateEvaluationResponse:
        payload = request.model_dump()

        baseline = request.current_dynamics or self._build_initial_dynamics(request)
        payload["current_dynamics"] = baseline.model_dump()

        result = await generate_structured(
            system_prompt=STATE_SYSTEM_PROMPT,
            user_prompt=self._build_prompt(payload),
            output_model=StateEvaluationResponse,
        )
        return self.post_process(result=result, request=request)

    def post_process(
        self,
        *,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
    ) -> StateEvaluationResponse:
        baseline = request.current_dynamics or self._build_initial_dynamics(request)

        self._normalize_state_delta(result.state_delta)
        self._normalize_dynamic_delta(result.dynamics_update.dynamics_delta)
        self._normalize_text_fields(result)
        self._normalize_lists(result)

        self._apply_relationship_guardrails(result, request)
        self._apply_dynamics_guardrails(result, request)

        self._normalize_state_delta(result.state_delta)
        self._normalize_dynamic_delta(result.dynamics_update.dynamics_delta)

        updated = self._rebuild_updated_dynamics(
            baseline=baseline,
            delta=result.dynamics_update.dynamics_delta,
            request=request,
            model_reason=result.dynamics_update.updated_dynamics.dynamics_reason,
        )
        result.dynamics_update.updated_dynamics = updated
        result.dynamics_update.control_suggestions = self._build_control_suggestions(updated)

        self._normalize_lists(result)
        return result

    def _build_prompt(self, payload: dict) -> str:
        base_prompt = build_state_user_prompt(payload)
        return f"""
{base_prompt}

【对话动态指标补充要求】
你还必须输出 dynamics_update，且严格符合 ConversationDynamicsUpdate。

current_dynamics 是本轮之前的动态状态。
dynamics_delta 是本轮变化量，不是最终值。
updated_dynamics 应与 current_dynamics + dynamics_delta 基本一致。

八项指标定义：
- atmosphere_score：安全、开放、可继续沟通的程度；越高越好。
- pace_score：节奏健康度；过快和停滞都会降低。
- pressure_level：对方被催促、被迫表态的压力；越高风险越大。
- clarity_score：用户表达的背景、请求、时间和方案是否清晰。
- responsiveness_score：用户是否真正回应了目标人物上一轮顾虑。
- progress_score：本轮是否更接近沟通目标。
- repairability_score：发生分歧后是否仍有修复和继续沟通空间。
- boundary_score：是否尊重双方边界、选择权和拒绝权。

变化要求：
- 普通一轮通常在 -3 到 +3；
- 明确接受、明确拒绝、明显施压、真诚道歉并提出补救方案时才可更大；
- pressure_level 为风险指标，上升通常是负面；
- pace_score 表示节奏是否合适，不表示推进速度；
- 不要因为礼貌词就大幅增加分数；
- 目标人物明确拒绝时，progress_score 不应上升；
- 用户明确给予退出空间时，boundary_score 不应下降；
- 用户命令、催促或威胁时，pressure_level 不应下降。

control_suggestions 只输出 1 到 3 条简短的内部控制提示，
不要写完整改写话术，不要代替 AnalysisAgent 或 RewriteAgent。
""".strip()

    def _normalize_state_delta(self, delta: StateDelta) -> None:
        delta.trust = self._clamp(delta.trust, -6, 6)
        delta.respect = self._clamp(delta.respect, -6, 6)
        delta.familiarity = self._clamp(delta.familiarity, -4, 4)
        delta.affinity = self._clamp(delta.affinity, -5, 5)
        delta.authority = self._clamp(delta.authority, -2, 2)
        delta.emotional = self._clamp(delta.emotional, -6, 6)

    def _normalize_dynamic_delta(self, delta: ConversationDynamicsDelta) -> None:
        for field_name in _DYNAMIC_FIELDS:
            value = getattr(delta, field_name)
            limit = 12 if field_name == "pressure_level" else 10
            setattr(delta, field_name, self._clamp(value, -limit, limit))

    def _normalize_text_fields(self, result: StateEvaluationResponse) -> None:
        result.state_reason = self._truncate(
            self._clean_text(
                result.state_reason,
                default="本轮表达对关系状态产生了有限影响。",
            ),
            max_length=300,
        )

        dynamics = result.dynamics_update.updated_dynamics
        dynamics.dynamics_reason = self._truncate(
            self._clean_text(
                dynamics.dynamics_reason,
                default="本轮动态变化主要由表达清晰度、压力感和目标人物回应共同决定。",
            ),
            max_length=360,
        )

    def _normalize_lists(self, result: StateEvaluationResponse) -> None:
        result.positive_signals = self._clean_list(result.positive_signals, max_items=5)
        result.negative_signals = self._clean_list(result.negative_signals, max_items=5)
        result.risk_flags = self._clean_list(result.risk_flags, max_items=6)
        result.dynamics_update.control_suggestions = self._clean_list(
            result.dynamics_update.control_suggestions,
            max_items=3,
        )

    def _apply_relationship_guardrails(
        self,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
    ) -> None:
        text = request.user_message.strip()
        lowered = text.lower()
        delta = result.state_delta

        polite = self._contains_any(
            lowered,
            ["请", "谢谢", "麻烦", "辛苦", "您好", "抱歉", "不好意思", "please", "thanks"],
        )
        concrete = self._contains_any(
            lowered,
            ["计划", "安排", "时间", "日期", "明天", "今天", "步骤", "方案", "补救", "提交", "deadline"],
        )
        pressure = self._contains_any(
            lowered,
            ["必须", "立刻", "马上", "赶紧", "你应该", "不然", "否则", "必须帮", "asap", "immediately"],
        )
        vague = self._contains_any(
            lowered,
            ["随便", "反正", "不知道", "你看着办", "没办法", "再说吧"],
        ) or len(text) < 8
        responsible = self._contains_any(
            lowered,
            ["我会", "我已经", "我负责", "我承担", "我来处理", "我会补充", "i will", "i have"],
        )

        if polite:
            delta.respect = max(delta.respect, 0)
            self._append_unique(result.positive_signals, "表达中包含礼貌或尊重性措辞")

        if concrete:
            delta.trust = max(delta.trust, 1)
            if request.scenario in {"advisor", "work"}:
                delta.respect = max(delta.respect, 1)
            self._append_unique(result.positive_signals, "提供了较具体的计划、时间或处理方案")

        if responsible and request.scenario in {"advisor", "work"}:
            delta.trust = max(delta.trust, 1)
            delta.respect = max(delta.respect, 1)
            self._append_unique(result.positive_signals, "表达中体现了责任承担或主动推进")

        if pressure:
            delta.trust = min(delta.trust, -1)
            delta.respect = min(delta.respect, -1)
            delta.affinity = min(delta.affinity, -1)
            delta.emotional = min(delta.emotional, -1)
            self._append_unique(result.negative_signals, "表达可能让对方感到被催促或被迫表态")
            self._append_unique(result.risk_flags, "表达中存在催促、施压或命令感")

        if vague:
            delta.trust = min(delta.trust, 0)
            delta.emotional = min(delta.emotional, 0)
            self._append_unique(result.negative_signals, "关键信息不足，可能增加对方判断成本")
            self._append_unique(result.risk_flags, "表达信息不足或请求不够具体")

        delta.authority = self._clamp(delta.authority, -2, 2)

    def _apply_dynamics_guardrails(
        self,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
    ) -> None:
        user_text = request.user_message.strip()
        target_text = request.target_reply.strip()
        user_lower = user_text.lower()
        target_lower = target_text.lower()
        delta = result.dynamics_update.dynamics_delta

        polite = self._contains_any(
            user_lower,
            ["请", "谢谢", "麻烦", "抱歉", "不好意思", "please", "thanks"],
        )
        concrete = self._contains_any(
            user_lower,
            ["计划", "安排", "时间", "日期", "明天", "今天", "步骤", "方案", "补救", "提交", "deadline"],
        )
        pressure = self._contains_any(
            user_lower,
            ["必须", "立刻", "马上", "赶紧", "你应该", "不然", "否则", "必须帮", "asap", "immediately"],
        )
        vague = self._contains_any(
            user_lower,
            ["随便", "反正", "不知道", "你看着办", "没办法", "再说吧"],
        ) or len(user_text) < 8
        responsibility = self._contains_any(
            user_lower,
            ["我会", "我已经", "我负责", "我承担", "我来处理", "我会补充", "i will", "i have"],
        )
        apology = self._contains_any(
            user_lower,
            ["抱歉", "对不起", "不好意思", "是我的问题", "我错了", "sorry"],
        )
        gives_space = self._contains_any(
            user_lower,
            [
                "不方便也没关系",
                "你可以拒绝",
                "不用马上",
                "不用现在回答",
                "你先考虑",
                "有空再",
                "如果不合适",
                "不合适也没关系",
                "不方便也可以",
                "no pressure",
                "take your time",
            ],
        )

        explicit_acceptance = self._contains_any(
            target_lower,
            ["可以", "好", "行", "没问题", "同意", "愿意", "那就这样", "我答应"],
        )
        conditional_acceptance = self._contains_any(
            target_lower,
            ["如果", "先把", "先发", "再看", "可以考虑", "看情况", "不保证"],
        )
        explicit_refusal = self._contains_any(
            target_lower,
            ["不行", "不能", "不接受", "不愿意", "不想", "拒绝", "算了", "不要再", "别再"],
        )
        defensive_reply = self._contains_any(
            target_lower,
            ["有压力", "别逼", "凭什么", "你总是", "我不舒服", "让我很不舒服", "防备"],
        )
        asks_for_detail = "?" in target_text or "？" in target_text or self._contains_any(
            target_lower,
            ["具体", "怎么", "什么时候", "哪些", "为什么"],
        )

        if polite:
            delta.atmosphere_score = max(delta.atmosphere_score, 0)
            delta.boundary_score = max(delta.boundary_score, 0)

        if concrete:
            delta.clarity_score = max(delta.clarity_score, 3)
            delta.pace_score = max(delta.pace_score, 1)
            delta.progress_score = max(delta.progress_score, 1)

        if responsibility:
            delta.responsiveness_score = max(delta.responsiveness_score, 2)
            delta.repairability_score = max(delta.repairability_score, 1)
            delta.progress_score = max(delta.progress_score, 1)

        if apology:
            delta.repairability_score = max(delta.repairability_score, 2)
            delta.atmosphere_score = max(delta.atmosphere_score, 1)

        if gives_space:
            delta.boundary_score = max(delta.boundary_score, 3)
            delta.pressure_level = min(delta.pressure_level, -3)
            delta.atmosphere_score = max(delta.atmosphere_score, 2)
            self._append_unique(result.positive_signals, "表达为对方保留了考虑、拒绝或延后回应的空间")

        if pressure:
            delta.pressure_level = max(delta.pressure_level, 6)
            delta.atmosphere_score = min(delta.atmosphere_score, -3)
            delta.boundary_score = min(delta.boundary_score, -4)
            delta.pace_score = min(delta.pace_score, -3)
            delta.repairability_score = min(delta.repairability_score, -1)

        if vague:
            delta.clarity_score = min(delta.clarity_score, -3)
            delta.pace_score = min(delta.pace_score, -2)
            delta.progress_score = min(delta.progress_score, 0)

        if asks_for_detail and not concrete:
            delta.clarity_score = min(delta.clarity_score, -2)
            delta.responsiveness_score = min(delta.responsiveness_score, 0)
            delta.progress_score = min(delta.progress_score, 0)

        if conditional_acceptance:
            delta.progress_score = max(delta.progress_score, 1)
            delta.atmosphere_score = max(delta.atmosphere_score, 0)

        if explicit_acceptance and not explicit_refusal:
            delta.progress_score = max(delta.progress_score, 4)
            delta.atmosphere_score = max(delta.atmosphere_score, 2)
            delta.pressure_level = min(delta.pressure_level, 0)

        if defensive_reply:
            delta.atmosphere_score = min(delta.atmosphere_score, -3)
            delta.pressure_level = max(delta.pressure_level, 4)
            delta.boundary_score = min(delta.boundary_score, -2)
            delta.progress_score = min(delta.progress_score, -1)
            self._append_unique(result.risk_flags, "目标人物已表现出压力或防御")

        if explicit_refusal:
            delta.progress_score = min(delta.progress_score, -5)
            delta.atmosphere_score = min(delta.atmosphere_score, -4)
            delta.pressure_level = max(delta.pressure_level, 4)
            delta.repairability_score = min(delta.repairability_score, -2)
            self._append_unique(result.risk_flags, "目标人物已出现明确拒绝或停止推进信号")

    def _rebuild_updated_dynamics(
        self,
        *,
        baseline: ConversationDynamics,
        delta: ConversationDynamicsDelta,
        request: StateEvaluateRequest,
        model_reason: str,
    ) -> ConversationDynamics:
        values: dict[str, int] = {}
        for field_name in _DYNAMIC_FIELDS:
            values[field_name] = self._clamp(
                getattr(baseline, field_name) + getattr(delta, field_name),
                0,
                100,
            )

        rhythm_label = self._derive_rhythm_label(values)
        atmosphere_label = self._derive_atmosphere_label(
            values=values,
            target_reply=request.target_reply,
        )
        recommended_next_move = self._derive_next_move(
            values=values,
            rhythm_label=rhythm_label,
            atmosphere_label=atmosphere_label,
        )

        reason = self._build_dynamics_reason(
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

    def _build_initial_dynamics(
        self,
        request: StateEvaluateRequest,
    ) -> ConversationDynamics:
        state = request.current_state.model_dump()
        trust = self._number(state.get("trust"), 50)
        respect = self._number(state.get("respect"), 50)
        affinity = self._number(state.get("affinity"), 50)
        emotional_raw = self._number(state.get("emotional"), 0)
        emotional_0_100 = self._clamp(round((emotional_raw + 100) / 2), 0, 100)

        atmosphere = self._clamp(
            round(
                0.30 * trust
                + 0.25 * respect
                + 0.20 * affinity
                + 0.25 * emotional_0_100
            ),
            25,
            75,
        )
        repairability = self._clamp(
            round(0.35 * trust + 0.35 * respect + 0.30 * emotional_0_100),
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
        rhythm = self._derive_rhythm_label(values)
        atmosphere_label = self._derive_atmosphere_label(
            values=values,
            target_reply="",
        )

        return ConversationDynamics(
            **values,
            rhythm_label=rhythm,
            atmosphere_label=atmosphere_label,
            recommended_next_move="clarify",
            dynamics_reason="首次评估使用关系状态生成保守基线，后续将根据每轮对话逐步更新。",
        )

    def _derive_rhythm_label(self, values: dict[str, int]) -> str:
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

    def _derive_atmosphere_label(
        self,
        *,
        values: dict[str, int],
        target_reply: str,
    ) -> str:
        atmosphere = values["atmosphere_score"]
        pressure = values["pressure_level"]
        target_lower = target_reply.lower()

        explicit_stop = self._contains_any(
            target_lower,
            ["不要再", "别再", "不想继续", "到此为止", "停止联系"],
        )
        explicit_refusal = self._contains_any(
            target_lower,
            ["不行", "不能", "不接受", "不愿意", "不想", "拒绝", "算了"],
        )

        if explicit_stop or atmosphere < 20:
            return "blocked"
        if explicit_refusal or atmosphere < 35 or pressure >= 78:
            return "defensive"
        if atmosphere < 50 or pressure >= 62:
            return "tense"
        if atmosphere >= 76 and pressure <= 35 and values["progress_score"] >= 55:
            return "warm"
        if atmosphere >= 64 and pressure <= 48:
            return "safe"
        return "neutral"

    def _derive_next_move(
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
        if atmosphere_label in {"defensive", "tense"} or values["repairability_score"] < 45:
            return "repair"
        if rhythm_label in {"too_fast", "slightly_fast"} or values["pressure_level"] > 58:
            return "slow_down"
        if values["clarity_score"] < 52 or values["responsiveness_score"] < 48:
            return "clarify"
        if values["progress_score"] < 85:
            return "advance"
        return "clarify"

    def _build_control_suggestions(
        self,
        dynamics: ConversationDynamics,
    ) -> list[str]:
        move = dynamics.recommended_next_move
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
        return mapping[move][:3]

    def _build_dynamics_reason(
        self,
        *,
        values: dict[str, int],
        delta: ConversationDynamicsDelta,
        model_reason: str,
    ) -> str:
        changes = sorted(
            (
                (field_name, getattr(delta, field_name))
                for field_name in _DYNAMIC_FIELDS
                if getattr(delta, field_name) != 0
            ),
            key=lambda item: abs(item[1]),
            reverse=True,
        )[:3]

        names = {
            "atmosphere_score": "氛围",
            "pace_score": "节奏健康度",
            "pressure_level": "压力",
            "clarity_score": "清晰度",
            "responsiveness_score": "回应度",
            "progress_score": "推进度",
            "repairability_score": "可修复性",
            "boundary_score": "边界健康度",
        }

        change_text = "、".join(
            f"{names[field]}{'上升' if value > 0 else '下降'}{abs(value)}"
            for field, value in changes
        )
        summary = (
            f"本轮主要变化为：{change_text}。"
            if change_text
            else "本轮各项动态指标整体保持稳定。"
        )

        cleaned_model_reason = self._truncate(
            self._clean_text(model_reason, default=""),
            max_length=220,
        )
        if cleaned_model_reason:
            summary = f"{summary}{cleaned_model_reason}"

        return self._truncate(summary, max_length=360)

    @staticmethod
    def _number(value: object, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _clean_text(value: object, *, default: str) -> str:
        text = value.strip() if isinstance(value, str) else ""
        return text or default

    @staticmethod
    def _truncate(value: str, *, max_length: int) -> str:
        value = value.strip()
        if len(value) <= max_length:
            return value
        return value[: max_length - 1].rstrip() + "…"

    def _clean_list(self, values: Iterable[object], *, max_items: int) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            if not isinstance(value, str):
                continue
            item = self._truncate(value.strip(), max_length=120)
            if item and item not in cleaned:
                cleaned.append(item)
        return cleaned[:max_items]

    @staticmethod
    def _append_unique(values: list[str], item: str) -> None:
        if item not in values:
            values.append(item)

    @staticmethod
    def _contains_any(text: str, keywords: Iterable[str]) -> bool:
        normalized = text.lower()
        return any(keyword.lower() in normalized for keyword in keywords)

    @staticmethod
    def _clamp(value: int, low: int, high: int) -> int:
        return max(low, min(high, int(value)))
