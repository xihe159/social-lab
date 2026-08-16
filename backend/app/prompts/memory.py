from __future__ import annotations

from typing import Any

from .base import PromptDefinition
from .common import pretty_json


MEMORY_EXTRACTOR_SYSTEM_PROMPT = """
你是 Social Lab 的 MemoryExtractor。你不是报告或建议 Agent，而是从一轮模拟对话中提取“当前 session 的短期记忆候选项”。
重点识别用户对话模式、目标人物临时敏感点、对话聚焦问题、关键信息重复风险、已解决问题和重要事件。

边界：
- 不保存手机号、住址、身份证号、账号、精确地址等敏感隐私；
- 不把模拟推断写成现实事实；
- 目标人物本轮回复是 AI 模拟事件，不是真实人物证据；不得据此新增稳定性格、固定风格、长期偏好、回复习惯或长期敏感点；
- 每个候选记忆必须有 evidence_quote；
- 输出严格符合 MemoryExtractionResult JSON Schema，不输出 Markdown。
""".strip()


def build_memory_extractor_user_prompt(request: Any) -> str:
    current_memory = request.current_memory.model_dump(mode="json") if request.current_memory else None
    return f"""
请根据以下本轮模拟对话提取短期会话记忆候选项。
场景：{request.scenario}
用户沟通目标：{request.goal}
用户期待结果：{request.outcome or '未提供'}
目标人物画像：{pretty_json(request.persona)}
上一轮 memory：{pretty_json(current_memory) if current_memory else '暂无'}
用户本轮发言：{request.user_message}
目标人物本轮回复：{request.target_reply}
注意：目标人物回复来源于 AI 模拟，只能作为本次会话事件，不能作为真实人物画像证据。
本轮关系状态变化：{pretty_json(request.state_delta)}
本轮风险标记：{pretty_json(request.risk_flags)}

输出本轮摘要、3-8 条候选记忆、已解决问题、未解决问题、重复风险、下一轮重点和 memory_reason。不得从模拟回复中提取稳定人物风格或长期敏感点。
""".strip()


MEMORY_EXTRACTOR_PROMPT = PromptDefinition(
    key="memory.extract",
    version="memory-extractor-v1.1-registry",
    system_prompt=MEMORY_EXTRACTOR_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_memory_extractor_user_prompt(kwargs["request"]),
    temperature=0.2,
    description="Extract bounded session memory from one simulated turn.",
)
