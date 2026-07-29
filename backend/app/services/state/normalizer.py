from __future__ import annotations

from app.schemas.dynamics import ConversationDynamicsDelta
from app.schemas.session import StateDelta
from app.schemas.state import StateEvaluationResponse
from app.services.state.constants import DYNAMIC_FIELDS
from app.services.state.utils import clean_list, clean_text, clamp, truncate


class StateOutputNormalizer:
    """统一约束模型输出的数值、文本和列表字段。"""

    def normalize_state_delta(self, delta: StateDelta) -> None:
        delta.trust = clamp(delta.trust, -6, 6)
        delta.respect = clamp(delta.respect, -6, 6)
        delta.familiarity = clamp(delta.familiarity, -4, 4)
        delta.affinity = clamp(delta.affinity, -5, 5)
        delta.authority = clamp(delta.authority, -2, 2)
        delta.emotional = clamp(delta.emotional, -6, 6)

    def normalize_dynamic_delta(
        self,
        delta: ConversationDynamicsDelta,
    ) -> None:
        for field_name in DYNAMIC_FIELDS:
            value = getattr(delta, field_name)
            limit = 12 if field_name == "pressure_level" else 10
            setattr(
                delta,
                field_name,
                clamp(value, -limit, limit),
            )

    def normalize_text_fields(
        self,
        result: StateEvaluationResponse,
    ) -> None:
        result.state_reason = truncate(
            clean_text(
                result.state_reason,
                default="本轮表达对关系状态产生了有限影响。",
            ),
            max_length=300,
        )

        dynamics = result.dynamics_update.updated_dynamics
        dynamics.dynamics_reason = truncate(
            clean_text(
                dynamics.dynamics_reason,
                default=(
                    "本轮动态变化主要由表达清晰度、压力感和"
                    "目标人物回应共同决定。"
                ),
            ),
            max_length=360,
        )

    def normalize_lists(
        self,
        result: StateEvaluationResponse,
    ) -> None:
        result.positive_signals = clean_list(
            result.positive_signals,
            max_items=5,
        )
        result.negative_signals = clean_list(
            result.negative_signals,
            max_items=5,
        )
        result.risk_flags = clean_list(
            result.risk_flags,
            max_items=6,
        )
        result.dynamics_update.control_suggestions = clean_list(
            result.dynamics_update.control_suggestions,
            max_items=3,
        )

    def normalize_before_guardrails(
        self,
        result: StateEvaluationResponse,
    ) -> None:
        self.normalize_state_delta(result.state_delta)
        self.normalize_dynamic_delta(
            result.dynamics_update.dynamics_delta,
        )
        self.normalize_text_fields(result)
        self.normalize_lists(result)

    def normalize_after_guardrails(
        self,
        result: StateEvaluationResponse,
    ) -> None:
        self.normalize_state_delta(result.state_delta)
        self.normalize_dynamic_delta(
            result.dynamics_update.dynamics_delta,
        )
