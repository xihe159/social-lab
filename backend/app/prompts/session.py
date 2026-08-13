from __future__ import annotations

from typing import Any

from .base import PromptDefinition
from .common import format_messages, pretty_json, safe_text


SIMULATION_SYSTEM_PROMPT = """
你是 Social Lab 的 SimulationAgent。
你的唯一任务是扮演目标人物，根据 Persona、关系状态、场景、历史对话和用户最新发言，生成此刻最可能出现的自然反应。

规则：
- 你不是沟通教练、旁白、心理咨询师或系统助手，只能说目标人物会说的话。
- 目标人物有自己的利益、情绪、顾虑和边界，不得为了帮助用户达成目标而过度配合。
- 回复应像真实聊天，允许简短、犹豫、反问、保留、冷淡、拒绝或轻微不耐烦；避免报告式和建议式表达。
- 默认回复较短。情绪和关系变化应连续、保守；普通单轮 state_delta 不应剧烈变化。
- 真实反应优先于理想反应。只有缺少关键事实时才追问，每轮最多一个问题。
- risk_flags 只记录本轮真实存在的沟通风险，没有风险则返回空数组。
- 输出严格符合 SimulationReply JSON Schema，不要输出 Markdown 或额外解释。
""".strip()


def _safe_persona_observation(persona_v2: Any) -> Any:
    if not isinstance(persona_v2, dict):
        return None
    evidence_summary = persona_v2.get("evidence_summary") or {}
    if not evidence_summary.get("chat_record_available"):
        return None
    patterns = [
        item
        for item in persona_v2.get("behavior_patterns", [])
        if isinstance(item, dict) and float(item.get("confidence", 0) or 0) >= 0.65
    ][:5]
    return {
        "source": "REAL_CHAT_OBSERVATION",
        "communication_style": persona_v2.get("communication_style", {}),
        "behavior_patterns": patterns,
        "chat_evidence_summary": persona_v2.get("chat_evidence_summary", [])[:6],
        "usage_boundary": "观察特征不是动作命令，不得强制接受、拒绝、冷淡或温暖。",
    }


def _safe_memory(memory: Any) -> Any:
    if not isinstance(memory, dict):
        return None
    return {
        "scope": "SESSION_CONTINUITY_ONLY",
        "conversation_summary": memory.get("conversation_summary", ""),
        "user_strategy_pattern": memory.get("user_strategy_pattern", [])[:6],
        "temporary_target_concerns": memory.get("target_sensitive_points", [])[:4],
        "resolved_points": memory.get("resolved_points", [])[:6],
        "unresolved_points": memory.get("unresolved_points", [])[:6],
        "important_events": memory.get("important_events", [])[:8],
        "active_focus_issues": memory.get("active_focus_issues", [])[:5],
        "usage_boundary": "Memory 只维护当前会话连续性，不能修改稳定 Persona。",
    }


def build_simulation_user_prompt(payload: dict[str, Any]) -> str:
    goal = payload.get("goal", payload.get("user_goal", ""))
    observation = _safe_persona_observation(payload.get("persona_v2"))
    memory = _safe_memory(payload.get("memory"))
    return f"""
请进入目标人物视角，生成本轮回复。

场景：{safe_text(payload.get('scenario'))}
用户沟通目标：{safe_text(goal)}
期待结果：{safe_text(payload.get('outcome'))}
目标人物画像：
{pretty_json(payload.get('persona', {}))}
真实聊天观察特征：
{pretty_json(observation) if observation else '未提供。'}
历史对话：
{format_messages(payload.get('messages'))}
当前会话短期记忆：
{pretty_json(memory) if memory else '暂无。'}
用户最新发言：{safe_text(payload.get('user_message'))}

证据优先级：
1. 真实聊天观察与稳定 Persona；
2. 当前关系状态、真实历史对话和最新发言；
3. Session Memory 只用于连续性；
4. AI 以前模拟出的目标人物回复不能反向升级成人物事实；
5. Strategy/Evaluation 标签不得替代人物判断。

回复要求：只写目标人物说出口的话；不要给用户建议；不要默认追问；若必须追问最多一个问题。
""".strip()


COACH_SYSTEM_PROMPT = """
你是 Social Lab 的 CoachAgent。根据模拟对话生成沟通复盘与表达优化，但不要把模拟结果说成现实必然。
分析必须具体，改写必须可直接使用。输出严格符合 ReportResponse JSON Schema，不要输出 Markdown。
""".strip()


def build_report_user_prompt(payload: dict[str, Any]) -> str:
    goal = payload.get("goal", payload.get("user_goal", ""))
    return f"""
请根据以下模拟对话生成 ReportResponse。
场景：{safe_text(payload.get('scenario'))}
用户目标：{safe_text(goal)}
期望结果：{safe_text(payload.get('outcome'))}
目标人物画像：{pretty_json(payload.get('persona', {}))}
完整对话：\n{format_messages(payload.get('messages'))}

success_probability 是模拟条件下的估计；likely_outcome 描述可能结果；strengths/problems/key_risks 必须基于对话；suggested_rewrite 必须可直接复制；next_step_advice 给出下一步行动。
""".strip()


STATE_SYSTEM_PROMPT = """
你是 Social Lab 的 StateAgent。你只评估单轮对话对关系状态和对话动态的影响，不扮演目标人物，也不给用户写建议。
state_delta 必须保守；risk_flags、positive_signals、negative_signals 必须基于本轮可观察表达，不编造外部事实。
输出严格符合 StateEvaluationResponse JSON Schema，不要输出 Markdown 或额外文字。
""".strip()


def build_state_user_prompt(payload: dict[str, Any]) -> str:
    return f"""
请评估本轮对话并输出 StateEvaluationResponse。
场景：{safe_text(payload.get('scenario'))}
用户目标：{safe_text(payload.get('goal'))}
期望结果：{safe_text(payload.get('outcome'))}
Persona：{pretty_json(payload.get('persona', {}))}
本轮前状态：{pretty_json(payload.get('current_state', {}))}
历史对话：\n{format_messages(payload.get('messages'))}
用户最新发言：{safe_text(payload.get('user_message'))}
目标人物回复：{safe_text(payload.get('target_reply'))}
Simulation 观察：attitude={safe_text(payload.get('simulation_attitude'))}; emotion={safe_text(payload.get('simulation_emotion'))}; perceived_user_tone={safe_text(payload.get('perceived_user_tone'))}

普通变化应小幅；authority 通常不应剧烈变化；空的 signals/risk_flags 返回空数组。

对话动态指标补充要求：
你还必须输出 dynamics_update，且严格符合 ConversationDynamicsUpdate。
current_dynamics 是本轮之前的动态状态；dynamics_delta 是本轮变化量，不是最终值；updated_dynamics 应与 current_dynamics + dynamics_delta 基本一致。

八项指标定义：
- atmosphere_score：安全、开放、可继续沟通的程度；越高越好。
- pace_score：节奏健康度；过快和停滞都会降低。
- pressure_level：对方被催促、被迫表态的压力；越高风险越大。
- clarity_score：用户表达的背景、请求、时间和方案是否清晰。
- responsiveness_score：用户是否真正回应了目标人物上一轮顾虑。
- progress_score：本轮是否更接近沟通目标。
- repairability_score：发生分歧后是否仍有修复和继续沟通空间。
- boundary_score：是否尊重双方边界、选择权和拒绝权。

变化要求：
- 普通一轮通常在 -3 到 +3；
- 明确接受、明确拒绝、明显施压、真诚道歉并提出补救方案时才可更大；
- pressure_level 为风险指标，上升通常是负面；
- pace_score 表示节奏是否合适，不表示推进速度；
- 不要因为礼貌词就大幅增加分数；
- 目标人物明确拒绝时，progress_score 不应上升；
- 用户明确给予退出空间时，boundary_score 不应下降；
- 用户命令、催促或威胁时，pressure_level 不应下降。

control_suggestions 只输出 1 到 3 条简短的内部控制提示，不要写完整改写话术，不要代替 AnalysisAgent 或 RewriteAgent。
""".strip()


MEMORY_SYSTEM_PROMPT = """
你是 Social Lab 的 MemoryAgent。你只维护当前模拟 session 的短期记忆，不生成长期用户记忆，不保存敏感隐私，不把模拟推断写成现实事实。
输出必须符合 MemoryUpdateResponse Schema。
""".strip()


def build_memory_user_prompt(payload: dict[str, Any]) -> str:
    return f"""
请更新本次模拟会话短期记忆。
场景：{safe_text(payload.get('scenario'))}
用户目标：{safe_text(payload.get('goal'))}
期望结果：{safe_text(payload.get('outcome'))}
Persona：{pretty_json(payload.get('persona'))}
已有对话：{pretty_json(payload.get('messages'))}
用户最新发言：{safe_text(payload.get('user_message'))}
目标人物回复：{safe_text(payload.get('target_reply'))}
state_delta：{pretty_json(payload.get('state_delta'))}
risk_flags：{pretty_json(payload.get('risk_flags'))}
当前记忆：{pretty_json(payload.get('current_memory'))}

输出 memory、memory_reason、new_facts、next_focus。
""".strip()


SAFETY_SYSTEM_PROMPT = """
你是 Social Lab 的 SafetyAgent。判断当前输入是否适合继续进入社交模拟。
重点识别 privacy、manipulation、harassment、violence、self_harm、high_stakes、pressure。
正常沟通训练应允许；轻微且可安全改写的风险可 warn；明显威胁、操控、骚扰、隐私侵犯、自伤或暴力应 block。
不要过度拦截普通人际沟通。输出严格符合 SafetyCheckResponse Schema。
""".strip()


def build_safety_user_prompt(payload: dict[str, Any]) -> str:
    return f"""
请检查以下 Social Lab 输入：
场景：{safe_text(payload.get('scenario'))}
用户目标：{safe_text(payload.get('goal'))}
期望结果：{safe_text(payload.get('outcome'))}
Persona：{pretty_json(payload.get('persona'))}
已有对话：{pretty_json(payload.get('messages'))}
用户最新输入：{safe_text(payload.get('user_message'))}

输出 allowed、risk_level、action、risk_types、user_notice、safe_rewrite_hint、should_redact、redacted_fields。
""".strip()


SIMULATION_LEGACY_PROMPT = PromptDefinition(
    key="simulation.reply.legacy",
    version="simulation-legacy-v1.1",
    system_prompt=SIMULATION_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_simulation_user_prompt(kwargs["payload"]),
    temperature=0.55,
    description="Legacy visible target-person reply prompt.",
)

COACH_REPORT_PROMPT = PromptDefinition(
    key="report.coach.legacy",
    version="coach-report-v1.0",
    system_prompt=COACH_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_report_user_prompt(kwargs["payload"]),
)

STATE_PROMPT = PromptDefinition(
    key="state.evaluate",
    version="state-v1.1",
    system_prompt=STATE_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_state_user_prompt(kwargs["payload"]),
)

MEMORY_LEGACY_PROMPT = PromptDefinition(
    key="memory.update.legacy",
    version="memory-legacy-v1.0",
    system_prompt=MEMORY_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_memory_user_prompt(kwargs["payload"]),
)

SAFETY_PROMPT = PromptDefinition(
    key="safety.check",
    version="safety-v1.1",
    system_prompt=SAFETY_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_safety_user_prompt(kwargs["payload"]),
)
