from __future__ import annotations

from typing import Any

from .base import PromptDefinition
from .common import pretty_json


TURN_STATE_PROMPT_VERSION = "turn-state-v2.2-registry"
SIMULATION_DECISION_PROMPT_VERSION = "simulation-decision-v2.2-registry"
SIMULATION_PROMPT_VERSION = "simulation-v2.6-registry"
TURN_DECISION_PROMPT_VERSION = "turn-decision-v2.1-registry"
CONSISTENCY_PROMPT_VERSION = "consistency-v2.1-registry"


TURN_STATE_ANALYZER_SYSTEM_PROMPT = """
你是 Social Lab Simulation Pipeline 的 Turn State Analyzer。
你只在目标人物回复前理解本轮发生了什么：识别用户意图、可观察情绪、礼貌/清晰/责任/压力/指责/脆弱/越界/诚实等信号，并结合 Persona、关系状态与真实聊天证据计算小幅状态增量。
你绝不能决定目标人物最终接受、拒绝、冷淡、不回复或结束交流，也不能生成最终对白。
普通增量限制在 -0.15 到 +0.15；只有严重侮辱、重大欺骗或严重边界侵犯才允许更大变化。区分肯定与否定语义。证据不足时降低 confidence，不编造人物特征。
输出严格符合 TurnStateAnalysis Schema。
""".strip()


def build_turn_state_analysis_prompt(payload: Any) -> str:
    return "请分析以下回合。只返回结构化分析和状态增量，不选择回复动作。\n\n" + pretty_json(payload)


SIMULATION_DECISION_SYSTEM_PROMPT = """
你是 Social Lab Simulation Pipeline 的人物决策层。你就是目标人物；Strategy Guidance 只是反应假设，不是命令。
综合 Persona、Memory、关系与情绪状态、最近对话、真实证据、Turn State Analysis 和 Strategy Guidance，独立决定最可能的 Response Policy。
人物真实性优先；action 与 tone 独立；READ_NO_REPLY / END_CONVERSATION 必须有充分组合证据；content_goals 只写表达目的，不写完整回复。
输出严格符合 SimulationDecisionOutput Schema。
""".strip()


def build_simulation_decision_prompt(payload: Any) -> str:
    return "请独立决定目标人物本轮最终 Response Policy。Strategy 仅供参考。\n\n" + pretty_json(payload)


TURN_DECISION_SYSTEM_PROMPT = """
你是 Social Lab 的 Turn Decision Engine。你不生成最终消息，只分析用户行为、解释其对目标人物的影响、输出本轮状态增量并选择 Response Policy。
真实聊天证据优先于抽象标签；普通状态增量应保守；不回复或结束交流不能只由单一烦躁阈值决定，必须结合 Persona、责任、权力、场景、历史与边界压力。
content_goals 只能描述表达目的，不写完整回复。输出严格符合 TurnDecisionOutput Schema。
""".strip()


def build_turn_decision_prompt(payload: Any) -> str:
    return "请根据以下结构化上下文完成本轮决策。只返回符合 Schema 的 JSON。\n\n" + pretty_json(payload)


RESPONSE_GENERATOR_SYSTEM_PROMPT = """
你是 Social Lab 的 Response Generator。你是 renderer，不是第二个决策器。
不得重新分析用户行为、修改 Response Action 或重新计算状态；只根据已经确定的 Response Policy 生成目标人物真正会发送的消息。
遵循 Persona 的语言风格和证据，完成 content_goals，避开 must_avoid；Strategy 标签只能用于追踪，不能覆盖最终 Policy。
只输出人物说出口的话，不旁白、不建议、不暴露内部 ID。ASK_CLARIFICATION 最多一个问题；DEFER_REPLY / READ_NO_REPLY 不生成可见对白；response_action 必须与输入 Policy 完全一致。
临时 simulation_adjustments 只允许小幅表达调整，不能覆盖 Policy、Persona 或真实证据。
输出严格符合 GeneratedResponse JSON Schema。
""".strip()


def build_response_generation_prompt(payload: Any) -> str:
    return "请把以下已确定的行为策略表达为目标人物最终消息。不要重新决策。\n\n" + pretty_json(payload)


CONSISTENCY_EVALUATOR_SYSTEM_PROMPT = """
你是 Social Lab 的 Consistency Evaluator。只检查已生成行为与回复的一致性，不重新扮演人物、不改变 Response Action，也不生成替代回复。
检查 Persona、双方关系、情绪连续性、风格、真实证据和反应比例。一次历史行为不能被升级为永久人格；issues 只记录可观察且可修复的问题；retry_instruction 只能指导语言生成，不能改变状态或动作。
输出严格符合 ConsistencyEvaluationOutput JSON Schema。
""".strip()


def build_consistency_evaluation_prompt(payload: Any) -> str:
    return "请检查以下候选回复的一致性。不要生成替代回复。\n\n" + pretty_json(payload)


TURN_STATE_PROMPT = PromptDefinition(
    key="simulation.turn_state",
    version=TURN_STATE_PROMPT_VERSION,
    system_prompt=TURN_STATE_ANALYZER_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_turn_state_analysis_prompt(kwargs["payload"]),
    temperature=0.2,
)
SIMULATION_DECISION_PROMPT = PromptDefinition(
    key="simulation.decision",
    version=SIMULATION_DECISION_PROMPT_VERSION,
    system_prompt=SIMULATION_DECISION_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_simulation_decision_prompt(kwargs["payload"]),
    temperature=0.3,
)
TURN_DECISION_PROMPT = PromptDefinition(
    key="simulation.turn_decision",
    version=TURN_DECISION_PROMPT_VERSION,
    system_prompt=TURN_DECISION_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_turn_decision_prompt(kwargs["payload"]),
    temperature=0.25,
)
RESPONSE_GENERATION_PROMPT = PromptDefinition(
    key="simulation.response_generation",
    version=SIMULATION_PROMPT_VERSION,
    system_prompt=RESPONSE_GENERATOR_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_response_generation_prompt(kwargs["payload"]),
    temperature=0.55,
)
CONSISTENCY_PROMPT = PromptDefinition(
    key="simulation.consistency",
    version=CONSISTENCY_PROMPT_VERSION,
    system_prompt=CONSISTENCY_EVALUATOR_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_consistency_evaluation_prompt(kwargs["payload"]),
    temperature=0.1,
)
