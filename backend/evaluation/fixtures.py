from __future__ import annotations

from app.schemas.persona_v2 import (
    BasicProfile,
    CommunicationStyle,
    DyadicProfile,
    PersonaModelV2,
    StableTraits,
)


def persona_a_direct_advisor() -> PersonaModelV2:
    return PersonaModelV2(
        persona_id="eval_persona_a",
        basic_profile=BasicProfile(
            role="导师",
            relationship_type="师生关系",
            power_dynamic="target_high_authority",
        ),
        stable_traits=StableTraits(
            directness=0.9,
            conflict_avoidance=0.15,
            responsibility_orientation=0.95,
            preference_for_efficiency=0.9,
            boundary_strictness=0.8,
            patience_for_explanation=0.35,
        ),
        communication_style=CommunicationStyle(
            average_reply_length="short",
            formality=0.85,
            emoji_frequency=0.0,
            question_frequency=0.45,
            uses_periods=True,
            typical_openings=["具体说"],
            typical_closings=["按时间完成。"],
            preferred_sentence_patterns=["direct_instruction"],
        ),
        dyadic_profile=DyadicProfile(
            trust=0.6,
            respect=0.75,
            warmth=0.4,
            expectation=0.85,
            patience=0.45,
            communication_distance=0.75,
        ),
    )


def persona_b_gentle_avoidant_friend() -> PersonaModelV2:
    return PersonaModelV2(
        persona_id="eval_persona_b",
        basic_profile=BasicProfile(
            role="朋友",
            relationship_type="朋友关系",
            power_dynamic="relatively_equal",
        ),
        stable_traits=StableTraits(
            directness=0.25,
            emotional_expressiveness=0.65,
            conflict_avoidance=0.9,
            responsibility_orientation=0.55,
            boundary_strictness=0.35,
            patience_for_explanation=0.75,
        ),
        communication_style=CommunicationStyle(
            average_reply_length="medium",
            formality=0.25,
            emoji_frequency=0.2,
            question_frequency=0.55,
            uses_periods=False,
            typical_openings=["嗯嗯"],
            typical_closings=["晚点再聊吧"],
            preferred_sentence_patterns=["softened_suggestion"],
        ),
        dyadic_profile=DyadicProfile(
            trust=0.75,
            respect=0.65,
            warmth=0.8,
            expectation=0.45,
            patience=0.75,
            communication_distance=0.2,
        ),
    )


def persona_c_sensitive_partner() -> PersonaModelV2:
    return PersonaModelV2(
        persona_id="eval_persona_c",
        basic_profile=BasicProfile(
            role="伴侣",
            relationship_type="亲密关系",
            power_dynamic="relatively_equal",
        ),
        stable_traits=StableTraits(
            directness=0.55,
            emotional_expressiveness=0.9,
            conflict_avoidance=0.45,
            sensitivity_to_rejection=0.95,
            need_for_reassurance=0.9,
            boundary_strictness=0.55,
            patience_for_explanation=0.6,
        ),
        communication_style=CommunicationStyle(
            average_reply_length="long",
            formality=0.1,
            emoji_frequency=0.35,
            question_frequency=0.75,
            uses_periods=False,
            typical_openings=["你怎么了"],
            typical_closings=["你和我说清楚好吗"],
            preferred_sentence_patterns=["emotion_then_question"],
        ),
        dyadic_profile=DyadicProfile(
            trust=0.7,
            respect=0.65,
            warmth=0.9,
            expectation=0.8,
            patience=0.6,
            psychological_safety=0.55,
            communication_distance=0.05,
        ),
    )


def fixed_personas() -> tuple[PersonaModelV2, PersonaModelV2, PersonaModelV2]:
    return (
        persona_a_direct_advisor(),
        persona_b_gentle_avoidant_friend(),
        persona_c_sensitive_partner(),
    )


REAL_CHAT_FIXTURE = """2026-06-01 09:00 我：老师，材料来不及准备，能否延期一天？
2026-06-01 09:05 导师：具体还缺什么？今天先把已有材料发我。
2026-06-05 10:00 我：这是我的问题，我会负责补齐。
2026-06-05 10:03 导师：可以，但不要再拖了。
2026-06-10 11:00 我：材料已经补齐，麻烦您确认。
2026-06-10 11:10 导师：好的，我看到了。以后提前准备。"""

