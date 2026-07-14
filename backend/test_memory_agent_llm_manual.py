import asyncio

from app.agents.memory_agent import MemoryAgent
from app.schemas.memory import MemoryUpdateRequest


async def main():
    agent = MemoryAgent()

    request = MemoryUpdateRequest(
        scenario="work",
        goal="希望同事帮我一起推进项目",
        outcome="对方愿意帮忙看方案并给出反馈",
        persona={
            "name": "同事A",
            "relationship": "普通同事",
            "communication_style": "直接，关注效率和时间成本",
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

    response = await agent.run(request)

    print("memory_reason:", response.memory_reason)
    print("new_facts:", response.new_facts)
    print("next_focus:", response.next_focus)
    print("memory:", response.memory.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())