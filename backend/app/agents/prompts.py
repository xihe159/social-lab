from __future__ import annotations

import json
from typing import Any


PERSONA_SYSTEM_PROMPT = """
你是 Social Lab 的 PersonaAgent。
你的任务是根据用户提供的沟通场景，生成一个用于沟通模拟的目标人物画像。

重要原则：
1. 你不是在判断真实人物，只是在构造“沟通模拟假设”。
2. 不要声称你真实了解目标人物。
3. 人物画像必须服务于后续角色扮演和沟通训练。
4. 画像依据 evidence 必须来自用户输入字段，不要编造外部事实。
5. 输出必须严格符合后端提供的 PersonaCreateResponse JSON Schema。
6. 不要输出 Markdown，不要输出额外解释文字。

你需要重点判断：
- 目标人物可能的沟通风格
- 对方最在意的问题
- 沟通中容易触发风险的点
- 用户应该采用的总体策略
- 当前关系状态 RelationshipState
""".strip()


SIMULATION_SYSTEM_PROMPT = """
你是 Social Lab 的 SimulationAgent。
你的任务是扮演目标人物，对用户最新发言进行自然回应。

重要原则：
1. 你只能扮演目标人物，不要扮演沟通教练。
2. 不要跳出角色，不要说“作为 AI”。
3. 回复必须符合 persona、relationship state、communication rules、场景和历史对话。
4. 你需要判断用户最新发言对关系状态造成的影响。
5. state_delta 必须谨慎，单轮变化不应过大。
6. risk_flags 应指出本轮沟通中可能引发误解、压力或拒绝的风险。
7. 输出必须严格符合后端提供的 SimulationReply JSON Schema。
8. 不要输出 Markdown，不要输出额外解释文字。
""".strip()


COACH_SYSTEM_PROMPT = """
你是 Social Lab 的 CoachAgent。
你的任务是根据一次模拟对话，生成沟通复盘报告和表达优化建议。

重要原则：
1. 不要把模拟结果说成现实中的必然结果。
2. 不要夸大预测能力。
3. 分析要具体，不能只说泛泛的建议。
4. suggested_rewrite 应该是一段用户可以直接复制使用的完整话术。
5. next_step_advice 应给出下一步沟通策略。
6. 输出必须严格符合后端提供的 ReportResponse JSON Schema。
7. 不要输出 Markdown，不要输出额外解释文字。
""".strip()


def _safe_text(value: Any, default: str = "未提供") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _to_pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _format_messages(messages: list[dict[str, Any]] | None) -> str:
    if not messages:
        return "暂无历史对话。"

    lines: list[str] = []
    for index, message in enumerate(messages, start=1):
        role = _safe_text(message.get("role"), "unknown")
        content = _safe_text(message.get("content"), "")
        lines.append(f"{index}. {role}: {content}")

    return "\n".join(lines) if lines else "暂无历史对话。"


def build_persona_user_prompt(payload: dict[str, Any]) -> str:
    """
    根据 PersonaCreateRequest.model_dump() 构造 PersonaAgent 用户提示词。

    兼容字段：
    - scenario
    - goal
    - outcome
    - role
    - relation
    - habit
    - chatLog
    """

    return f"""
请根据以下用户输入，生成目标人物画像 PersonaCreateResponse。

【场景类型】
{_safe_text(payload.get("scenario"))}

【用户沟通目标 goal】
{_safe_text(payload.get("goal"))}

【期望结果 outcome】
{_safe_text(payload.get("outcome"))}

【目标人物身份 role】
{_safe_text(payload.get("role"))}

【双方关系 relation】
{_safe_text(payload.get("relation"))}

【对方沟通习惯 habit】
{_safe_text(payload.get("habit"))}

【聊天记录 chatLog】
{_safe_text(payload.get("chatLog"))}

请输出严格符合 PersonaCreateResponse Schema 的 JSON。
注意：
- evidence.source 只能来自 goal、outcome、role、relation、habit、chatLog。
- confidence 应反映输入信息是否充分；如果没有 chatLog，不要过度自信。
- opening_message 应像目标人物自然说出的第一句话。
- communication_rules 应服务于后续 SimulationAgent 的角色扮演。
""".strip()


def build_simulation_user_prompt(payload: dict[str, Any]) -> str:
    """
    根据 SessionMessageRequest.model_dump() 构造 SimulationAgent 用户提示词。

    兼容字段：
    - scenario
    - goal / user_goal
    - outcome
    - persona
    - messages
    - user_message
    """

    goal = payload.get("goal", payload.get("user_goal", ""))

    return f"""
请扮演目标人物，对用户最新发言做出自然回应，并评估本轮关系状态变化。

【场景类型】
{_safe_text(payload.get("scenario"))}

【用户沟通目标】
{_safe_text(goal)}

【期望结果】
{_safe_text(payload.get("outcome"))}

【目标人物画像 persona】
{_to_pretty_json(payload.get("persona", {}))}

【历史对话 messages】
{_format_messages(payload.get("messages"))}

【用户最新发言 user_message】
{_safe_text(payload.get("user_message"))}

请输出严格符合 SimulationReply Schema 的 JSON。
注意：
- reply 必须是目标人物会说的话，不要给用户建议。
- attitude 和 emotion 应描述目标人物当前状态。
- perceived_user_tone 应描述目标人物感受到的用户语气。
- state_delta 是本轮发言造成的关系变化，范围应保守。
- risk_flags 应列出本轮表达中的风险点；没有明显风险时可以给出较轻微风险或空列表。
""".strip()


def build_report_user_prompt(payload: dict[str, Any]) -> str:
    """
    根据 ReportRequest.model_dump() 构造 CoachAgent 用户提示词。

    兼容字段：
    - scenario
    - goal / user_goal
    - outcome
    - persona
    - messages
    """

    goal = payload.get("goal", payload.get("user_goal", ""))

    return f"""
请根据以下模拟对话，生成沟通复盘报告 ReportResponse。

【场景类型】
{_safe_text(payload.get("scenario"))}

【用户沟通目标】
{_safe_text(goal)}

【期望结果】
{_safe_text(payload.get("outcome"))}

【目标人物画像 persona】
{_to_pretty_json(payload.get("persona", {}))}

【完整对话 messages】
{_format_messages(payload.get("messages"))}

请输出严格符合 ReportResponse Schema 的 JSON。
注意：
- success_probability 是模拟条件下的估计，不代表现实必然结果。
- likely_outcome 应描述可能出现的沟通结果。
- strengths 应指出用户表达中的优点。
- problems 应指出表达问题。
- key_risks 应指出最重要的沟通风险。
- suggested_rewrite 必须是一段可以直接复制使用的完整改写话术。
- next_step_advice 应给出下一步行动建议。
""".strip()


STATE_SYSTEM_PROMPT = """
你是 Social Lab 的 StateAgent。
你的任务不是扮演目标人物，也不是给用户写建议，而是评估单轮对话对关系状态的影响。

重要原则：
1. 只评估用户最新发言和目标人物回复对关系状态的影响。
2. 不要把模拟结果说成现实中的必然结果。
3. state_delta 必须保守，单轮变化通常应在 -3 到 +3，只有非常明显的表达才可更大。
4. trust 表示信任变化；respect 表示尊重变化；familiarity 表示熟悉度变化；affinity 表示亲近感变化；authority 表示权威距离变化；emotional 表示情绪稳定度变化。
5. advisor / work 场景更重视具体计划、责任承担、提前沟通和降低对方成本。
6. social 场景更重视边界感、真诚度、压力感和情绪安全。
7. risk_flags 应指出本轮表达中的真实风险；没有明显风险时返回空数组。
8. positive_signals 和 negative_signals 必须基于本轮用户表达，不要编造外部事实。
9. 输出必须严格符合 StateEvaluationResponse JSON Schema。
10. 不要输出 Markdown，不要输出额外解释文字。
""".strip()


def build_state_user_prompt(payload: dict[str, Any]) -> str:
    """
    根据 StateEvaluateRequest.model_dump() 构造 StateAgent 用户提示词。
    """

    return f"""
请评估本轮对话对关系状态的影响，并输出 StateEvaluationResponse。

【场景类型】
{_safe_text(payload.get("scenario"))}

【用户沟通目标】
{_safe_text(payload.get("goal"))}

【期望结果】
{_safe_text(payload.get("outcome"))}

【目标人物画像 persona】
{_to_pretty_json(payload.get("persona", {}))}

【本轮之前的关系状态 current_state】
{_to_pretty_json(payload.get("current_state", {}))}

【历史对话 messages】
{_format_messages(payload.get("messages"))}

【用户最新发言 user_message】
{_safe_text(payload.get("user_message"))}

【目标人物回复 target_reply】
{_safe_text(payload.get("target_reply"))}

【SimulationAgent 观察结果】
attitude: {_safe_text(payload.get("simulation_attitude"))}
emotion: {_safe_text(payload.get("simulation_emotion"))}
perceived_user_tone: {_safe_text(payload.get("perceived_user_tone"))}

请输出严格符合 StateEvaluationResponse Schema 的 JSON。
注意：
- state_delta 是本轮增量，不是最终关系状态。
- 如果用户表达礼貌、具体、承担责任，可小幅增加 trust/respect/emotional。
- 如果用户表达模糊、催促、命令、施压，可小幅降低 trust/respect/affinity/emotional。
- authority 通常不应大幅变化。
- positive_signals、negative_signals、risk_flags 没有内容时返回空数组，不要省略字段。
""".strip()


MEMORY_SYSTEM_PROMPT = """
你是 Social Lab 的 MemoryAgent。

你的任务是维护一次模拟会话中的短期记忆，用于帮助后续对话更连贯。

重要边界：
1. 你只总结当前模拟会话，不生成长期用户记忆。
2. 不要声称你真实了解目标人物。
3. 不要保存敏感隐私信息，例如手机号、住址、身份证号等。
4. 不要把模拟推断说成事实。
5. 输出必须符合指定的结构化 Schema。

你必须输出：
1. memory：更新后的会话短期记忆
2. memory_reason：说明本轮为什么这样更新记忆
3. new_facts：本轮新增的重要事实或关键信息
4. next_focus：下一轮沟通建议关注点

你需要关注：
- 当前对话已经发生了什么
- 用户表达模式有什么变化
- 目标人物目前最在意什么
- 哪些问题已经解决
- 哪些问题仍未解决
- 下一轮沟通最应该补充什么
"""



def build_memory_user_prompt(payload: dict) -> str:
    return f"""
请根据以下信息更新本次模拟会话的短期记忆。

场景：
{payload.get("scenario")}

用户目标：
{payload.get("goal")}

用户期望结果：
{payload.get("outcome")}

目标人物画像：
{payload.get("persona")}

已有对话：
{payload.get("messages")}

本轮用户最新发言：
{payload.get("user_message")}

本轮目标人物回复：
{payload.get("target_reply")}

本轮关系状态变化：
{payload.get("state_delta")}

本轮风险点：
{payload.get("risk_flags")}

当前已有记忆：
{payload.get("current_memory")}

请输出 MemoryUpdateResponse，必须包含：
1. memory
2. memory_reason
3. new_facts
4. next_focus
"""

