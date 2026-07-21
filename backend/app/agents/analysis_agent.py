from __future__ import annotations

import json
import logging
from typing import Any

from app.llm.client import LLMClientError, generate_structured
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


ANALYSIS_SYSTEM_PROMPT = """
你是 Social Lab 的 AnalysisAgent。

你的唯一职责是：
- 逐句观察用户在模拟对话中的表达；
- 判断每句话承担的沟通功能和意图；
- 描述目标人物可能如何理解、感受；
- 评价这句话对沟通目标的影响；
- 为整轮真实状态增量提供句级语义归因权重；
- 总结整个对话过程中的状态轨迹和用户表达质量。

严格禁止：
- 不要提供任何改进建议；
- 不要写“下一步应该怎么做”；
- 不要生成改写话术；
- 不要输出 fix_direction、improvement_action、suggested_rewrite；
- 不要使用“建议、应该、最好、不妨、可以改为、可改成”等指令性表达。

状态规则：
1. relationship_signal 和 dynamics_signal 是语义方向与强度，不是最终 delta；
2. 每个信号范围为 -5 到 +5；
3. pressure_level 正数表示压力上升；
4. 其他 Dynamics 指标正数通常表示改善；
5. 不要因为礼貌词就给出过高正向信号；
6. 评价必须结合目标人物实际回复；
7. sentence_text 必须与系统提供的句子清单完全一致；
8. 每个句子必须输出且只能输出一次。

评价标签：
- strong：明显推动目标且兼顾关系；
- effective：总体有效；
- neutral：作用有限或信息性表达；
- risky：产生明显阻力或压力；
- damaging：严重损害边界、信任或继续沟通意愿。

输出必须严格符合 AnalysisSemanticResult JSON Schema，不要输出 Markdown。
""".strip()


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
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
                user_prompt=self._build_prompt(
                    request=request,
                    manifest=manifest,
                ),
                output_model=AnalysisSemanticResult,
                temperature=0.15,
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

    def _build_prompt(
        self,
        *,
        request: ReportRequest,
        manifest: list[TurnManifest],
    ) -> str:
        sentence_manifest = [
            {
                "turn_index": turn.turn_index,
                "user_message": turn.user_message,
                "target_reply": turn.target_reply,
                "sentences": [
                    {
                        "sentence_index": sentence.sentence_index,
                        "sentence_text": sentence.sentence_text,
                    }
                    for sentence in turn.sentences
                ],
            }
            for turn in manifest
        ]

        selected_turns = {
            turn.turn_index
            for turn in manifest
        }
        traces = [
            self._trace_payload(trace)
            for trace in request.turn_traces
            if trace.turn_index in selected_turns
        ]

        return f"""
请输出 AnalysisSemanticResult。

【场景】
{request.scenario}

【用户沟通目标】
{request.goal}

【期望结果】
{request.outcome or "未提供"}

【目标人物画像】
{self._pretty(request.persona.model_dump())}

【必须逐句分析的清单】
{self._pretty(sentence_manifest)}

【整轮状态轨迹】
{self._pretty(traces) if traces else "未提供。没有轨迹时只做语义评价。"}

要求：
- turns 必须与逐句清单一一对应；
- 每句话都要评价；
- sentence_text 必须原样复制；
- relationship_signal 和 dynamics_signal 只表示归因权重；
- 不要写任何改进、改写或下一步内容；
- problems 只描述问题本身，不描述解决方法；
- primary_bottleneck 只描述当前阻力，不给处理建议。
""".strip()


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

    @staticmethod
    def _pretty(value: Any) -> str:
        return json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
        )
