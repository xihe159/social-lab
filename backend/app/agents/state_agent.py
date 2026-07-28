from __future__ import annotations

from collections.abc import Iterable

from app.agents.prompts import STATE_SYSTEM_PROMPT, build_state_user_prompt
from app.llm.client import generate_structured
from app.schemas.dynamics import (
    ConversationDynamics,
    ConversationDynamicsDelta,
)
from app.schemas.session import StateDelta
from app.schemas.state import StateEvaluateRequest, StateEvaluationResponse
from app.services.state import StateResultProcessor
from app.services.state.utils import (
    append_unique,
    clean_list,
    clean_text,
    clamp,
    contains_any,
    number,
    truncate,
)


class StateAgent:
    """
    评估单轮沟通对关系状态和对话动态的影响。

    StateAgent 现在只负责：
    1. 准备 LLM 输入；
    2. 调用结构化模型；
    3. 把模型结果交给确定性 StateResultProcessor。

    规则、信号、数值重建和标签推导位于 app.services.state。
    """

    def __init__(
        self,
        processor: StateResultProcessor | None = None,
    ) -> None:
        self.processor = processor or StateResultProcessor()

    async def run(
        self,
        request: StateEvaluateRequest,
    ) -> StateEvaluationResponse:
        baseline = self.processor.build_baseline(request)
        payload = request.model_dump()
        payload["current_dynamics"] = baseline.model_dump()

        result = await generate_structured(
            system_prompt=STATE_SYSTEM_PROMPT,
            user_prompt=self._build_prompt(payload),
            output_model=StateEvaluationResponse,
        )

        return self.processor.process(
            result=result,
            request=request,
            baseline=baseline,
        )

    def post_process(
        self,
        *,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
    ) -> StateEvaluationResponse:
        """兼容原有测试或调用方使用的同步后处理入口。"""

        return self.processor.process(
            result=result,
            request=request,
        )

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

    # ------------------------------------------------------------------
    # 以下方法是兼容层。新代码应直接测试或调用 app.services.state。
    # ------------------------------------------------------------------

    def _build_initial_dynamics(
        self,
        request: StateEvaluateRequest,
    ) -> ConversationDynamics:
        return self.processor.dynamics_calculator.build_initial(request)

    def _rebuild_updated_dynamics(
        self,
        *,
        baseline: ConversationDynamics,
        delta: ConversationDynamicsDelta,
        request: StateEvaluateRequest,
        model_reason: str,
    ) -> ConversationDynamics:
        return self.processor.dynamics_calculator.rebuild(
            baseline=baseline,
            delta=delta,
            request=request,
            model_reason=model_reason,
        )

    def _build_control_suggestions(
        self,
        dynamics: ConversationDynamics,
    ) -> list[str]:
        return self.processor.dynamics_calculator.build_control_suggestions(
            dynamics
        )

    def _normalize_state_delta(self, delta: StateDelta) -> None:
        self.processor.normalizer.normalize_state_delta(delta)

    def _normalize_dynamic_delta(
        self,
        delta: ConversationDynamicsDelta,
    ) -> None:
        self.processor.normalizer.normalize_dynamic_delta(delta)

    def _normalize_text_fields(
        self,
        result: StateEvaluationResponse,
    ) -> None:
        self.processor.normalizer.normalize_text_fields(result)

    def _normalize_lists(
        self,
        result: StateEvaluationResponse,
    ) -> None:
        self.processor.normalizer.normalize_lists(result)

    def _apply_relationship_guardrails(
        self,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
    ) -> None:
        self.processor.relationship_guardrails.apply(
            result=result,
            request=request,
            signals=self.processor.signal_detector.detect(request),
        )

    def _apply_dynamics_guardrails(
        self,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
    ) -> None:
        self.processor.dynamics_guardrails.apply(
            result=result,
            request=request,
            signals=self.processor.signal_detector.detect(request),
        )

    def _derive_rhythm_label(self, values: dict[str, int]) -> str:
        return self.processor.dynamics_calculator.derive_rhythm_label(values)

    def _derive_atmosphere_label(
        self,
        *,
        values: dict[str, int],
        target_reply: str,
    ) -> str:
        return self.processor.dynamics_calculator.derive_atmosphere_label(
            values=values,
            target_reply=target_reply,
        )

    def _derive_next_move(
        self,
        *,
        values: dict[str, int],
        rhythm_label: str,
        atmosphere_label: str,
    ) -> str:
        return self.processor.dynamics_calculator.derive_next_move(
            values=values,
            rhythm_label=rhythm_label,
            atmosphere_label=atmosphere_label,
        )

    def _build_dynamics_reason(
        self,
        *,
        values: dict[str, int],
        delta: ConversationDynamicsDelta,
        model_reason: str,
    ) -> str:
        return self.processor.dynamics_calculator.build_reason(
            values=values,
            delta=delta,
            model_reason=model_reason,
        )

    @staticmethod
    def _number(value: object, default: int) -> int:
        return number(value, default)

    @staticmethod
    def _clean_text(value: object, *, default: str) -> str:
        return clean_text(value, default=default)

    @staticmethod
    def _truncate(value: str, *, max_length: int) -> str:
        return truncate(value, max_length=max_length)

    @staticmethod
    def _clean_list(
        values: Iterable[object],
        *,
        max_items: int,
    ) -> list[str]:
        return clean_list(values, max_items=max_items)

    @staticmethod
    def _append_unique(values: list[str], item: str) -> None:
        append_unique(values, item)

    @staticmethod
    def _contains_any(
        text: str,
        keywords: Iterable[str],
    ) -> bool:
        return contains_any(text, keywords)

    @staticmethod
    def _clamp(value: int, low: int, high: int) -> int:
        return clamp(value, low, high)
