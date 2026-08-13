from __future__ import annotations

import json
import logging
from typing import Any

from app.llm.client import LLMClientError, generate_structured
from app.prompts.report import ANALYSIS_PROMPT, build_analysis_user_prompt
from app.schemas.analysis import (
    AnalysisSemanticResult,
    ConversationEvaluationScores,
    ConversationProcessAnalysis,
    DynamicsSignalVector,
    RelationshipSignalVector,
    SentenceSemanticObservation,
    TurnSemanticObservation,
)
from app.schemas.report import ReportRequest
from app.services.sentence_analysis_allocator import (
    SentenceAnalysisAllocator,
    TurnManifest,
)


logger = logging.getLogger(__name__)

class AnalysisAgent:
    """
    逐句分析型 Agent。

    LLM 负责语义观察；
    SentenceAnalysisAllocator 负责：
    - 对齐真实句子；
    - 清除改进性措辞；
    - 将整轮真实 delta 归因到句子；
    - 构建最终可展示的对话过程分析。
    """

    def __init__(
        self,
        allocator: SentenceAnalysisAllocator | None = None,
    ) -> None:
        self.allocator = allocator or SentenceAnalysisAllocator()

    async def run(
        self,
        *,
        request: ReportRequest,
    ) -> ConversationProcessAnalysis:
        manifest, coverage = self.allocator.build_manifest(
            request.messages
        )

        if not manifest:
            semantic = self._empty_semantic()
            return self.allocator.build_analysis(
                request=request,
                semantic=semantic,
                manifest=[],
                coverage=coverage,
            )

        try:
            semantic = await generate_structured(
                system_prompt=ANALYSIS_PROMPT.system_prompt,
                user_prompt=build_analysis_user_prompt(
                    request=request,
                    manifest=manifest,
                ),
                output_model=AnalysisSemanticResult,
                temperature=ANALYSIS_PROMPT.temperature,
            )
        except LLMClientError:
            logger.exception(
                "AnalysisAgent LLM failed; using neutral fallback"
            )
            semantic = self._fallback_semantic(manifest)

        return self.allocator.build_analysis(
            request=request,
            semantic=semantic,
            manifest=manifest,
            coverage=coverage,
        )

    @staticmethod
    def _trace_payload(trace: Any) -> dict[str, Any]:
        """只把观察性状态信息传给 AnalysisAgent，不传策略建议字段。"""

        payload = trace.model_dump()
        for field_name in ("dynamics_before", "dynamics_after"):
            dynamics = payload.get(field_name)
            if isinstance(dynamics, dict):
                dynamics.pop("recommended_next_move", None)
                dynamics.pop("dynamics_reason", None)
        return payload

    @staticmethod
    def _fallback_semantic(
        manifest: list[TurnManifest],
    ) -> AnalysisSemanticResult:
        turns: list[TurnSemanticObservation] = []

        for turn in manifest:
            sentences = [
                SentenceSemanticObservation(
                    turn_index=item.turn_index,
                    sentence_index=item.sentence_index,
                    sentence_text=item.sentence_text,
                    communicative_function="other",
                    intent_summary="该句表达了当前沟通内容。",
                    target_likely_interpretation=(
                        "目标人物可能按字面理解该句。"
                    ),
                    target_likely_feeling="neutral",
                    evaluation_label="neutral",
                    evaluation_score=50,
                    goal_effect="neutral",
                    evaluation_reason=(
                        "AnalysisAgent 语义调用失败，当前仅保留中性评价。"
                    ),
                    relationship_signal=RelationshipSignalVector(
                        trust=0,
                        respect=0,
                        familiarity=0,
                        affinity=0,
                        authority=0,
                        emotional=0,
                    ),
                    dynamics_signal=DynamicsSignalVector(
                        atmosphere_score=0,
                        pace_score=0,
                        pressure_level=0,
                        clarity_score=0,
                        responsiveness_score=0,
                        progress_score=0,
                        repairability_score=0,
                        boundary_score=0,
                    ),
                )
                for item in turn.sentences
            ]

            turns.append(
                TurnSemanticObservation(
                    turn_index=turn.turn_index,
                    turn_summary="本轮语义分析使用中性回退结果。",
                    target_reply_interpretation=(
                        "当前未形成可靠的目标人物回复解释。"
                    ),
                    turn_evaluation_score=50,
                    sentences=sentences,
                )
            )

        return AnalysisSemanticResult(
            overall_assessment=(
                "AnalysisAgent 语义调用失败，当前报告保留状态轨迹和中性句级评价。"
            ),
            strengths=["对话中存在可识别的用户表达。"],
            problems=["当前缺少可靠的句级语义评估。"],
            key_risks=["句级评价的置信度较低。"],
            primary_bottleneck="当前主要限制是句级语义证据不足。",
            evaluation_scores=ConversationEvaluationScores(
                clarity=50,
                responsiveness=50,
                respect_and_boundary=50,
                responsibility=50,
                emotional_safety=50,
                goal_alignment=50,
                overall=50,
            ),
            state_trajectory_summary=(
                "状态变化仍以 Session 保存的整轮轨迹为准。"
            ),
            turns=turns,
        )

    @staticmethod
    def _empty_semantic() -> AnalysisSemanticResult:
        return AnalysisSemanticResult(
            overall_assessment="当前没有可分析的用户对话。",
            strengths=[],
            problems=["尚未形成有效用户表达。"],
            key_risks=["对话证据不足。"],
            primary_bottleneck="缺少可分析的用户对话。",
            evaluation_scores=ConversationEvaluationScores(
                clarity=0,
                responsiveness=0,
                respect_and_boundary=0,
                responsibility=0,
                emotional_safety=0,
                goal_alignment=0,
                overall=0,
            ),
            state_trajectory_summary="当前没有状态轨迹。",
            turns=[],
        )

