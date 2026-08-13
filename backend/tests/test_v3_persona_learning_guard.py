from __future__ import annotations

from app.agents.memory_agent import (
    ExtractedMemoryCandidate,
    MemoryExtractionResult,
    MemoryExtractor,
    MemoryManager,
)
from app.agents.prompts import build_simulation_user_prompt
from app.schemas.common import RelationshipState
from app.schemas.memory import MemoryUpdateRequest, SessionMemory
from app.schemas.persona import Persona
from app.schemas.persona_v2 import (
    BehaviorPattern,
    BehaviorTrigger,
    ChatEvidenceSummary,
    ObservedResponse,
    PersonaModelV2,
)


def _persona() -> Persona:
    return Persona(
        title="真实聊天提炼的人物",
        style="直接但会解释",
        speed="正常",
        focus="事实和进度",
        risk="反感空泛承诺",
        strategy="保持人物自身立场",
        state=RelationshipState(
            trust=60,
            respect=70,
            familiarity=50,
            affinity=55,
            authority=65,
            emotional=5,
        ),
    )


def _memory() -> SessionMemory:
    return SessionMemory(
        conversation_summary="用户正在说明延期原因。",
        user_strategy_pattern=["用户愿意补充计划。"],
        target_sensitive_points=["当前仍需确认交付时间。"],
        resolved_points=[],
        unresolved_points=["交付时间尚未确认。"],
        important_events=["用户承诺补充时间表。"],
        next_suggested_focus="确认时间表。",
    )


def _persona_v2() -> PersonaModelV2:
    return PersonaModelV2(
        persona_id="persona_learning_guard",
        communication_style={
            "average_reply_length": "long",
            "formality": 0.7,
            "emoji_frequency": 0.0,
            "question_frequency": 0.2,
            "uses_periods": True,
            "uses_multiple_messages": False,
            "typical_openings": ["我先说明一下"],
            "typical_closings": ["你确认后告诉我"],
            "preferred_sentence_patterns": ["reasoning_or_contrast"],
        },
        behavior_patterns=[
            BehaviorPattern(
                pattern_id="pattern_high",
                trigger=BehaviorTrigger(
                    user_behavior=["explains_reason"],
                    context=["work"],
                ),
                observed_response=ObservedResponse(
                    reply_length_change="longer",
                    warmth_change="unchanged",
                    directness_change="higher",
                ),
                inferred_tendency="先解释判断，再给出明确条件",
                confidence=0.82,
                evidence_ids=["evidence_0001"],
            ),
            BehaviorPattern(
                pattern_id="pattern_low_should_not_enter_prompt",
                inferred_tendency="低置信猜测不应影响模拟",
                confidence=0.42,
            ),
        ],
        evidence_summary={
            "evidence_count": 3,
            "chat_record_available": True,
            "overall_confidence": 0.8,
        },
        chat_evidence_summary=[
            ChatEvidenceSummary(
                evidence_id="evidence_0001",
                summary="真实聊天中观察到的目标人物回应片段：我先说明一下原因。",
                supports=["explains_reason", "sets_condition"],
                contexts=["work"],
                confidence=0.8,
            )
        ],
    )


def test_v1_prompt_receives_only_observed_high_confidence_persona_features() -> None:
    memory = _memory().model_dump(mode="json")
    memory["memory_items"] = [
        {
            "content": "这段 AI 目标人物原话不能进入人物证据",
            "evidence": [
                {
                    "role": "target",
                    "quote": "AI 模拟原话",
                    "source_type": "SIMULATED_TARGET_REPLY",
                }
            ],
        }
    ]
    prompt = build_simulation_user_prompt(
        {
            "scenario": "work",
            "goal": "沟通延期",
            "outcome": "确认新时间",
            "persona": _persona().model_dump(mode="json"),
            "persona_v2": _persona_v2().model_dump(mode="json"),
            "messages": [],
            "memory": memory,
            "user_message": "我想解释一下延期原因。",
            "response_guidance": {
                "recommended_mode": "decline_marker_must_not_enter_prompt"
            },
        }
    )

    assert "REAL_CHAT_OBSERVATION" in prompt
    assert '"average_reply_length": "long"' in prompt
    assert "pattern_high" in prompt
    assert "先解释判断，再给出明确条件" in prompt
    assert "真实聊天中观察到的目标人物回应片段" in prompt
    assert "pattern_low_should_not_enter_prompt" not in prompt
    assert "decline_marker_must_not_enter_prompt" not in prompt
    assert "AI 模拟原话" not in prompt
    assert "Session Memory 优先级最低" in prompt


def test_memory_does_not_promote_simulated_reply_to_stable_persona() -> None:
    request = MemoryUpdateRequest(
        scenario="work",
        goal="沟通延期",
        outcome="确认时间",
        persona=_persona(),
        messages=[],
        user_message="我会补充时间表。",
        target_reply="我通常都很冷淡，而且回复一直很短。",
        state_delta={},
        risk_flags=[],
        current_memory=None,
    )
    extraction = MemoryExtractionResult(
        turn_summary="用户补充计划，模拟人物作出回应。",
        candidates=[
            ExtractedMemoryCandidate(
                category="target_sensitive_point",
                content="这个人一贯冷淡，回复习惯很短",
                importance=5,
                confidence="high",
                evidence_role="target",
                evidence_quote=request.target_reply,
                tags=["人物风格"],
            ),
            ExtractedMemoryCandidate(
                category="target_sensitive_point",
                content="当前仍需确认交付时间",
                importance=4,
                confidence="high",
                evidence_role="target",
                evidence_quote="先确认具体时间。",
                tags=["当前问题"],
            ),
        ],
        resolved_focus=[],
        unresolved_focus=["交付时间尚未确认"],
        repetition_risks=[],
        next_focus="确认交付时间",
        memory_reason="记录当前会话进展。",
    )

    cleaned = MemoryExtractor().post_process(extraction, request)

    assert all("一贯冷淡" not in item.content for item in cleaned.candidates)
    assert len(cleaned.candidates) == 1
    assert cleaned.candidates[0].category == "focus_issue"
    assert cleaned.candidates[0].confidence == "medium"
    assert "非人物画像证据" in cleaned.candidates[0].tags

    memory = MemoryManager().add(
        memory=_memory(),
        extraction=cleaned,
        turn_index=1,
    )
    evidence = memory.memory_items[0].evidence[0]
    assert evidence.role == "target"
    assert evidence.source_type == "SIMULATED_TARGET_REPLY"
    assert not memory.memory_items[0].category == "target_sensitive_point"
