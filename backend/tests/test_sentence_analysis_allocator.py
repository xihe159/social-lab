from __future__ import annotations

from app.schemas.analysis import (
    AnalysisSemanticResult,
    ConversationEvaluationScores,
    ConversationTurnTrace,
    DynamicsSignalVector,
    RelationshipSignalVector,
    SentenceSemanticObservation,
    TurnSemanticObservation,
)
from app.schemas.common import RelationshipState
from app.schemas.dynamics import (
    ConversationDynamics,
    ConversationDynamicsDelta,
)
from app.schemas.persona import Persona
from app.schemas.report import ReportRequest
from app.schemas.session import ChatMessage, StateDelta
from app.services.sentence_analysis_allocator import (
    DYNAMICS_FIELDS,
    RELATIONSHIP_FIELDS,
    SentenceAnalysisAllocator,
)


def _persona(state: RelationshipState) -> Persona:
    return Persona(
        title="理性直接的导师",
        style="理性、结果导向",
        speed="正常",
        focus="计划、进度和可执行性",
        risk="模糊解释和持续施压",
        strategy="说明事实并给出具体方案",
        state=state,
    )


def _dynamics(
    *,
    atmosphere: int,
    pace: int,
    pressure: int,
    clarity: int,
    responsiveness: int,
    progress: int,
    repairability: int,
    boundary: int,
) -> ConversationDynamics:
    return ConversationDynamics(
        atmosphere_score=atmosphere,
        pace_score=pace,
        pressure_level=pressure,
        clarity_score=clarity,
        responsiveness_score=responsiveness,
        progress_score=progress,
        repairability_score=repairability,
        boundary_score=boundary,
        rhythm_label="balanced",
        atmosphere_label="neutral",
        recommended_next_move="clarify",
        dynamics_reason="测试状态",
    )


def _semantic() -> AnalysisSemanticResult:
    return AnalysisSemanticResult(
        overall_assessment="建议下一步继续说明。当前表达先说明事实，再提出请求。",
        strengths=["表达包含具体时间。"],
        problems=["建议补充对方成本。当前句子存在催促感。"],
        key_risks=["持续要求立即答复可能提高压力。"],
        primary_bottleneck="应该先道歉。当前阻力是催促感。",
        evaluation_scores=ConversationEvaluationScores(
            clarity=70,
            responsiveness=55,
            respect_and_boundary=45,
            responsibility=65,
            emotional_safety=45,
            goal_alignment=60,
            overall=58,
        ),
        state_trajectory_summary="下一步应放慢。当前压力先升后降。",
        turns=[
            TurnSemanticObservation(
                turn_index=1,
                turn_summary="用户先说明计划，再要求立即答复。",
                target_reply_interpretation="对方接受计划信息，但感到被催促。",
                turn_evaluation_score=58,
                sentences=[
                    SentenceSemanticObservation(
                        turn_index=1,
                        sentence_index=1,
                        sentence_text="我会在周三前提交完整版本。",
                        communicative_function="commitment",
                        intent_summary="说明具体承诺。",
                        target_likely_interpretation="用户给出了明确交付时间。",
                        target_likely_feeling="reassured",
                        evaluation_label="effective",
                        evaluation_score=78,
                        goal_effect="supports",
                        evaluation_reason="具体时间降低了信息不确定性。",
                        relationship_signal=RelationshipSignalVector(
                            trust=4,
                            respect=2,
                            familiarity=0,
                            affinity=1,
                            authority=0,
                            emotional=2,
                        ),
                        dynamics_signal=DynamicsSignalVector(
                            atmosphere_score=2,
                            pace_score=2,
                            pressure_level=-1,
                            clarity_score=5,
                            responsiveness_score=2,
                            progress_score=4,
                            repairability_score=2,
                            boundary_score=2,
                        ),
                    ),
                    SentenceSemanticObservation(
                        turn_index=1,
                        sentence_index=2,
                        sentence_text="你必须现在答应。",
                        communicative_function="pressure",
                        intent_summary="要求对方立即表态。",
                        target_likely_interpretation="用户不接受延后决定。",
                        target_likely_feeling="pressured",
                        evaluation_label="risky",
                        evaluation_score=25,
                        goal_effect="obstructs",
                        evaluation_reason="命令式表达明显提高压力。",
                        relationship_signal=RelationshipSignalVector(
                            trust=-4,
                            respect=-5,
                            familiarity=0,
                            affinity=-3,
                            authority=2,
                            emotional=-5,
                        ),
                        dynamics_signal=DynamicsSignalVector(
                            atmosphere_score=-5,
                            pace_score=-4,
                            pressure_level=5,
                            clarity_score=0,
                            responsiveness_score=-4,
                            progress_score=-3,
                            repairability_score=-4,
                            boundary_score=-5,
                        ),
                    ),
                ],
            )
        ],
    )


def _request(with_trace: bool = True) -> ReportRequest:
    before_state = RelationshipState(
        trust=50,
        respect=60,
        familiarity=40,
        affinity=45,
        authority=70,
        emotional=0,
    )
    relationship_delta = StateDelta(
        trust=-2,
        respect=-3,
        familiarity=0,
        affinity=-1,
        authority=1,
        emotional=-4,
    )
    after_state = RelationshipState(
        trust=48,
        respect=57,
        familiarity=40,
        affinity=44,
        authority=71,
        emotional=-4,
    )

    dynamics_before = _dynamics(
        atmosphere=60,
        pace=60,
        pressure=30,
        clarity=50,
        responsiveness=50,
        progress=40,
        repairability=65,
        boundary=60,
    )
    dynamics_delta = ConversationDynamicsDelta(
        atmosphere_score=-3,
        pace_score=-2,
        pressure_level=6,
        clarity_score=3,
        responsiveness_score=-1,
        progress_score=-2,
        repairability_score=-2,
        boundary_score=-4,
    )
    dynamics_after = _dynamics(
        atmosphere=57,
        pace=58,
        pressure=36,
        clarity=53,
        responsiveness=49,
        progress=38,
        repairability=63,
        boundary=56,
    )

    traces = []
    if with_trace:
        traces.append(
            ConversationTurnTrace(
                turn_index=1,
                user_message=(
                    "我会在周三前提交完整版本。你必须现在答应。"
                ),
                target_reply="计划可以看，但不要逼我现在决定。",
                relationship_before=before_state,
                relationship_delta=relationship_delta,
                relationship_after=after_state,
                dynamics_before=dynamics_before,
                dynamics_delta=dynamics_delta,
                dynamics_after=dynamics_after,
                risk_flags=["存在催促感"],
            )
        )

    return ReportRequest(
        scenario="advisor",
        goal="获得延期批准",
        outcome="导师接受周三提交",
        persona=_persona(after_state),
        messages=[
            ChatMessage(
                role="user",
                content="我会在周三前提交完整版本。你必须现在答应。",
            ),
            ChatMessage(
                role="target",
                content="计划可以看，但不要逼我现在决定。",
            ),
        ],
        current_dynamics=dynamics_after,
        dynamics_history=[],
        turn_traces=traces,
    )


def test_sentence_split_preserves_punctuation() -> None:
    allocator = SentenceAnalysisAllocator()
    assert allocator.split_sentences(
        "第一句。第二句！Is this third? 最后一段"
    ) == [
        "第一句。",
        "第二句！",
        "Is this third?",
        "最后一段",
    ]


def test_integer_allocation_conserves_total() -> None:
    allocator = SentenceAnalysisAllocator()

    positive = allocator._allocate_integer(
        total=7,
        signals=[5, 2, -4],
    )
    negative = allocator._allocate_integer(
        total=-5,
        signals=[4, -5, -1],
    )

    assert sum(positive) == 7
    assert sum(negative) == -5
    assert positive[0] >= positive[1]
    assert negative[1] <= negative[2]


def test_sentence_deltas_sum_to_turn_delta() -> None:
    allocator = SentenceAnalysisAllocator()
    request = _request(with_trace=True)
    manifest, coverage = allocator.build_manifest(
        request.messages
    )

    result = allocator.build_analysis(
        request=request,
        semantic=_semantic(),
        manifest=manifest,
        coverage=coverage,
    )

    turn = result.turns[0]

    for field_name in RELATIONSHIP_FIELDS:
        assert sum(
            getattr(
                sentence.relationship_delta,
                field_name,
            )
            for sentence in turn.sentences
            if sentence.relationship_delta is not None
        ) == getattr(turn.relationship_delta, field_name)

    for field_name in DYNAMICS_FIELDS:
        assert sum(
            getattr(
                sentence.dynamics_delta,
                field_name,
            )
            for sentence in turn.sentences
            if sentence.dynamics_delta is not None
        ) == getattr(turn.dynamics_delta, field_name)

    assert (
        turn.sentences[-1].relationship_after
        == turn.relationship_after
    )

    for field_name in DYNAMICS_FIELDS:
        assert getattr(
            turn.sentences[-1].dynamics_after,
            field_name,
        ) == getattr(
            turn.dynamics_after,
            field_name,
        )


def test_analysis_removes_prescriptive_language() -> None:
    allocator = SentenceAnalysisAllocator()
    request = _request(with_trace=True)
    manifest, coverage = allocator.build_manifest(
        request.messages
    )

    result = allocator.build_analysis(
        request=request,
        semantic=_semantic(),
        manifest=manifest,
        coverage=coverage,
    )
    payload = result.model_dump_json(ensure_ascii=False)

    assert "建议" not in payload
    assert "下一步" not in payload
    assert "fix_direction" not in payload
    assert "improvement_action" not in payload
    assert "suggested_rewrite" not in payload


def test_missing_trace_does_not_fabricate_state_values() -> None:
    allocator = SentenceAnalysisAllocator()
    request = _request(with_trace=False)
    manifest, coverage = allocator.build_manifest(
        request.messages
    )

    result = allocator.build_analysis(
        request=request,
        semantic=_semantic(),
        manifest=manifest,
        coverage=coverage,
    )

    sentence = result.turns[0].sentences[0]
    assert sentence.state_change_source == "unavailable"
    assert sentence.relationship_delta is None
    assert sentence.dynamics_delta is None
    assert result.coverage.turn_trace_count == 0
