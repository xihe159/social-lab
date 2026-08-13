from __future__ import annotations

from typing import Any

from .base import PromptDefinition
from .common import format_messages, pretty_json


ANALYSIS_SYSTEM_PROMPT = """
你是 Social Lab 的 AnalysisAgent。
你的职责是逐句观察用户在模拟对话中的表达，判断沟通功能和意图，描述目标人物可能如何理解和感受，评价每句话对沟通目标的影响，并为真实状态增量提供句级语义归因权重。

严格禁止：不要提供改进建议、下一步行动、改写话术或任何 fix_direction / improvement_action / suggested_rewrite；不要使用“建议、应该、最好、不妨、可以改为、可改成”等指令性措辞。
relationship_signal 和 dynamics_signal 只是语义方向和强度，不是最终 delta；每个信号范围 -5 到 +5；pressure_level 正数表示压力上升；sentence_text 必须与输入清单完全一致，每个句子只能出现一次。
评价标签仅使用 strong / effective / neutral / risky / damaging。
输出严格符合 AnalysisSemanticResult JSON Schema，不输出 Markdown。
""".strip()


def build_analysis_user_prompt(*, request: Any, manifest: list[Any]) -> str:
    sentence_manifest = [
        {
            "turn_index": turn.turn_index,
            "user_message": turn.user_message,
            "target_reply": turn.target_reply,
            "sentences": [
                {
                    "sentence_index": sentence.sentence_index,
                    "sentence_text": sentence.sentence_text,
                }
                for sentence in turn.sentences
            ],
        }
        for turn in manifest
    ]
    selected_turns = {turn.turn_index for turn in manifest}
    traces: list[dict[str, Any]] = []
    for trace in request.turn_traces:
        if trace.turn_index not in selected_turns:
            continue
        payload = trace.model_dump()
        for field_name in ("dynamics_before", "dynamics_after"):
            dynamics = payload.get(field_name)
            if isinstance(dynamics, dict):
                dynamics.pop("recommended_next_move", None)
                dynamics.pop("dynamics_reason", None)
        traces.append(payload)

    return f"""
请输出 AnalysisSemanticResult。
场景：{request.scenario}
用户沟通目标：{request.goal}
期望结果：{request.outcome or '未提供'}
目标人物画像：{pretty_json(request.persona)}
必须逐句分析的清单：{pretty_json(sentence_manifest)}
整轮状态轨迹：{pretty_json(traces) if traces else '未提供。没有轨迹时只做语义评价。'}

要求：turns 与逐句清单一一对应；sentence_text 原样复制；所有 signals 只表示归因权重；problems 和 primary_bottleneck 只描述问题，不给解决方案。
""".strip()


PREDICTION_SYSTEM_PROMPT = """
你是 Social Lab 的 PredictionAgent。你不直接猜成功率，只进行有限语义评估：判断目标人物更接近接受、条件接受、犹豫、拒绝、不回应或未知；找出结构化指标尚未覆盖的语义因素；给出 -8 到 +8 的 semantic_adjustment；提供绑定原话的证据；解释最可能的模拟结果。
禁止直接输出 success_probability、下一步建议、改写话术或 improvement_action。不要把模拟结果写成现实必然，也不要重复给已经进入 Dynamics/关系状态的因素大幅计分。
输出严格符合 SemanticPredictionAssessment JSON Schema，不输出 Markdown。
""".strip()


def build_prediction_user_prompt(*, request: Any, context: Any) -> str:
    dynamics = pretty_json(context.current_dynamics) if context.current_dynamics is not None else "未提供"
    trend = pretty_json(context.dynamics_history[-5:]) if context.dynamics_history else "未提供"
    return f"""
请输出 SemanticPredictionAssessment。
场景：{request.scenario}
沟通目标：{request.goal}
期望结果：{request.outcome or '未提供'}
目标人物画像：{pretty_json(request.persona)}
完整模拟对话：\n{format_messages(request.messages)}
当前对话动态：{dynamics}
最近 Dynamics 快照：{trend}

重点判断目标人物最新回应的 outcome_state，以及当前 Dynamics 尚未完整表达的语义信号。semantic_adjustment 只能在 -8 到 +8；semantic_factors 必须引用真实对话原话；不要输出建议或改写。
""".strip()


REWRITE_SYSTEM_PROMPT = """
你是 Social Lab 的 RewriteAgent。AnalysisAgent 只负责观察与评价；所有改进相关内容由你负责。
任务：对低效/高风险/阻碍目标的用户句子提供逐句改写；生成综合推荐话术；生成最小修改版、温和版、坚定边界版；给出下一步沟通行动；列出下一轮应避免的表达。
约束：sentence_rewrites 只能引用 AnalysisAgent 中真实存在的用户句子，original_text 必须原样复制；不要修改目标人物回复；不要操控、威胁、欺骗、道德绑架或持续施压；目标人物已明确拒绝或终止时不要继续强推；推荐表达应自然、可复制并保留对方选择空间。
输出严格符合 RewriteResult JSON Schema，不输出 Markdown。
""".strip()


def build_rewrite_user_prompt(*, request: Any, prediction: Any, analysis: Any) -> str:
    rewrite_candidates = [
        {
            "turn_index": sentence.turn_index,
            "sentence_index": sentence.sentence_index,
            "sentence_text": sentence.sentence_text,
            "evaluation_label": sentence.evaluation_label,
            "evaluation_score": sentence.evaluation_score,
            "goal_effect": sentence.goal_effect,
            "target_likely_feeling": sentence.target_likely_feeling,
            "evaluation_reason": sentence.evaluation_reason,
        }
        for turn in analysis.turns
        for sentence in turn.sentences
        if (
            sentence.evaluation_label in {"neutral", "risky", "damaging"}
            or sentence.goal_effect == "obstructs"
            or sentence.evaluation_score < 65
        )
    ]
    summary = {
        "overall_assessment": analysis.overall_assessment,
        "problems": analysis.problems,
        "key_risks": analysis.key_risks,
        "primary_bottleneck": analysis.primary_bottleneck,
        "evaluation_scores": analysis.evaluation_scores.model_dump(),
        "state_trajectory_summary": analysis.state_trajectory_summary,
    }
    return f"""
请输出 RewriteResult。
场景：{request.scenario}
用户目标：{request.goal}
期望结果：{request.outcome or '未提供'}
PredictionAgent 结果：{pretty_json(prediction)}
AnalysisAgent 整体分析：{pretty_json(summary)}
可逐句改写的候选句：{pretty_json(rewrite_candidates)}
完整逐句分析：{pretty_json([turn.model_dump() for turn in analysis.turns])}

sentence_rewrites 只处理确有改进价值的句子；不必改写 strong/effective 句子；所有下一步和改进内容都在本输出完成；suggested_rewrite 应形成自然连贯、可直接复制的完整表达。
""".strip()


ANALYSIS_PROMPT = PromptDefinition(
    key="report.analysis",
    version="analysis-v1.1-registry",
    system_prompt=ANALYSIS_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_analysis_user_prompt(
        request=kwargs["request"], manifest=kwargs["manifest"]
    ),
    temperature=0.15,
    description="Sentence-level observational analysis with no advice.",
)

PREDICTION_PROMPT = PromptDefinition(
    key="report.prediction",
    version="prediction-v1.1-registry",
    system_prompt=PREDICTION_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_prediction_user_prompt(
        request=kwargs["request"], context=kwargs["context"]
    ),
    temperature=0.15,
    description="Bounded semantic adjustment for deterministic prediction.",
)

REWRITE_PROMPT = PromptDefinition(
    key="report.rewrite",
    version="rewrite-v1.1-registry",
    system_prompt=REWRITE_SYSTEM_PROMPT,
    user_builder=lambda **kwargs: build_rewrite_user_prompt(
        request=kwargs["request"], prediction=kwargs["prediction"], analysis=kwargs["analysis"]
    ),
    temperature=0.25,
    description="All user-facing rewriting and next-step advice.",
)
