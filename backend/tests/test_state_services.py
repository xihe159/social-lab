from __future__ import annotations

from app.schemas.common import RelationshipState
from app.schemas.dynamics import (
    ConversationDynamics,
    ConversationDynamicsDelta,
    ConversationDynamicsUpdate,
)
from app.schemas.session import StateDelta
from app.schemas.state import StateEvaluateRequest, StateEvaluationResponse
from app.services.state import StateResultProcessor


def build_baseline() -> ConversationDynamics:
    return ConversationDynamics(
        atmosphere_score=60,
        pace_score=55,
        pressure_level=30,
        clarity_score=50,
        responsiveness_score=50,
        progress_score=35,
        repairability_score=60,
        boundary_score=60,
        rhythm_label="balanced",
        atmosphere_label="neutral",
        recommended_next_move="clarify",
        dynamics_reason="测试基线",
    )


def build_request(
    *,
    user_message: str,
    target_reply: str,
) -> StateEvaluateRequest:
    # 这些单元测试只覆盖确定性规则，不读取 persona 和 messages。
    # model_construct 可避免为了规则测试构造完整画像。
    return StateEvaluateRequest.model_construct(
        scenario="work",
        goal="推进沟通",
        outcome="达成下一步安排",
        persona=None,
        messages=[],
        user_message=user_message,
        target_reply=target_reply,
        current_state=RelationshipState(
            trust=60,
            respect=60,
            familiarity=40,
            affinity=50,
            authority=50,
            emotional=0,
        ),
        simulation_attitude="谨慎",
        simulation_emotion="平静",
        perceived_user_tone="中性",
        current_dynamics=build_baseline(),
    )


def build_model_result() -> StateEvaluationResponse:
    baseline = build_baseline()
    return StateEvaluationResponse(
        state_delta=StateDelta(
            trust=0,
            respect=0,
            familiarity=0,
            affinity=0,
            authority=0,
            emotional=0,
        ),
        state_reason="模型初始判断",
        positive_signals=[],
        negative_signals=[],
        risk_flags=[],
        dynamics_update=ConversationDynamicsUpdate(
            dynamics_delta=ConversationDynamicsDelta(
                atmosphere_score=0,
                pace_score=0,
                pressure_level=0,
                clarity_score=0,
                responsiveness_score=0,
                progress_score=0,
                repairability_score=0,
                boundary_score=0,
            ),
            updated_dynamics=baseline.model_copy(
                update={"dynamics_reason": "模型给出的解释。"}
            ),
            control_suggestions=["模型生成的建议会被确定性建议替换"],
        ),
    )


def test_pressure_and_refusal_are_guarded() -> None:
    processor = StateResultProcessor()
    request = build_request(
        user_message="你必须马上答复，否则我会继续催你。",
        target_reply="不行，我不想继续，到此为止。",
    )

    result = processor.process(
        result=build_model_result(),
        request=request,
    )

    assert result.state_delta.trust <= -1
    assert result.state_delta.respect <= -1
    assert result.state_delta.affinity <= -1
    assert result.state_delta.emotional <= -1

    delta = result.dynamics_update.dynamics_delta
    assert delta.pressure_level >= 6
    assert delta.boundary_score <= -4
    assert delta.progress_score <= -5

    updated = result.dynamics_update.updated_dynamics
    assert updated.atmosphere_label == "blocked"
    assert updated.recommended_next_move == "pause"
    assert "表达中存在催促、施压或命令感" in result.risk_flags
    assert "目标人物已出现明确拒绝或停止推进信号" in result.risk_flags


def test_giving_space_reduces_pressure() -> None:
    processor = StateResultProcessor()
    request = build_request(
        user_message=(
            "我会补充完整方案，你不用马上回答，"
            "如果不合适也没关系。"
        ),
        target_reply="可以考虑，你先把具体安排发给我。",
    )

    result = processor.process(
        result=build_model_result(),
        request=request,
    )

    delta = result.dynamics_update.dynamics_delta
    assert delta.boundary_score >= 3
    assert delta.pressure_level <= -3
    assert delta.clarity_score >= 3
    assert delta.responsiveness_score >= 2
    assert delta.progress_score >= 1

    assert (
        "表达为对方保留了考虑、拒绝或延后回应的空间"
        in result.positive_signals
    )

    updated = result.dynamics_update.updated_dynamics
    assert updated.pressure_level == 30 + delta.pressure_level
    assert updated.boundary_score == 60 + delta.boundary_score
    assert 1 <= len(result.dynamics_update.control_suggestions) <= 3


def test_model_deltas_are_clamped_before_rebuild() -> None:
    processor = StateResultProcessor()
    request = build_request(
        user_message="我会在明天提交完整方案。",
        target_reply="可以。",
    )
    result = build_model_result()

    # model_construct 模拟不可信的模型输出，绕过 Pydantic 字段范围校验。
    result.state_delta = StateDelta.model_construct(
        trust=100,
        respect=100,
        familiarity=100,
        affinity=100,
        authority=100,
        emotional=100,
    )
    result.dynamics_update.dynamics_delta = (
        ConversationDynamicsDelta.model_construct(
            atmosphere_score=100,
            pace_score=100,
            pressure_level=100,
            clarity_score=100,
            responsiveness_score=100,
            progress_score=100,
            repairability_score=100,
            boundary_score=100,
        )
    )

    processed = processor.process(result=result, request=request)

    assert processed.state_delta.trust == 6
    assert processed.state_delta.respect == 6
    assert processed.state_delta.familiarity == 4
    assert processed.state_delta.affinity == 5
    assert processed.state_delta.authority == 2
    assert processed.state_delta.emotional == 6

    delta = processed.dynamics_update.dynamics_delta
    assert delta.atmosphere_score == 10
    assert delta.pressure_level == 12
    assert processed.dynamics_update.updated_dynamics.atmosphere_score == 70
    assert processed.dynamics_update.updated_dynamics.pressure_level == 42
