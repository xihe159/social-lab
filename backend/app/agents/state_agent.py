from __future__ import annotations

from app.agents.prompts import STATE_SYSTEM_PROMPT, build_state_user_prompt
from app.llm.client import generate_structured
from app.schemas.session import StateDelta
from app.schemas.state import StateEvaluateRequest, StateEvaluationResponse


class StateAgent:
    """
    StateAgent 负责评估单轮对话对关系状态的影响。

    职责边界：
    - SimulationAgent 负责“像目标人物一样回复”；
    - StateAgent 负责“判断这轮沟通让关系状态如何变化”；
    - Orchestrator 负责把两者结果合并为 SessionMessageResponse。
    """

    async def run(self, request: StateEvaluateRequest) -> StateEvaluationResponse:
        payload = request.model_dump()

        result = await generate_structured(
            system_prompt=STATE_SYSTEM_PROMPT,
            user_prompt=build_state_user_prompt(payload),
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

        Pydantic 负责结构合法性；这里负责关系评估的业务合理性：
        - 单轮变化不要过大；
        - 空文本要兜底；
        - 风险和信号列表要去重、限长；
        - 根据明确表达特征做轻量规则校正。
        """

        self._normalize_state_delta(result.state_delta)
        self._normalize_text_fields(result)
        self._normalize_lists(result)
        self._apply_rule_guardrails(result, request)
        self._normalize_state_delta(result.state_delta)

        return result

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
        result.risk_flags = self._clean_list(result.risk_flags, max_items=5)

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

        polite_keywords = ["请", "谢谢", "麻烦", "辛苦", "您好", "可以", "方便", "抱歉", "不好意思", "thanks", "please"]
        concrete_keywords = ["计划", "安排", "时间", "周", "明天", "今天", "原因", "具体", "步骤", "方案", "补救", "提交", "deadline"]
        pressure_keywords = ["必须", "立刻", "马上", "赶紧", "你应该", "凭什么", "不然", "否则", "必须帮", "asap", "immediately"]
        vague_keywords = ["随便", "反正", "不知道", "你看着办", "没办法", "再说吧"]

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

        # 导师和职场场景中，明确承担责任通常应增加 trust/respect。
        responsibility_keywords = ["我会", "我已经", "我负责", "我承担", "我会补充", "我会整理", "I will", "I have"]
        if request.scenario in {"advisor", "work"} and self._contains_any(text, responsibility_keywords):
            delta.trust = max(delta.trust, 1)
            delta.respect = max(delta.respect, 1)
            if "责任" not in "".join(result.positive_signals):
                result.positive_signals.append("表达中体现了责任承担或主动推进")

        # authority 通常不应因为单轮普通表达大幅变化。
        delta.authority = self._clamp(delta.authority, -2, 2)

        result.positive_signals = self._clean_list(result.positive_signals, max_items=5)
        result.negative_signals = self._clean_list(result.negative_signals, max_items=5)
        result.risk_flags = self._clean_list(result.risk_flags, max_items=5)

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
            item = self._truncate(value.strip(), max_length=120)
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
