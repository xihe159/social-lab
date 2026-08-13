from __future__ import annotations

import json
from typing import Any

from app.llm.client import generate_structured
from app.prompts.report import PREDICTION_PROMPT, build_prediction_user_prompt
from app.schemas.dynamics import ConversationDynamics
from app.schemas.prediction import (
    PredictionContext,
    PredictionResult,
    SemanticPredictionAssessment,
)
from app.schemas.report import ReportRequest
from app.schemas.session import ChatMessage
from app.services.prediction_calculator import PredictionCalculator

class PredictionAgent:
    """
    LLM 只进行有限语义判断，PredictionCalculator 决定最终评分、区间和分布。
    """

    def __init__(self, calculator: PredictionCalculator | None = None) -> None:
        self.calculator = calculator or PredictionCalculator()

    async def run(self, request: ReportRequest) -> PredictionResult:
        context = self.build_context(request)
        semantic = await generate_structured(
            system_prompt=PREDICTION_PROMPT.system_prompt,
            user_prompt=build_prediction_user_prompt(request=request, context=context),
            output_model=SemanticPredictionAssessment,
            temperature=PREDICTION_PROMPT.temperature,
        )
        semantic = self.post_process_semantic(semantic, context)
        return self.calculator.calculate(context=context, semantic=semantic)

    def build_context(self, request: ReportRequest) -> PredictionContext:
        messages = request.messages
        user_messages = [
            (index, message)
            for index, message in enumerate(messages, start=1)
            if message.role == "user" and message.content.strip()
        ]
        target_messages = [
            (index, message)
            for index, message in enumerate(messages, start=1)
            if message.role == "target" and message.content.strip()
        ]

        current_dynamics = request.current_dynamics
        if current_dynamics is None and request.dynamics_history:
            current_dynamics = self._snapshot_to_dynamics(
                request.dynamics_history[-1]
            )

        latest_user_turn_index = user_messages[-1][0] if user_messages else 0
        last_user_message = (
            user_messages[-1][1].content.strip() if user_messages else ""
        )
        last_target_message = (
            target_messages[-1][1].content.strip() if target_messages else ""
        )

        return PredictionContext(
            scenario=request.scenario,
            goal=request.goal,
            outcome=request.outcome,
            relationship_state=request.persona.state,
            current_dynamics=current_dynamics,
            dynamics_history=request.dynamics_history,
            user_turn_count=len(user_messages),
            target_turn_count=len(target_messages),
            total_message_count=len(messages),
            last_user_message=last_user_message,
            last_target_message=last_target_message,
            latest_user_turn_index=latest_user_turn_index,
        )

    def post_process_semantic(
        self,
        semantic: SemanticPredictionAssessment,
        context: PredictionContext,
    ) -> SemanticPredictionAssessment:
        semantic.semantic_adjustment = self._clamp(
            semantic.semantic_adjustment,
            -8,
            8,
        )
        semantic.likely_outcome = self._clean_text(
            semantic.likely_outcome,
            "当前信息不足，结果更可能表现为犹豫或要求补充信息。",
            500,
        )
        semantic.probability_reasoning = self._clean_text(
            semantic.probability_reasoning,
            "语义判断主要基于目标人物最新回应与用户表达方式。",
            500,
        )

        cleaned_factors = []
        for factor in semantic.semantic_factors[:4]:
            factor.factor_name = self._clean_text(
                factor.factor_name,
                "未命名语义因素",
                80,
            )
            factor.evidence_quote = self._clean_text(
                factor.evidence_quote,
                "未找到明确原话证据。",
                180,
            )
            factor.explanation = self._clean_text(
                factor.explanation,
                "该因素会影响目标人物当前的接受或继续沟通意愿。",
                260,
            )
            factor.importance = self._clamp(factor.importance, 1, 5)
            factor.evidence_turns = sorted(
                {
                    self._clamp(turn, 1, max(1, context.total_message_count))
                    for turn in factor.evidence_turns
                }
            )[:4]
            cleaned_factors.append(factor)

        semantic.semantic_factors = cleaned_factors

        if context.target_turn_count == 0:
            semantic.outcome_state = "unknown"
            semantic.semantic_adjustment = self._clamp(
                semantic.semantic_adjustment,
                -3,
                3,
            )
            semantic.evidence_strength = min(semantic.evidence_strength, 0.35)

        if self._contains_any(
            context.last_target_message,
            ["不行", "不能", "不接受", "不愿意", "拒绝", "不要再", "别再"],
        ):
            semantic.outcome_state = "refuse"
            semantic.semantic_adjustment = min(
                semantic.semantic_adjustment,
                -2,
            )

        return semantic

    @staticmethod
    def _snapshot_to_dynamics(snapshot: Any) -> ConversationDynamics:
        return ConversationDynamics(
            atmosphere_score=snapshot.atmosphere_score,
            pace_score=snapshot.pace_score,
            pressure_level=snapshot.pressure_level,
            clarity_score=snapshot.clarity_score,
            responsiveness_score=snapshot.responsiveness_score,
            progress_score=snapshot.progress_score,
            repairability_score=snapshot.repairability_score,
            boundary_score=snapshot.boundary_score,
            rhythm_label=snapshot.rhythm_label,
            atmosphere_label=snapshot.atmosphere_label,
            recommended_next_move=snapshot.recommended_next_move,
            dynamics_reason=snapshot.reason,
        )

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        lowered = text.lower()
        return any(keyword.lower() in lowered for keyword in keywords)

    @staticmethod
    def _clean_text(value: object, default: str, max_length: int) -> str:
        text = value.strip() if isinstance(value, str) else ""
        text = text or default
        if len(text) <= max_length:
            return text
        return text[: max_length - 1].rstrip() + "…"

    @staticmethod
    def _clamp(value: int, low: int, high: int) -> int:
        return max(low, min(high, int(value)))
