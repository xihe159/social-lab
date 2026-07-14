from app.agents.memory_agent import MemoryManager
from app.schemas.memory import (
    SessionMemory,
    MemoryItem,
    MemoryEvidence,
)


def build_test_memory() -> SessionMemory:
    """
    构造一份不依赖 LLM 的测试 memory。
    用来专门测试 MemorySelector.search()。
    """

    return SessionMemory(
        conversation_summary="用户正在尝试说服同事帮忙看方案。",
        user_strategy_pattern=[
            "用户表达中存在催促感。",
            "用户开始尝试降低对方时间成本。",
        ],
        target_sensitive_points=[
            "目标人物对时间成本较敏感。",
            "目标人物希望用户先说明重点。",
        ],
        resolved_points=[
            "用户已经开始把请求缩小为两个重点。",
        ],
        unresolved_points=[
            "用户还没有明确两个重点分别是什么。",
        ],
        important_events=[
            "用户要求同事今天看完方案，对方表达时间顾虑。",
        ],
        next_suggested_focus="下一轮应直接列出两个重点，并说明需要对方判断什么。",
        memory_version="v2",
        last_turn_index=2,
        active_focus_issues=[
            "用户需要明确方案的两个重点。",
            "用户需要降低对方时间成本。",
        ],
        key_info_repetition_risks=[
            "如果用户继续重复要求帮忙，而不说明重点，会增加对方抗拒。",
        ],
        forgotten_items=[],
        memory_items=[
            MemoryItem(
                memory_id="mem_user_pressure",
                category="user_dialogue_pattern",
                content="用户表达中存在较强催促和命令感，容易给对方造成压力。",
                importance=5,
                confidence="high",
                status="active",
                evidence=[
                    MemoryEvidence(
                        turn_index=1,
                        role="user",
                        quote="你今天必须帮我看完这个方案。",
                    )
                ],
                tags=["催促", "命令感", "压力"],
                first_seen_turn=1,
                last_seen_turn=1,
                seen_count=1,
            ),
            MemoryItem(
                memory_id="mem_target_time_cost",
                category="target_sensitive_point",
                content="目标人物对时间成本较敏感，希望用户先说明重点。",
                importance=5,
                confidence="high",
                status="active",
                evidence=[
                    MemoryEvidence(
                        turn_index=1,
                        role="target",
                        quote="我今天不一定有时间，你能不能先说重点？",
                    )
                ],
                tags=["时间成本", "重点", "效率"],
                first_seen_turn=1,
                last_seen_turn=2,
                seen_count=2,
            ),
            MemoryItem(
                memory_id="mem_focus_issue",
                category="focus_issue",
                content="当前对话的核心问题是用户没有充分降低对方的时间成本。",
                importance=5,
                confidence="high",
                status="active",
                evidence=[
                    MemoryEvidence(
                        turn_index=1,
                        role="target",
                        quote="你能不能先说重点？",
                    )
                ],
                tags=["聚焦问题", "时间成本", "下一轮重点"],
                first_seen_turn=1,
                last_seen_turn=2,
                seen_count=2,
            ),
            MemoryItem(
                memory_id="mem_repetition_risk",
                category="key_info_repetition_risk",
                content="如果用户继续重复要求对方帮忙，而不说明重点，会加重对方抗拒。",
                importance=4,
                confidence="medium",
                status="active",
                evidence=[
                    MemoryEvidence(
                        turn_index=1,
                        role="target",
                        quote="我今天不一定有时间",
                    )
                ],
                tags=["重复风险", "抗拒", "重点缺失"],
                first_seen_turn=1,
                last_seen_turn=1,
                seen_count=1,
            ),
            MemoryItem(
                memory_id="mem_forgotten_test",
                category="important_event",
                content="这是一条已经被遗忘的旧记忆，不应该被搜索出来。",
                importance=5,
                confidence="high",
                status="forgotten",
                evidence=[
                    MemoryEvidence(
                        turn_index=1,
                        role="user",
                        quote="旧信息",
                    )
                ],
                tags=["时间成本", "旧信息"],
                first_seen_turn=1,
                last_seen_turn=1,
                seen_count=1,
            ),
        ],
    )


def print_results(title: str, results):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    if not results:
        print("没有搜索结果")
        return

    for index, item in enumerate(results, start=1):
        print(f"{index}. [{item.category}] {item.content}")
        print(f"   importance={item.importance}, seen_count={item.seen_count}, last_seen_turn={item.last_seen_turn}")
        print(f"   tags={item.tags}")
        print(f"   evidence={[e.quote for e in item.evidence]}")
        print()


def main():
    memory = build_test_memory()

    manager = MemoryManager()
    selector = manager.selector

    # 测试 1：按关键词搜索
    results = selector.search(
        memory,
        query="时间成本",
        limit=5,
    )
    print_results("测试 1：搜索关键词『时间成本』", results)

    # 测试 2：按另一个关键词搜索
    results = selector.search(
        memory,
        query="催促",
        limit=5,
    )
    print_results("测试 2：搜索关键词『催促』", results)

    # 测试 3：只搜索目标人物敏感点
    results = selector.search(
        memory,
        query="时间成本",
        category="target_sensitive_point",
        limit=5,
    )
    print_results("测试 3：搜索『时间成本』，并限制 category=target_sensitive_point", results)

    # 测试 4：只搜索重复风险
    results = selector.search(
        memory,
        query="重复",
        category="key_info_repetition_risk",
        limit=5,
    )
    print_results("测试 4：搜索『重复』，并限制 category=key_info_repetition_risk", results)

    # 测试 5：测试 forgotten 是否被排除
    results = selector.search(
        memory,
        query="旧信息",
        limit=5,
    )
    print_results("测试 5：搜索『旧信息』，确认 forgotten 记忆不会出现", results)

    # 测试 6：不传 query，只按重要度和最近轮次返回
    results = selector.search(
        memory,
        limit=5,
    )
    print_results("测试 6：不传 query，返回当前最重要的记忆", results)


if __name__ == "__main__":
    main()