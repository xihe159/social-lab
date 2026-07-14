from app.agents.memory_agent import (
    MemoryManager,
    MemoryExtractionResult,
    ExtractedMemoryCandidate,
)
from app.schemas.memory import MemoryUpdateRequest


def main():
    request = MemoryUpdateRequest(
        scenario="work",
        goal="希望同事帮我一起推进项目",
        outcome="对方愿意协助，并明确下一步安排",
        persona={
            "name": "同事A",
            "relationship": "普通同事",
            "communication_style": "直接，关注时间成本",
        },
        messages=[
            {"role": "user", "content": "你今天必须帮我看完这个方案。"},
            {"role": "target", "content": "我今天不一定有时间，你能不能先说重点？"},
        ],
        user_message="你今天必须帮我看完这个方案。",
        target_reply="我今天不一定有时间，你能不能先说重点？",
        state_delta={
            "trust": -1,
            "respect": -1,
            "affinity": -1,
            "emotional_tension": 2,
        },
        risk_flags=["语气施压", "对方时间成本未被照顾"],
        current_memory=None,
    )

    extraction = MemoryExtractionResult(
        turn_summary="用户要求同事当天看完方案，目标人物表现出时间成本顾虑。",
        candidates=[
            ExtractedMemoryCandidate(
                category="user_dialogue_pattern",
                content="用户表达中存在较强催促和命令感，容易给对方造成压力。",
                importance=5,
                confidence="high",
                evidence_role="user",
                evidence_quote="你今天必须帮我看完这个方案。",
                tags=["催促", "命令感", "压力"],
            ),
            ExtractedMemoryCandidate(
                category="target_sensitive_point",
                content="目标人物对时间成本较敏感，希望用户先说明重点。",
                importance=5,
                confidence="high",
                evidence_role="target",
                evidence_quote="我今天不一定有时间，你能不能先说重点？",
                tags=["时间成本", "重点", "协作"],
            ),
            ExtractedMemoryCandidate(
                category="focus_issue",
                content="当前对话的核心问题是用户没有降低对方的时间成本。",
                importance=5,
                confidence="high",
                evidence_role="target",
                evidence_quote="你能不能先说重点？",
                tags=["聚焦问题", "时间成本"],
            ),
            ExtractedMemoryCandidate(
                category="key_info_repetition_risk",
                content="如果用户继续重复要求对方帮忙，而不说明重点，会加重对方抗拒。",
                importance=4,
                confidence="medium",
                evidence_role="target",
                evidence_quote="我今天不一定有时间",
                tags=["重复风险", "抗拒"],
            ),
        ],
        resolved_focus=[],
        unresolved_focus=["用户还没有说明方案重点和需要对方投入的具体时间。"],
        repetition_risks=["用户可能继续重复要求对方帮忙，但没有回应对方时间成本顾虑。"],
        next_focus="下一轮应先说明方案重点，并降低对方需要投入的时间成本。",
        memory_reason="本轮对话暴露出用户表达压力较高，以及目标人物对时间成本敏感。",
    )

    manager = MemoryManager()
    memory = manager.update(request=request, extraction=extraction)

    print("memory_version:", memory.memory_version)
    print("last_turn_index:", memory.last_turn_index)
    print("conversation_summary:", memory.conversation_summary)
    print("user_strategy_pattern:", memory.user_strategy_pattern)
    print("target_sensitive_points:", memory.target_sensitive_points)
    print("active_focus_issues:", memory.active_focus_issues)
    print("key_info_repetition_risks:", memory.key_info_repetition_risks)
    print("next_suggested_focus:", memory.next_suggested_focus)
    print("memory_items_count:", len(memory.memory_items))

    for item in memory.memory_items:
        print("----")
        print("id:", item.memory_id)
        print("category:", item.category)
        print("content:", item.content)
        print("importance:", item.importance)
        print("seen_count:", item.seen_count)
        print("evidence:", [e.quote for e in item.evidence])


if __name__ == "__main__":
    main()

