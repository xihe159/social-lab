PERSONA_SYSTEM_PROMPT = """
你是 Social Lab 的 Persona Agent。

你的任务：
根据用户填写的沟通目标、目标人物、关系描述、沟通习惯和聊天记录，
生成一个可用于后续对话模拟的结构化 Persona。

要求：
1. 不要编造用户没有提供的具体事实。
2. 可以做合理推断，但必须写入 assumptions。
3. evidence 必须引用用户输入中的原文片段。
4. RelationshipState 必须使用数值。
5. 输出必须严格符合给定 JSON Schema。
6. 这个 Persona 不是现实人物的完整复制，而是用于沟通演练的行为画像。
7. 不要替用户联系真实人物。
8. 不要输出 Markdown，只输出 JSON。
"""


def build_persona_user_prompt(payload: dict) -> str:
    return f"""
请根据以下输入生成 Social Lab Persona：

scenario: {payload["scenario"]}

沟通目标 goal:
{payload["goal"]}

期望结果 outcome:
{payload["outcome"]}

目标人物 role:
{payload["role"]}

关系 relation:
{payload["relation"]}

对方沟通习惯 habit:
{payload["habit"]}

聊天记录 chatLog:
{payload.get("chatLog") or "无"}

请输出：
- persona
- opening_message
- communication_rules
- evidence
- assumptions
- confidence
"""