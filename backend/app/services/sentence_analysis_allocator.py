from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from math import floor

from app.schemas.analysis import (
    AnalysisCoverage,
    AnalysisSemanticResult,
    ConversationProcessAnalysis,
    ConversationTurnTrace,
    DynamicsMetricState,
    SentenceProcessAnalysis,
    SentenceSemanticObservation,
    TurnProcessAnalysis,
    TurnSemanticObservation,
)
from app.schemas.common import RelationshipState
from app.schemas.dynamics import (
    ConversationDynamics,
    ConversationDynamicsDelta,
)
from app.schemas.report import ReportRequest
from app.schemas.session import ChatMessage, StateDelta


RELATIONSHIP_FIELDS = (
    "trust",
    "respect",
    "familiarity",
    "affinity",
    "authority",
    "emotional",
)

DYNAMICS_FIELDS = (
    "atmosphere_score",
    "pace_score",
    "pressure_level",
    "clarity_score",
    "responsiveness_score",
    "progress_score",
    "repairability_score",
    "boundary_score",
)

MAX_ANALYSIS_TURNS = 20
MAX_ANALYSIS_SENTENCES = 100


@dataclass(frozen=True)
class SentenceManifestItem:
    turn_index: int
    sentence_index: int
    sentence_text: str


@dataclass(frozen=True)
class TurnManifest:
    turn_index: int
    user_message: str
    target_reply: str
    sentences: tuple[SentenceManifestItem, ...]


class SentenceAnalysisAllocator:
    """
    将 AnalysisAgent 的句级语义信号映射为可审计的句级状态归因。

    核心约束：
    - StateAgent 只测得整轮 delta；
    - 句级变化是归因，不是新的独立测量；
    - 每个指标的句级 delta 之和严格等于该轮真实 delta；
    - 没有 ConversationTurnTrace 时，不伪造状态数值。
    """

    def build_manifest(
        self,
        messages: list[ChatMessage],
    ) -> tuple[list[TurnManifest], AnalysisCoverage]:
        raw_turns: list[tuple[str, str]] = []
        current_user: str | None = None
        current_target = ""

        for message in messages:
            content = message.content.strip()
            if not content:
                continue

            if message.role == "user":
                if current_user is not None:
                    raw_turns.append((current_user, current_target))
                current_user = content
                current_target = ""
            elif message.role == "target" and current_user is not None:
                if current_target:
                    current_target = f"{current_target}\n{content}"
                else:
                    current_target = content

        if current_user is not None:
            raw_turns.append((current_user, current_target))

        total_turns = len(raw_turns)
        total_sentences = sum(
            len(self.split_sentences(user_message))
            for user_message, _ in raw_turns
        )

        selected_turns = raw_turns[:MAX_ANALYSIS_TURNS]
        manifests: list[TurnManifest] = []
        analyzed_sentence_count = 0

        for turn_index, (user_message, target_reply) in enumerate(
            selected_turns,
            start=1,
        ):
            sentence_texts = self.split_sentences(user_message)
            remaining = MAX_ANALYSIS_SENTENCES - analyzed_sentence_count
            if remaining <= 0:
                break
            sentence_texts = sentence_texts[:remaining]

            sentence_items = tuple(
                SentenceManifestItem(
                    turn_index=turn_index,
                    sentence_index=sentence_index,
                    sentence_text=sentence_text,
                )
                for sentence_index, sentence_text in enumerate(
                    sentence_texts,
                    start=1,
                )
            )
            analyzed_sentence_count += len(sentence_items)

            manifests.append(
                TurnManifest(
                    turn_index=turn_index,
                    user_message=user_message,
                    target_reply=target_reply,
                    sentences=sentence_items,
                )
            )

        coverage = AnalysisCoverage(
            total_user_turns=total_turns,
            analyzed_user_turns=len(manifests),
            total_user_sentences=total_sentences,
            analyzed_user_sentences=analyzed_sentence_count,
            turn_trace_count=0,
            complete=(
                len(manifests) == total_turns
                and analyzed_sentence_count == total_sentences
            ),
        )
        return manifests, coverage

    @staticmethod
    def split_sentences(text: str) -> list[str]:
        """
        中英文混合句子切分。

        保留句末标点，避免报告中的 evidence_quote 与原句不一致。
        换行也作为弱分隔符。
        """

        normalized = re.sub(r"\r\n?", "\n", text.strip())
        if not normalized:
            return []

        pieces = re.findall(
            r"[^。！？!?；;\n]+[。！？!?；;]?|[^\n]+$",
            normalized,
        )

        cleaned: list[str] = []
        for piece in pieces:
            sentence = piece.strip()
            if sentence:
                cleaned.append(sentence)

        return cleaned or [normalized]

    def build_analysis(
        self,
        *,
        request: ReportRequest,
        semantic: AnalysisSemanticResult,
        manifest: list[TurnManifest],
        coverage: AnalysisCoverage,
    ) -> ConversationProcessAnalysis:
        trace_map = {
            trace.turn_index: trace
            for trace in request.turn_traces
        }

        normalized_turns = self._normalize_semantic_turns(
            semantic.turns,
            manifest,
        )

        turn_results: list[TurnProcessAnalysis] = []
        for turn_manifest in manifest:
            semantic_turn = normalized_turns[turn_manifest.turn_index]
            trace = trace_map.get(turn_manifest.turn_index)

            turn_results.append(
                self._build_turn_analysis(
                    turn_manifest=turn_manifest,
                    semantic_turn=semantic_turn,
                    trace=trace,
                )
            )

        coverage.turn_trace_count = sum(
            1
            for turn in manifest
            if turn.turn_index in trace_map
        )

        methodology_notice = (
            "逐句状态变化采用“句级归因”方法：StateAgent 提供整轮关系状态与 "
            "Dynamics 增量，AnalysisAgent 判断每句话的语义影响权重，系统再将整轮"
            "增量确定性分配到各句。每轮各句增量之和严格等于该轮真实增量。"
            "没有整轮轨迹的数据不会伪造句级状态数值。"
        )

        return ConversationProcessAnalysis(
            methodology_notice=methodology_notice,
            coverage=coverage,
            overall_assessment=self._strip_prescriptive(
                semantic.overall_assessment,
                fallback="当前分析基于用户逐句表达、目标人物回复和状态轨迹。",
            ),
            strengths=self._clean_list(
                semantic.strengths,
                fallback=["用户已经形成可识别的沟通目标。"],
                max_items=6,
            ),
            problems=self._clean_list(
                semantic.problems,
                fallback=["部分句子对目标人物的成本、顾虑或边界表达不足。"],
                max_items=6,
            ),
            key_risks=self._clean_list(
                semantic.key_risks,
                fallback=["部分表达可能提高压力或降低继续沟通意愿。"],
                max_items=6,
            ),
            primary_bottleneck=self._strip_prescriptive(
                semantic.primary_bottleneck,
                fallback="当前主要阻力来自表达与目标人物顾虑之间的不匹配。",
            ),
            evaluation_scores=semantic.evaluation_scores,
            state_trajectory_summary=self._strip_prescriptive(
                semantic.state_trajectory_summary,
                fallback="当前状态轨迹信息有限，无法形成完整变化结论。",
            ),
            turns=turn_results,
        )

    def _build_turn_analysis(
        self,
        *,
        turn_manifest: TurnManifest,
        semantic_turn: TurnSemanticObservation,
        trace: ConversationTurnTrace | None,
    ) -> TurnProcessAnalysis:
        sentence_observations = semantic_turn.sentences

        relationship_allocations: dict[str, list[int]] = {}
        dynamics_allocations: dict[str, list[int]] = {}

        if trace is not None:
            for field_name in RELATIONSHIP_FIELDS:
                signals = [
                    getattr(item.relationship_signal, field_name)
                    for item in sentence_observations
                ]
                relationship_allocations[field_name] = self._allocate_integer(
                    total=getattr(trace.relationship_delta, field_name),
                    signals=signals,
                )

            if trace.dynamics_delta is not None:
                for field_name in DYNAMICS_FIELDS:
                    signals = [
                        getattr(item.dynamics_signal, field_name)
                        for item in sentence_observations
                    ]
                    dynamics_allocations[field_name] = self._allocate_integer(
                        total=getattr(trace.dynamics_delta, field_name),
                        signals=signals,
                    )

        relationship_cursor = (
            trace.relationship_before.model_copy()
            if trace is not None
            else None
        )
        dynamics_cursor = self._resolve_dynamics_before(trace)

        sentence_results: list[SentenceProcessAnalysis] = []
        for sentence_position, item in enumerate(sentence_observations):
            if trace is None:
                sentence_results.append(
                    self._build_unavailable_sentence(item)
                )
                continue

            relationship_before = (
                relationship_cursor.model_copy()
                if relationship_cursor is not None
                else None
            )
            relationship_delta = StateDelta(
                **{
                    field_name: relationship_allocations[field_name][
                        sentence_position
                    ]
                    for field_name in RELATIONSHIP_FIELDS
                }
            )
            relationship_cursor = self._apply_relationship_delta(
                relationship_cursor,
                relationship_delta,
            )
            relationship_after = relationship_cursor.model_copy()

            dynamics_before = (
                dynamics_cursor.model_copy()
                if dynamics_cursor is not None
                else None
            )
            dynamics_delta = None
            dynamics_after = None

            if trace.dynamics_delta is not None:
                dynamics_delta = ConversationDynamicsDelta(
                    **{
                        field_name: dynamics_allocations[field_name][
                            sentence_position
                        ]
                        for field_name in DYNAMICS_FIELDS
                    }
                )
                dynamics_cursor = self._apply_dynamics_delta(
                    dynamics_cursor,
                    dynamics_delta,
                )
                dynamics_after = (
                    dynamics_cursor.model_copy()
                    if dynamics_cursor is not None
                    else None
                )

            sentence_results.append(
                SentenceProcessAnalysis(
                    turn_index=item.turn_index,
                    sentence_index=item.sentence_index,
                    sentence_text=item.sentence_text,
                    communicative_function=item.communicative_function,
                    intent_summary=self._strip_prescriptive(
                        item.intent_summary,
                        fallback="该句表达了当前沟通意图。",
                    ),
                    target_likely_interpretation=self._strip_prescriptive(
                        item.target_likely_interpretation,
                        fallback="目标人物可能按字面理解该句。",
                    ),
                    target_likely_feeling=item.target_likely_feeling,
                    evaluation_label=item.evaluation_label,
                    evaluation_score=item.evaluation_score,
                    goal_effect=item.goal_effect,
                    evaluation_reason=self._strip_prescriptive(
                        item.evaluation_reason,
                        fallback="该评价基于句子内容、上下文和目标人物回复。",
                    ),
                    state_change_source="turn_delta_attribution",
                    state_change_note=(
                        "本句变化是对该轮真实状态增量的语义归因；"
                        "不是独立传感或独立模型测量。"
                    ),
                    relationship_before=relationship_before,
                    relationship_delta=relationship_delta,
                    relationship_after=relationship_after,
                    dynamics_before=dynamics_before,
                    dynamics_delta=dynamics_delta,
                    dynamics_after=dynamics_after,
                )
            )

        return TurnProcessAnalysis(
            turn_index=turn_manifest.turn_index,
            user_message=turn_manifest.user_message,
            target_reply=turn_manifest.target_reply,
            turn_summary=self._strip_prescriptive(
                semantic_turn.turn_summary,
                fallback="本轮包含用户表达及目标人物回应。",
            ),
            target_reply_interpretation=self._strip_prescriptive(
                semantic_turn.target_reply_interpretation,
                fallback="目标人物回复反映了当前接受度和顾虑。",
            ),
            turn_evaluation_score=semantic_turn.turn_evaluation_score,
            relationship_before=(
                trace.relationship_before if trace is not None else None
            ),
            relationship_delta=(
                trace.relationship_delta if trace is not None else None
            ),
            relationship_after=(
                trace.relationship_after if trace is not None else None
            ),
            dynamics_before=self._resolve_dynamics_before(trace),
            dynamics_delta=(
                trace.dynamics_delta if trace is not None else None
            ),
            dynamics_after=self._dynamics_metrics(
                trace.dynamics_after
                if trace is not None
                else None
            ),
            risk_flags=(
                self._clean_list(
                    trace.risk_flags,
                    fallback=[],
                    max_items=6,
                )
                if trace is not None
                else []
            ),
            sentences=sentence_results,
        )

    def _build_unavailable_sentence(
        self,
        item: SentenceSemanticObservation,
    ) -> SentenceProcessAnalysis:
        return SentenceProcessAnalysis(
            turn_index=item.turn_index,
            sentence_index=item.sentence_index,
            sentence_text=item.sentence_text,
            communicative_function=item.communicative_function,
            intent_summary=self._strip_prescriptive(
                item.intent_summary,
                fallback="该句表达了当前沟通意图。",
            ),
            target_likely_interpretation=self._strip_prescriptive(
                item.target_likely_interpretation,
                fallback="目标人物可能按字面理解该句。",
            ),
            target_likely_feeling=item.target_likely_feeling,
            evaluation_label=item.evaluation_label,
            evaluation_score=item.evaluation_score,
            goal_effect=item.goal_effect,
            evaluation_reason=self._strip_prescriptive(
                item.evaluation_reason,
                fallback="该评价基于句子内容和上下文。",
            ),
            state_change_source="unavailable",
            state_change_note=(
                "该轮没有保存完整 ConversationTurnTrace，"
                "因此只展示语义评价，不展示伪造的句级状态数值。"
            ),
            relationship_before=None,
            relationship_delta=None,
            relationship_after=None,
            dynamics_before=None,
            dynamics_delta=None,
            dynamics_after=None,
        )

    def _normalize_semantic_turns(
        self,
        semantic_turns: list[TurnSemanticObservation],
        manifest: list[TurnManifest],
    ) -> dict[int, TurnSemanticObservation]:
        provided = {
            turn.turn_index: turn
            for turn in semantic_turns
        }
        normalized: dict[int, TurnSemanticObservation] = {}

        for turn_manifest in manifest:
            candidate = provided.get(turn_manifest.turn_index)
            sentence_map = {
                item.sentence_index: item
                for item in candidate.sentences
            } if candidate is not None else {}

            normalized_sentences: list[SentenceSemanticObservation] = []
            for sentence_manifest in turn_manifest.sentences:
                item = sentence_map.get(
                    sentence_manifest.sentence_index
                )
                if item is None:
                    item = self._fallback_sentence(sentence_manifest)
                else:
                    item.turn_index = sentence_manifest.turn_index
                    item.sentence_index = sentence_manifest.sentence_index
                    item.sentence_text = sentence_manifest.sentence_text
                    item.intent_summary = self._strip_prescriptive(
                        item.intent_summary,
                        fallback="该句表达了当前沟通意图。",
                    )
                    item.target_likely_interpretation = (
                        self._strip_prescriptive(
                            item.target_likely_interpretation,
                            fallback="目标人物可能按字面理解该句。",
                        )
                    )
                    item.evaluation_reason = self._strip_prescriptive(
                        item.evaluation_reason,
                        fallback="该评价基于句子内容和上下文。",
                    )

                normalized_sentences.append(item)

            if candidate is None:
                candidate = TurnSemanticObservation(
                    turn_index=turn_manifest.turn_index,
                    turn_summary="本轮包含用户表达及目标人物回应。",
                    target_reply_interpretation=(
                        "目标人物回复反映了当前接受度和顾虑。"
                    ),
                    turn_evaluation_score=self._average(
                        [
                            item.evaluation_score
                            for item in normalized_sentences
                        ],
                        default=50,
                    ),
                    sentences=normalized_sentences,
                )
            else:
                candidate.turn_index = turn_manifest.turn_index
                candidate.turn_summary = self._strip_prescriptive(
                    candidate.turn_summary,
                    fallback="本轮包含用户表达及目标人物回应。",
                )
                candidate.target_reply_interpretation = (
                    self._strip_prescriptive(
                        candidate.target_reply_interpretation,
                        fallback="目标人物回复反映了当前接受度和顾虑。",
                    )
                )
                candidate.sentences = normalized_sentences

            normalized[turn_manifest.turn_index] = candidate

        return normalized

    @staticmethod
    def _fallback_sentence(
        item: SentenceManifestItem,
    ) -> SentenceSemanticObservation:
        from app.schemas.analysis import (
            DynamicsSignalVector,
            RelationshipSignalVector,
        )

        return SentenceSemanticObservation(
            turn_index=item.turn_index,
            sentence_index=item.sentence_index,
            sentence_text=item.sentence_text,
            communicative_function="other",
            intent_summary="该句表达了当前沟通内容。",
            target_likely_interpretation="目标人物可能按字面理解该句。",
            target_likely_feeling="neutral",
            evaluation_label="neutral",
            evaluation_score=50,
            goal_effect="neutral",
            evaluation_reason="当前缺少更具体的句级语义判断。",
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

    @staticmethod
    def _allocate_integer(
        *,
        total: int,
        signals: list[int],
    ) -> list[int]:
        """
        Largest-remainder integer allocation。

        对于正 delta 优先使用正向信号；
        对于负 delta 优先使用负向信号；
        若没有同方向信号，再使用绝对强度；
        若全部为 0，则平均分配。
        """

        count = len(signals)
        if count == 0:
            return []
        if total == 0:
            return [0] * count

        direction = 1 if total > 0 else -1
        weights = [
            max(0, signal * direction)
            for signal in signals
        ]

        if sum(weights) == 0:
            weights = [abs(signal) for signal in signals]
        if sum(weights) == 0:
            weights = [1] * count

        absolute_total = abs(total)
        weight_sum = sum(weights)
        quotas = [
            absolute_total * weight / weight_sum
            for weight in weights
        ]
        allocated = [floor(value) for value in quotas]
        remainder = absolute_total - sum(allocated)

        order = sorted(
            range(count),
            key=lambda index: (
                quotas[index] - allocated[index],
                weights[index],
                -index,
            ),
            reverse=True,
        )
        for index in order[:remainder]:
            allocated[index] += 1

        return [direction * value for value in allocated]

    @staticmethod
    def _apply_relationship_delta(
        state: RelationshipState | None,
        delta: StateDelta,
    ) -> RelationshipState:
        if state is None:
            state = RelationshipState(
                trust=50,
                respect=50,
                familiarity=50,
                affinity=50,
                authority=50,
                emotional=0,
            )

        values = state.model_dump()
        for field_name in RELATIONSHIP_FIELDS:
            low, high = (
                (-100, 100)
                if field_name == "emotional"
                else (0, 100)
            )
            values[field_name] = max(
                low,
                min(
                    high,
                    values[field_name]
                    + getattr(delta, field_name),
                ),
            )
        return RelationshipState(**values)

    @staticmethod
    def _apply_dynamics_delta(
        state: DynamicsMetricState | None,
        delta: ConversationDynamicsDelta,
    ) -> DynamicsMetricState | None:
        if state is None:
            return None

        values = state.model_dump()
        for field_name in DYNAMICS_FIELDS:
            values[field_name] = max(
                0,
                min(
                    100,
                    values[field_name]
                    + getattr(delta, field_name),
                ),
            )
        return DynamicsMetricState(**values)

    def _resolve_dynamics_before(
        self,
        trace: ConversationTurnTrace | None,
    ) -> DynamicsMetricState | None:
        if trace is None:
            return None
        if trace.dynamics_before is not None:
            return self._dynamics_metrics(trace.dynamics_before)
        if (
            trace.dynamics_after is not None
            and trace.dynamics_delta is not None
        ):
            values = {
                field_name: max(
                    0,
                    min(
                        100,
                        getattr(trace.dynamics_after, field_name)
                        - getattr(trace.dynamics_delta, field_name),
                    ),
                )
                for field_name in DYNAMICS_FIELDS
            }
            return DynamicsMetricState(**values)
        return None

    @staticmethod
    def _dynamics_metrics(
        dynamics: ConversationDynamics | None,
    ) -> DynamicsMetricState | None:
        if dynamics is None:
            return None
        return DynamicsMetricState(
            **{
                field_name: getattr(dynamics, field_name)
                for field_name in DYNAMICS_FIELDS
            }
        )

    @staticmethod
    def _strip_prescriptive(
        value: str,
        *,
        fallback: str,
    ) -> str:
        text = value.strip() if isinstance(value, str) else ""
        if not text:
            return fallback

        forbidden = (
            "建议",
            "下一步",
            "应该",
            "应当",
            "最好",
            "不妨",
            "可以改为",
            "可改成",
            "需要改成",
            "改写为",
        )

        clauses = re.split(r"(?<=[。！？!?；;])", text)
        kept = [
            clause.strip()
            for clause in clauses
            if clause.strip()
            and not any(
                marker in clause
                for marker in forbidden
            )
        ]
        cleaned = "".join(kept).strip()
        return cleaned or fallback

    def _clean_list(
        self,
        values: Iterable[str],
        *,
        fallback: list[str],
        max_items: int,
    ) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = self._strip_prescriptive(
                str(value),
                fallback="",
            )
            if item and item not in cleaned:
                cleaned.append(item[:260])

        for item in fallback:
            if item and item not in cleaned:
                cleaned.append(item)

        return cleaned[:max_items]

    @staticmethod
    def _average(
        values: list[int],
        *,
        default: int,
    ) -> int:
        if not values:
            return default
        return round(sum(values) / len(values))
