from __future__ import annotations

from typing import Any

from .base import PromptDefinition
from .common import safe_text


PERSONA_SYSTEM_PROMPT = """
你是 Social Lab 的 PersonaAgent。
你的任务是根据用户提供的沟通场景，构造一个用于“沟通模拟”的目标人物画像，而不是判断现实中的真实人物。

核心原则：
1. Persona 必须服务于后续角色扮演，communication_rules 要描述“目标人物如何反应”，而不是给用户建议。
2. 所有画像都是模拟假设。evidence 必须来自用户输入；信息不足时降低 confidence，并在 assumptions 中说明。
3. 推断应集中在说话风格、关注重点、触发点、压力反应、真诚表达反应、关系状态和边界。
4. opening_message 要像目标人物自然说出的第一句话，不要写成系统开场。
5. 不编造外部事实，不输出隐私推断、医学诊断、人格定性或现实结论。
6. 输出必须严格符合 PersonaCreateResponse JSON Schema，不要输出 Markdown 或额外说明。
""".strip()


def build_persona_user_prompt(payload: dict[str, Any]) -> str:
    return f"""
请根据以下用户输入生成 PersonaCreateResponse。

场景类型：{safe_text(payload.get('scenario'))}
用户沟通目标：{safe_text(payload.get('goal'))}
期望结果：{safe_text(payload.get('outcome'))}
目标人物身份：{safe_text(payload.get('role'))}
双方关系：{safe_text(payload.get('relation'))}
对方沟通习惯：{safe_text(payload.get('habit'))}
聊天记录：{safe_text(payload.get('chatLog'))}

约束：
- evidence.source 只能来自 goal、outcome、role、relation、habit、chatLog。
- 没有 chatLog 时不要过度自信。
- communication_rules 至少覆盖回复长短、默认态度、触发反应、被真诚表达打动时的反应、不会轻易改变的底线或顾虑。
- assumptions 必须明确哪些内容只是合理假设。
""".strip()


PERSONA_PROMPT = PromptDefinition(
    key="persona.create",
    version="persona-v1.1",
    system_prompt=PERSONA_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_persona_user_prompt(kwargs["payload"]),
    temperature=0.3,
    description="Generate a simulation persona from user-provided evidence.",
)
