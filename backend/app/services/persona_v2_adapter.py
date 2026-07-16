from __future__ import annotations

from app.schemas.common import ScenarioKey
from app.schemas.persona import Persona
from app.schemas.persona_v2 import (
    BasicProfile,
    CommunicationStyle,
    DyadicProfile,
    EvidenceSummary,
    PersonaModelV2,
    StableTraits,
)


def compile_legacy_persona(
    persona: Persona,
    *,
    persona_id: str,
    role: str = "",
    relation: str = "",
    scenario: ScenarioKey | None = None,
    evidence_count: int = 0,
    chat_record_available: bool = False,
    confidence: float = 0.4,
) -> PersonaModelV2:
    """Convert the current V1 persona into a validated Persona Model V2."""

    text = " ".join(
        [
            persona.title,
            persona.style,
            persona.focus,
            persona.risk,
            persona.strategy,
            role,
            relation,
        ]
    ).lower()

    authority = _unit(persona.state.authority)
    familiarity = _unit(persona.state.familiarity)
    affinity = _unit(persona.state.affinity)
    psychological_safety = _clamp((persona.state.emotional + 100) / 200)

    basic_profile = BasicProfile(
        name="",
        role=role.strip() or _default_role(scenario),
        relationship_type=relation.strip() or _default_relationship(scenario),
        power_dynamic=_power_dynamic(authority),
    )

    stable_traits = StableTraits(
        directness=_dimension(text, 0.5, ["直接", "严厉", "强势"], ["委婉", "温和"]),
        emotional_expressiveness=_dimension(
            text, 0.45, ["情绪敏感", "感性", "外向"], ["理性", "克制", "内向"]
        ),
        conflict_avoidance=_dimension(
            text, 0.45, ["回避", "避免冲突"], ["强势", "直接", "严厉"]
        ),
        need_for_control=_dimension(
            text, max(0.4, authority), ["控制", "强势", "严格"], ["随和", "宽松"]
        ),
        tolerance_for_ambiguity=_dimension(
            text, 0.5, ["包容", "灵活"], ["结果导向", "清晰", "具体", "效率"]
        ),
        sensitivity_to_disrespect=_dimension(
            text, max(0.5, authority), ["尊重", "礼貌", "冒犯", "权威"], ["随意"]
        ),
        sensitivity_to_rejection=_dimension(
            text, 0.5, ["敏感", "拒绝"], ["理性", "独立"]
        ),
        patience_for_explanation=_dimension(
            text, 0.5, ["耐心", "愿意听"], ["效率", "不耐烦", "简洁"]
        ),
        preference_for_efficiency=_dimension(
            text, 0.55, ["效率", "结果导向", "简洁"], ["慢慢", "详细交流"]
        ),
        need_for_reassurance=_dimension(
            text, 0.4, ["敏感", "确认", "安慰"], ["独立", "理性"]
        ),
        boundary_strictness=_dimension(
            text, max(0.45, authority), ["边界", "严格", "原则"], ["随和"]
        ),
        forgiveness_speed=_dimension(
            text, 0.5, ["温和", "包容"], ["记仇", "严格", "敏感"]
        ),
        responsibility_orientation=_dimension(
            text, 0.55, ["责任", "结果导向", "导师", "领导"], ["随意"]
        ),
    )

    communication_style = CommunicationStyle(
        average_reply_length=_reply_length(text),
        formality=_clamp(max(0.4, authority)),
        emoji_frequency=0.0,
        question_frequency=0.6 if _contains_any(text, ["提问", "追问", "询问"]) else 0.5,
        uses_periods=True,
        uses_multiple_messages=False,
    )

    dyadic_profile = DyadicProfile(
        trust=_unit(persona.state.trust),
        respect=_unit(persona.state.respect),
        warmth=affinity,
        expectation=_clamp((_unit(persona.state.respect) + authority) / 2),
        patience=0.6,
        psychological_safety=psychological_safety,
        communication_distance=_clamp(1 - familiarity),
    )

    return PersonaModelV2(
        persona_id=persona_id.strip(),
        basic_profile=basic_profile,
        stable_traits=stable_traits,
        communication_style=communication_style,
        dyadic_profile=dyadic_profile,
        evidence_summary=EvidenceSummary(
            evidence_count=max(0, int(evidence_count)),
            chat_record_available=chat_record_available,
            overall_confidence=_clamp(confidence),
        ),
    )


def _dimension(
    text: str,
    default: float,
    high_keywords: list[str],
    low_keywords: list[str],
) -> float:
    if _contains_any(text, high_keywords):
        return _clamp(max(default, 0.75))
    if _contains_any(text, low_keywords):
        return _clamp(min(default, 0.3))
    return _clamp(default)


def _reply_length(text: str) -> str:
    if _contains_any(text, ["简洁", "短回复", "话少", "效率"]):
        return "short"
    if _contains_any(text, ["详细", "长回复", "解释充分"]):
        return "long"
    return "medium"


def _default_role(scenario: ScenarioKey | None) -> str:
    return {
        "advisor": "导师",
        "work": "工作关系对象",
        "social": "社交关系对象",
    }.get(scenario, "目标人物")


def _default_relationship(scenario: ScenarioKey | None) -> str:
    return {
        "advisor": "师生关系",
        "work": "工作关系",
        "social": "社交关系",
    }.get(scenario, "未明确关系")


def _power_dynamic(authority: float) -> str:
    if authority >= 0.7:
        return "target_high_authority"
    if authority >= 0.45:
        return "target_moderate_authority"
    return "relatively_equal"


def _unit(value: int) -> float:
    return _clamp(value / 100)


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)
