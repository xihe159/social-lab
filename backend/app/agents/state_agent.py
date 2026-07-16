from __future__ import annotations

from typing import Any

from app.agents.prompts import STATE_SYSTEM_PROMPT, build_state_user_prompt
from app.llm.client import generate_structured
from app.schemas.dynamics import (
    ConversationDynamics,
    ConversationDynamicsDelta,
    ConversationDynamicsUpdate,
)
from app.schemas.session import StateDelta
from app.schemas.state import StateEvaluateRequest, StateEvaluationResponse


DYNAMICS_EVALUATION_INSTRUCTIONS = """
你还需要评估本轮对话对“对话氛围与节奏动态指标”的影响。

动态指标含义：
- atmosphere_score：当前对话氛围健康度。越高表示越安全、开放、可继续沟通。
- pace_score：当前节奏健康度。越高表示推进速度越合适。注意：它不是推进速度本身，过快和停滞都会降低该分数。
- pressure_level：当前压力水平。越高表示对方越可能感到被催促、被要求或被迫表态。
- clarity_score：用户表达清晰度。越高表示背景、请求、时间、方案越具体。
- responsiveness_score：用户回应目标人物顾虑的程度。越高表示越能接住对方反馈。
- progress_score：沟通目标推进度。越高表示本轮更接近用户目标。
- repairability_score：后续修复空间。越高表示仍然容易继续沟通或修复关系。
- boundary_score：边界健康度。越高表示表达既有边界又不过度施压。

输出要求：
1. dynamics_update.dynamics_delta 表示本轮变化，范围 -15 到 15；
2. dynamics_update.updated_dynamics 表示更新后的当前指标，范围 0 到 100；
3. 如果用户表达具体但带有催促感，clarity_score 可以上升，但 pressure_level 也应上升，pace_score 和 atmosphere_score 可能下降；
4. 如果用户给选择空间、承担责任、回应对方顾虑，atmosphere_score、responsiveness_score、repairability_score 可上升；
5. 如果用户表达模糊、逃避、重复解释但没有回应对方顾虑，clarity_score、responsiveness_score、progress_score 应下降；
6. pace_score 不是越高越快，而是“节奏是否健康”；推进过快和停滞都会降低 pace_score；
7. control_suggestions 必须给出下一轮如何控制氛围和节奏的建议。
""".strip()


class StateAgent:
    """
    StateAgent 负责评估单轮对话对关系状态、对话氛围和对话节奏的影响。

    职责边界：
    - SimulationAgent 负责“像目标人物一样回复”；
    - StateAgent 负责“判断这轮沟通让关系状态如何变化”；
    - StateAgent 同时评估“氛围是否安全、节奏是否合适、压力是否升高”；
    - Orchestrator 负责把结果合并为 SessionMessageResponse。
    """

    async def run(self, request: StateEvaluateRequest) -> StateEvaluationResponse:
        payload = request.model_dump()

        result = await generate_structured(
            system_prompt=STATE_SYSTEM_PROMPT,
            user_prompt=self._build_user_prompt(payload),
            output_model=StateEvaluationResponse,
        )

        return self.post_process(result=result, request=request)

    def post_process(
        self,
        *,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
    ) -> StateEvaluationResponse:
        """
        对 LLM 输出做业务级修正。

        Pydantic 负责结构合法性；这里负责业务合理性：
        - 单轮关系变化不要过大；
        - 空文本要兜底；
        - 风险和信号列表要去重、限长；
        - 根据明确表达特征做轻量规则校正；
        - 如果 StateEvaluationResponse 已接入 dynamics_update，则同步修正动态指标。
        """

        self._normalize_state_delta(result.state_delta)
        self._normalize_text_fields(result)
        self._normalize_lists(result)

        self._apply_rule_guardrails(result, request)
        self._normalize_state_delta(result.state_delta)

        if self._supports_dynamics_schema():
            self._ensure_dynamics_update(result, request)
            self._normalize_dynamics_delta(result.dynamics_update.dynamics_delta)
            self._apply_dynamics_rule_guardrails(result, request)
            self._normalize_dynamics_delta(result.dynamics_update.dynamics_delta)
            self._rebuild_updated_dynamics(result, request)
            self._normalize_dynamics_text_fields(result)
            self._normalize_dynamics_suggestions(result)

        self._normalize_lists(result)

        return result

    def _build_user_prompt(self, payload: dict[str, Any]) -> str:
        """
        在不强制修改 prompts.py 的前提下，为 StateAgent 追加 dynamics 评估说明。

        如果当前 StateEvaluationResponse 还没有 dynamics_update 字段，
        则保持旧提示词，避免模型输出 schema 不允许的字段。
        """

        base_prompt = build_state_user_prompt(payload)

        if not self._supports_dynamics_schema():
            return base_prompt

        return f"{base_prompt}\n\n{DYNAMICS_EVALUATION_INSTRUCTIONS}"

    def _supports_dynamics_schema(self) -> bool:
        return "dynamics_update" in getattr(
            StateEvaluationResponse,
            "model_fields",
            {},
        )

    def _ensure_dynamics_update(
        self,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
    ) -> None:
        """
        兼容兜底：
        如果 schema 已有 dynamics_update，但 LLM 输出为空或异常，
        用保守默认值补齐，避免后处理报错。
        """

        current_update = getattr(result, "dynamics_update", None)
        if isinstance(current_update, ConversationDynamicsUpdate):
            return

        base = self._default_dynamics(request)
        zero_delta = ConversationDynamicsDelta(
            atmosphere_score=0,
            pace_score=0,
            pressure_level=0,
            clarity_score=0,
            responsiveness_score=0,
            progress_score=0,
            repairability_score=0,
            boundary_score=0,
        )

        result.dynamics_update = ConversationDynamicsUpdate(
            dynamics_delta=zero_delta,
            updated_dynamics=base,
            control_suggestions=self._build_control_suggestions(base),
        )

    def _normalize_state_delta(self, delta: StateDelta) -> None:
        """
        单轮关系变化保持保守。
        这里限制在 -6 到 6，比 schema 的 -10 到 10 更稳。
        """

        delta.trust = self._clamp(delta.trust, -6, 6)
        delta.respect = self._clamp(delta.respect, -6, 6)
        delta.familiarity = self._clamp(delta.familiarity, -4, 4)
        delta.affinity = self._clamp(delta.affinity, -5, 5)
        delta.authority = self._clamp(delta.authority, -3, 3)
        delta.emotional = self._clamp(delta.emotional, -6, 6)

    def _normalize_text_fields(self, result: StateEvaluationResponse) -> None:
        result.state_reason = self._clean_text(
            result.state_reason,
            default="本轮表达对关系状态产生了轻微影响，主要取决于用户表达是否具体、尊重且降低了对方负担。",
        )
        result.state_reason = self._truncate(result.state_reason, max_length=300)

    def _normalize_lists(self, result: StateEvaluationResponse) -> None:
        result.positive_signals = self._clean_list(result.positive_signals, max_items=5)
        result.negative_signals = self._clean_list(result.negative_signals, max_items=5)
        result.risk_flags = self._clean_list(result.risk_flags, max_items=6)

    def _apply_rule_guardrails(
        self,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
    ) -> None:
        """
        用轻量规则修正明显偏差。

        这些规则不是替代 LLM 判断，而是防止 LLM 在非常明显的表达特征下给出不合理 delta。
        """

        text = request.user_message.strip()
        lowered = text.lower()
        delta = result.state_delta

        polite_keywords = [
            "请",
            "谢谢",
            "麻烦",
            "辛苦",
            "您好",
            "可以",
            "方便",
            "抱歉",
            "不好意思",
            "thanks",
            "please",
        ]
        concrete_keywords = [
            "计划",
            "安排",
            "时间",
            "周",
            "明天",
            "今天",
            "原因",
            "具体",
            "步骤",
            "方案",
            "补救",
            "提交",
            "deadline",
        ]
        pressure_keywords = [
            "必须",
            "立刻",
            "马上",
            "赶紧",
            "你应该",
            "凭什么",
            "不然",
            "否则",
            "必须帮",
            "asap",
            "immediately",
        ]
        vague_keywords = [
            "随便",
            "反正",
            "不知道",
            "你看着办",
            "没办法",
            "再说吧",
        ]

        has_polite = self._contains_any(lowered, polite_keywords)
        has_concrete = self._contains_any(lowered, concrete_keywords)
        has_pressure = self._contains_any(lowered, pressure_keywords)
        has_vague = self._contains_any(lowered, vague_keywords) or len(text) < 12

        if has_polite:
            delta.respect = max(delta.respect, 0)
            if "礼貌" not in "".join(result.positive_signals):
                result.positive_signals.append("表达中包含礼貌或尊重性措辞")

        if has_concrete:
            delta.trust = max(delta.trust, 1)
            if request.scenario in {"advisor", "work"}:
                delta.respect = max(delta.respect, 1)
            delta.emotional = max(delta.emotional, 1)
            if "具体" not in "".join(result.positive_signals):
                result.positive_signals.append("提供了较具体的原因、计划或时间安排")

        if has_pressure:
            delta.trust = min(delta.trust, -1)
            delta.respect = min(delta.respect, -1)
            delta.affinity = min(delta.affinity, -1)
            delta.emotional = min(delta.emotional, -1)
            if "压力" not in "".join(result.risk_flags):
                result.risk_flags.append("表达中存在催促、施压或命令感")
            if "施压" not in "".join(result.negative_signals):
                result.negative_signals.append("表达可能让对方感到被施压")

        if has_vague:
            delta.trust = min(delta.trust, 0)
            delta.emotional = min(delta.emotional, 0)
            if "模糊" not in "".join(result.risk_flags):
                result.risk_flags.append("表达信息不足或请求不够具体")
            if "信息不足" not in "".join(result.negative_signals):
                result.negative_signals.append("关键信息不足，可能增加对方判断成本")

        responsibility_keywords = [
            "我会",
            "我已经",
            "我负责",
            "我承担",
            "我会补充",
            "我会整理",
            "I will",
            "I have",
        ]
        if request.scenario in {"advisor", "work"} and self._contains_any(text, responsibility_keywords):
            delta.trust = max(delta.trust, 1)
            delta.respect = max(delta.respect, 1)
            if "责任" not in "".join(result.positive_signals):
                result.positive_signals.append("表达中体现了责任承担或主动推进")

        # authority 通常不应因为单轮普通表达大幅变化。
        delta.authority = self._clamp(delta.authority, -2, 2)

    def _normalize_dynamics_delta(self, delta: ConversationDynamicsDelta) -> None:
        """
        动态指标单轮变化保持保守。
        """

        delta.atmosphere_score = self._clamp(delta.atmosphere_score, -12, 12)
        delta.pace_score = self._clamp(delta.pace_score, -12, 12)
        delta.pressure_level = self._clamp(delta.pressure_level, -12, 12)
        delta.clarity_score = self._clamp(delta.clarity_score, -12, 12)
        delta.responsiveness_score = self._clamp(delta.responsiveness_score, -12, 12)
        delta.progress_score = self._clamp(delta.progress_score, -12, 12)
        delta.repairability_score = self._clamp(delta.repairability_score, -12, 12)
        delta.boundary_score = self._clamp(delta.boundary_score, -12, 12)

    def _apply_dynamics_rule_guardrails(
        self,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
    ) -> None:
        """
        用规则修正“氛围、压力、节奏”这些容易被模型误判的指标。

        重点：
        - 具体表达可以提高 clarity，但如果带有命令感，也应提高 pressure；
        - 给选择空间可以降低 pressure；
        - 负责和修复表达可以提高 repairability；
        - 节奏健康度 pace_score 不是越快越高。
        """

        text = request.user_message.strip()
        lowered = text.lower()
        target_reply = getattr(request, "target_reply", "") or ""
        target_lowered = target_reply.lower()

        update = result.dynamics_update
        delta = update.dynamics_delta

        polite_keywords = [
            "请",
            "谢谢",
            "麻烦",
            "辛苦",
            "您好",
            "可以",
            "方便",
            "抱歉",
            "不好意思",
            "thanks",
            "please",
        ]
        concrete_keywords = [
            "计划",
            "安排",
            "时间",
            "周",
            "明天",
            "今天",
            "原因",
            "具体",
            "步骤",
            "方案",
            "补救",
            "提交",
            "重点",
            "两个点",
            "deadline",
        ]
        pressure_keywords = [
            "必须",
            "立刻",
            "马上",
            "赶紧",
            "你应该",
            "凭什么",
            "不然",
            "否则",
            "必须帮",
            "asap",
            "immediately",
        ]
        vague_keywords = [
            "随便",
            "反正",
            "不知道",
            "你看着办",
            "没办法",
            "再说吧",
        ]
        choice_keywords = [
            "如果你方便",
            "如果方便",
            "可以的话",
            "你也可以",
            "不方便也没关系",
            "看你时间",
            "你觉得哪种合适",
            "可以直接告诉我",
            "先帮我看",
        ]
        repair_keywords = [
            "抱歉",
            "不好意思",
            "我理解",
            "我明白",
            "我会改",
            "我来负责",
            "我会补上",
            "谢谢你提醒",
        ]
        boundary_keywords = [
            "我只需要",
            "先看",
            "只看",
            "两个重点",
            "这两个点",
            "不用完整看",
            "不用马上",
            "如果不方便",
        ]

        target_resistance_keywords = [
            "没时间",
            "不一定",
            "不方便",
            "为什么",
            "凭什么",
            "压力",
            "算了",
            "不想",
            "别",
            "不太",
            "有点",
        ]
        target_acceptance_keywords = [
            "可以",
            "好",
            "没问题",
            "愿意",
            "行",
            "可以看",
            "我看看",
            "谢谢",
        ]

        has_polite = self._contains_any(lowered, polite_keywords)
        has_concrete = self._contains_any(lowered, concrete_keywords)
        has_pressure = self._contains_any(lowered, pressure_keywords)
        has_vague = self._contains_any(lowered, vague_keywords) or len(text) < 12
        has_choice = self._contains_any(lowered, choice_keywords)
        has_repair = self._contains_any(lowered, repair_keywords)
        has_boundary = self._contains_any(lowered, boundary_keywords)
        target_resistant = self._contains_any(target_lowered, target_resistance_keywords)
        target_accepting = self._contains_any(target_lowered, target_acceptance_keywords)

        if has_polite:
            delta.atmosphere_score = max(delta.atmosphere_score, 2)
            delta.boundary_score = max(delta.boundary_score, 1)

        if has_concrete:
            delta.clarity_score = max(delta.clarity_score, 4)
            delta.progress_score = max(delta.progress_score, 1)

        if has_choice:
            delta.pressure_level = min(delta.pressure_level, -4)
            delta.atmosphere_score = max(delta.atmosphere_score, 3)
            delta.responsiveness_score = max(delta.responsiveness_score, 2)
            delta.repairability_score = max(delta.repairability_score, 2)
            delta.boundary_score = max(delta.boundary_score, 3)

        if has_repair:
            delta.atmosphere_score = max(delta.atmosphere_score, 3)
            delta.repairability_score = max(delta.repairability_score, 4)
            delta.responsiveness_score = max(delta.responsiveness_score, 2)
            delta.pressure_level = min(delta.pressure_level, 0)

        if has_boundary:
            delta.boundary_score = max(delta.boundary_score, 3)
            delta.pressure_level = min(delta.pressure_level, 0)
            delta.pace_score = max(delta.pace_score, 1)

        if has_pressure:
            delta.pressure_level = max(delta.pressure_level, 7)
            delta.atmosphere_score = min(delta.atmosphere_score, -4)
            delta.pace_score = min(delta.pace_score, -4)
            delta.repairability_score = min(delta.repairability_score, -2)
            delta.boundary_score = min(delta.boundary_score, -3)
            delta.responsiveness_score = min(delta.responsiveness_score, -2)

            if "推进节奏过急" not in "".join(result.risk_flags):
                result.risk_flags.append("推进节奏过急，可能让对方产生压力或防御")

        if has_vague:
            delta.clarity_score = min(delta.clarity_score, -4)
            delta.progress_score = min(delta.progress_score, -2)
            delta.pace_score = min(delta.pace_score, -3)
            delta.responsiveness_score = min(delta.responsiveness_score, -1)

            if "信息不足" not in "".join(result.risk_flags):
                result.risk_flags.append("信息不足，可能导致对话停滞或反复解释")

        if target_resistant:
            delta.atmosphere_score = min(delta.atmosphere_score, -2)
            delta.pressure_level = max(delta.pressure_level, 1)
            delta.progress_score = min(delta.progress_score, 0)
            delta.repairability_score = min(delta.repairability_score, 0)

        if target_accepting and not has_pressure:
            delta.atmosphere_score = max(delta.atmosphere_score, 2)
            delta.progress_score = max(delta.progress_score, 2)
            delta.repairability_score = max(delta.repairability_score, 1)

        update.control_suggestions = self._clean_list(
            update.control_suggestions,
            max_items=5,
        )

    def _rebuild_updated_dynamics(
        self,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
    ) -> None:
        """
        用 current_dynamics + dynamics_delta 重新计算 updated_dynamics。

        不完全信任 LLM 直接给出的 updated_dynamics，
        避免出现 delta 和 updated 不一致。
        """

        base = self._get_current_dynamics(request)
        delta = result.dynamics_update.dynamics_delta

        existing_reason = ""
        current_update = getattr(result, "dynamics_update", None)
        if current_update and current_update.updated_dynamics:
            existing_reason = current_update.updated_dynamics.dynamics_reason

        updated = ConversationDynamics(
            atmosphere_score=self._clamp(
                base.atmosphere_score + delta.atmosphere_score,
                0,
                100,
            ),
            pace_score=self._clamp(
                base.pace_score + delta.pace_score,
                0,
                100,
            ),
            pressure_level=self._clamp(
                base.pressure_level + delta.pressure_level,
                0,
                100,
            ),
            clarity_score=self._clamp(
                base.clarity_score + delta.clarity_score,
                0,
                100,
            ),
            responsiveness_score=self._clamp(
                base.responsiveness_score + delta.responsiveness_score,
                0,
                100,
            ),
            progress_score=self._clamp(
                base.progress_score + delta.progress_score,
                0,
                100,
            ),
            repairability_score=self._clamp(
                base.repairability_score + delta.repairability_score,
                0,
                100,
            ),
            boundary_score=self._clamp(
                base.boundary_score + delta.boundary_score,
                0,
                100,
            ),
            rhythm_label="balanced",
            atmosphere_label="neutral",
            recommended_next_move="clarify",
            dynamics_reason=self._clean_text(
                existing_reason,
                default="本轮动态指标根据用户表达、目标人物回复、压力水平、清晰度和节奏健康度综合更新。",
            ),
        )

        updated.rhythm_label = self._infer_rhythm_label(updated)
        updated.atmosphere_label = self._infer_atmosphere_label(updated)
        updated.recommended_next_move = self._infer_recommended_next_move(updated)

        result.dynamics_update.updated_dynamics = updated

    def _normalize_dynamics_text_fields(self, result: StateEvaluationResponse) -> None:
        dynamics = result.dynamics_update.updated_dynamics

        dynamics.dynamics_reason = self._clean_text(
            dynamics.dynamics_reason,
            default="本轮动态指标根据用户表达、目标人物回复、压力水平、清晰度和节奏健康度综合更新。",
        )
        dynamics.dynamics_reason = self._truncate(
            dynamics.dynamics_reason,
            max_length=300,
        )

    def _normalize_dynamics_suggestions(
        self,
        result: StateEvaluationResponse,
    ) -> None:
        update = result.dynamics_update

        update.control_suggestions = self._clean_list(
            update.control_suggestions,
            max_items=5,
        )

        if not update.control_suggestions:
            update.control_suggestions = self._build_control_suggestions(
                update.updated_dynamics
            )

        update.control_suggestions = self._clean_list(
            update.control_suggestions,
            max_items=5,
        )

    def _get_current_dynamics(self, request: StateEvaluateRequest) -> ConversationDynamics:
        current = getattr(request, "current_dynamics", None)

        if isinstance(current, ConversationDynamics):
            return current

        return self._default_dynamics(request)

    def _default_dynamics(self, request: StateEvaluateRequest) -> ConversationDynamics:
        """
        如果上游没有传 current_dynamics，
        根据当前关系状态给一个保守默认值。
        """

        state = request.current_state

        trust = self._get_int_attr(state, "trust", 50)
        respect = self._get_int_attr(state, "respect", 50)
        affinity = self._get_int_attr(state, "affinity", 50)
        emotional = self._get_int_attr(state, "emotional", 50)

        atmosphere_score = self._clamp(
            int((trust + respect + affinity + emotional) / 4),
            0,
            100,
        )

        repairability_score = self._clamp(
            int((trust + respect + emotional) / 3),
            0,
            100,
        )

        default = ConversationDynamics(
            atmosphere_score=atmosphere_score,
            pace_score=55,
            pressure_level=35,
            clarity_score=50,
            responsiveness_score=50,
            progress_score=40,
            repairability_score=repairability_score,
            boundary_score=55,
            rhythm_label="balanced",
            atmosphere_label="neutral",
            recommended_next_move="clarify",
            dynamics_reason="初始动态指标根据当前关系状态保守估计。",
        )

        default.rhythm_label = self._infer_rhythm_label(default)
        default.atmosphere_label = self._infer_atmosphere_label(default)
        default.recommended_next_move = self._infer_recommended_next_move(default)

        return default

    def _infer_rhythm_label(self, dynamics: ConversationDynamics) -> str:
        """
        pace_score 是节奏健康度，不是推进速度。
        pressure_level 高时，即使 pace_score 不低，也应判断为偏快。
        """

        if dynamics.pressure_level >= 75:
            return "too_fast"

        if dynamics.pressure_level >= 62:
            return "slightly_fast"

        if dynamics.pace_score <= 30 and dynamics.progress_score <= 35:
            return "stalled"

        if dynamics.pace_score <= 40:
            return "slightly_slow"

        if dynamics.pace_score <= 50 and dynamics.clarity_score <= 40:
            return "stalled"

        return "balanced"

    def _infer_atmosphere_label(self, dynamics: ConversationDynamics) -> str:
        if dynamics.atmosphere_score <= 25:
            return "blocked"

        if dynamics.pressure_level >= 75 and dynamics.atmosphere_score <= 45:
            return "defensive"

        if dynamics.pressure_level >= 65:
            return "tense"

        if dynamics.atmosphere_score <= 40:
            return "tense"

        if dynamics.atmosphere_score >= 72 and dynamics.pressure_level <= 35:
            return "safe"

        if dynamics.atmosphere_score >= 58:
            return "warm"

        return "neutral"

    def _infer_recommended_next_move(
        self,
        dynamics: ConversationDynamics,
    ) -> str:
        if dynamics.pressure_level >= 65:
            return "slow_down"

        if dynamics.atmosphere_score <= 35 or dynamics.repairability_score <= 40:
            return "repair"

        if dynamics.clarity_score <= 45 or dynamics.responsiveness_score <= 45:
            return "clarify"

        if dynamics.boundary_score <= 40:
            return "set_boundary"

        if (
            dynamics.progress_score >= 65
            and dynamics.atmosphere_score >= 55
            and dynamics.pressure_level <= 55
        ):
            return "advance"

        if dynamics.pace_score <= 35 and dynamics.progress_score <= 35:
            return "clarify"

        return "clarify"

    def _build_control_suggestions(
        self,
        dynamics: ConversationDynamics,
    ) -> list[str]:
        suggestions: list[str] = []

        if dynamics.pressure_level >= 65:
            suggestions.append("下一轮先降低催促感，给对方选择空间，不要要求对方立刻表态。")

        if dynamics.atmosphere_score <= 45:
            suggestions.append("先回应对方顾虑，再提出请求，避免继续解释自己的立场。")

        if dynamics.clarity_score <= 45:
            suggestions.append("补充具体事实、时间节点和需要对方判断的重点。")

        if dynamics.responsiveness_score <= 45:
            suggestions.append("先接住对方已经表达的顾虑，再推进自己的目标。")

        if dynamics.pace_score <= 40:
            suggestions.append("调整对话节奏，把请求拆成一个对方能立刻判断的小动作。")

        if dynamics.boundary_score <= 45:
            suggestions.append("明确自己的需求边界，同时避免把决定压力全部推给对方。")

        if dynamics.repairability_score <= 40:
            suggestions.append("加入责任承担或修复性表达，先恢复信任再推进目标。")

        return suggestions[:5] or ["下一轮保持具体、尊重和低压力表达。"]

    @staticmethod
    def _get_int_attr(obj: Any, field_name: str, default: int) -> int:
        if isinstance(obj, dict):
            value = obj.get(field_name, default)
        else:
            value = getattr(obj, field_name, default)

        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _clean_text(value: str, *, default: str) -> str:
        value = value.strip() if isinstance(value, str) else ""
        return value or default

    @staticmethod
    def _truncate(value: str, *, max_length: int) -> str:
        value = value.strip()
        if len(value) <= max_length:
            return value
        return value[: max_length - 1].rstrip() + "…"

    def _clean_list(self, values: list[str], *, max_items: int) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            if not isinstance(value, str):
                continue
            item = self._truncate(value.strip(), max_length=140)
            if item and item not in cleaned:
                cleaned.append(item)
        return cleaned[:max_items]

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        normalized = text.lower()
        return any(keyword.lower() in normalized for keyword in keywords)

    @staticmethod
    def _clamp(value: int, low: int, high: int) -> int:
        return max(low, min(high, int(value)))


