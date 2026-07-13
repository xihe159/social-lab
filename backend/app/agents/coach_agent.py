from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.llm.client import generate_structured
from app.schemas.report import ReportRequest, ReportResponse
from app.schemas.session import ChatMessage


# =========================================================
# 1. 中间结构化输出 Schema
#    这些 Schema 只在 coach_agent.py 内部使用，不影响外部 API。
# =========================================================

class InfluenceFactor(BaseModel):
    """
    影响沟通结果的主要因素。
    用于解释 success_probability 为什么是这个数。
    """

    model_config = ConfigDict(extra="forbid")

    factor_name: str = Field(description="影响因素名称，例如：目标清晰度、情绪安全感、对方成本感知")
    direction: Literal["positive", "negative", "mixed"] = Field(description="该因素是正向、负向还是混合影响")
    importance: int = Field(ge=1, le=5, description="重要程度，1 到 5")
    impact_score: int = Field(ge=-20, le=20, description="对成功率的影响分，负数表示拉低，正数表示拉高")
    evidence_turns: list[int] = Field(description="相关对话轮次编号")
    evidence_quote: str = Field(description="相关用户原话证据")
    explanation: str = Field(description="为什么该因素会影响目标人物反应")
    improvement_action: str = Field(description="用户下一步应该如何优化")


class PredictionResult(BaseModel):
    """
    PredictionAgent 的输出。
    只负责预测，不负责详细诊断和改写。
    """

    model_config = ConfigDict(extra="forbid")

    success_probability: int = Field(ge=0, le=100, description="模拟条件下的成功概率")
    likely_outcome: str = Field(description="基于模拟对话的可能结果")
    confidence: Literal["low", "medium", "high"] = Field(description="预测置信度")
    probability_reasoning: str = Field(description="成功率判断依据")
    main_influence_factors: list[InfluenceFactor] = Field(description="主要影响因素，3 到 5 条")


class TurnDiagnostic(BaseModel):
    """
    单轮表达诊断。
    用于让报告从泛泛总结变成具体指导。
    """

    model_config = ConfigDict(extra="forbid")

    turn_index: int = Field(description="对话轮次编号")
    issue_type: str = Field(description="问题类型，例如：表达模糊、语气施压、缺少方案、没有照顾对方成本")
    evidence_quote: str = Field(description="用户原话证据")
    target_likely_feeling: str = Field(description="目标人物可能产生的感受或理解")
    relationship_impact: str = Field(description="对关系状态或沟通目标的影响")
    fix_direction: str = Field(description="这一轮应该如何修改")


class AnalysisResult(BaseModel):
    """
    AnalysisAgent 的输出。
    负责诊断，不负责生成最终完整改写。
    """

    model_config = ConfigDict(extra="forbid")

    strengths: list[str] = Field(description="用户表达中的优点")
    problems: list[str] = Field(description="用户表达中的主要问题")
    key_risks: list[str] = Field(description="关键沟通风险")
    primary_bottleneck: str = Field(description="当前最影响沟通目标达成的核心瓶颈")
    turn_diagnostics: list[TurnDiagnostic] = Field(description="逐轮诊断，最多 5 条")


class RewriteResult(BaseModel):
    """
    RewriteAgent 的输出。
    负责生成可复制话术和下一步行动建议。
    """

    model_config = ConfigDict(extra="forbid")

    suggested_rewrite: str = Field(description="最推荐的完整改写话术，用户可以直接复制")
    minimal_edit: str = Field(description="最小修改版，尽量保留用户原意")
    warmer_version: str = Field(description="更温和共情版")
    firmer_version: str = Field(description="更坚定边界版")
    next_step_advice: str = Field(description="下一步沟通建议")
    do_not_say: list[str] = Field(description="下一轮应避免的表达")


# =========================================================
# 2. Prompt
#    为了这次重构尽量集中修改，先把拆分 Agent 的 prompt 放在本文件。
# =========================================================

PREDICTION_SYSTEM_PROMPT = """
你是 Social Lab 的 PredictionAgent。
你的任务是根据一次模拟对话，判断用户当前沟通目标在模拟条件下的成功概率、可能结果和主要影响因素。

你只负责预测，不负责给完整改写话术。
你必须保持“模拟预测”语气，不要把结果说成现实必然。

你需要重点判断：
1. 用户目标是否清晰；
2. 目标人物是否已经表现出接受、犹豫、抗拒或防御；
3. 用户表达是否降低了对方成本；
4. 用户表达是否让对方有情绪安全感；
5. 对话是否出现了压力、指责、模糊、逃避责任、缺少方案等风险。

输出要求：
1. success_probability 必须是 0 到 100 的整数；
2. confidence 只能是 low、medium、high；
3. main_influence_factors 输出 3 到 5 条；
4. 每个影响因素必须有 evidence_quote，不能空泛；
5. 不要输出 Markdown；
6. 输出必须严格符合 PredictionResult JSON Schema。
""".strip()


ANALYSIS_SYSTEM_PROMPT = """
你是 Social Lab 的 AnalysisAgent。
你的任务是对用户在模拟对话中的表达进行具体诊断。

你不负责预测成功率，也不负责生成最终完整改写。
你只负责指出：
1. 用户表达中做得好的地方；
2. 用户表达中的主要问题；
3. 关键沟通风险；
4. 最核心瓶颈；
5. 哪几轮话最需要修改。

重要要求：
1. 不要泛泛地说“表达要更清楚”“语气要更好”；
2. 每个问题都要尽量绑定用户原话；
3. turn_diagnostics 最多输出 5 条；
4. 如果没有足够对话，也要说明信息不足；
5. 不要输出 Markdown；
6. 输出必须严格符合 AnalysisResult JSON Schema。
""".strip()


REWRITE_SYSTEM_PROMPT = """
你是 Social Lab 的 RewriteAgent。
你的任务是根据预测结果和诊断结果，为用户生成可以直接使用的优化话术。

你需要输出：
1. suggested_rewrite：综合最推荐版本；
2. minimal_edit：最小修改版，尽量保留用户原意；
3. warmer_version：更温和、更照顾对方感受的版本；
4. firmer_version：更坚定、更有边界的版本；
5. next_step_advice：下一步沟通策略；
6. do_not_say：下一轮应避免的话。

重要原则：
1. 不要操控、威胁、欺骗、道德绑架或过度施压；
2. 话术应该自然，像真实人会说的话；
3. suggested_rewrite 必须是一段完整可复制的话；
4. 如果信息不足，优先建议用户补充背景和具体请求；
5. 不要输出 Markdown；
6. 输出必须严格符合 RewriteResult JSON Schema。
""".strip()


# =========================================================
# 3. Prompt 构造工具函数
# =========================================================

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


def _build_base_context(request: ReportRequest) -> str:
    payload = request.model_dump()
    goal = payload.get("goal", payload.get("user_goal", ""))

    return f"""
〖场景类型〗
{_safe_text(payload.get("scenario"))}

〖用户沟通目标〗
{_safe_text(goal)}

〖期望结果〗
{_safe_text(payload.get("outcome"))}

〖目标人物画像 persona〗
{_to_pretty_json(payload.get("persona", {}))}

〖完整模拟对话 messages〗
{_format_messages(payload.get("messages"))}
""".strip()


def _build_prediction_prompt(request: ReportRequest) -> str:
    return f"""
请根据以下信息输出 PredictionResult。

{_build_base_context(request)}

请特别注意：
- success_probability 是模拟条件下的估计，不代表现实必然；
- main_influence_factors 必须解释成功率为什么是这个数；
- 每个影响因素必须绑定 evidence_quote。
""".strip()


def _build_analysis_prompt(
    request: ReportRequest,
    prediction: PredictionResult,
) -> str:
    return f"""
请根据以下信息输出 AnalysisResult。

{_build_base_context(request)}

〖PredictionAgent 预测结果〗
{_to_pretty_json(prediction.model_dump())}

请重点诊断：
- 用户哪几句话推动了目标；
- 用户哪几句话造成了阻力；
- 哪些问题最需要下一轮修正；
- turn_diagnostics 必须尽量引用用户原话。
""".strip()


def _build_rewrite_prompt(
    request: ReportRequest,
    prediction: PredictionResult,
    analysis: AnalysisResult,
) -> str:
    return f"""
请根据以下信息输出 RewriteResult。

{_build_base_context(request)}

〖PredictionAgent 预测结果〗
{_to_pretty_json(prediction.model_dump())}

〖AnalysisAgent 诊断结果〗
{_to_pretty_json(analysis.model_dump())}

请生成：
1. 一段最推荐的完整改写话术；
2. 一个最小修改版本；
3. 一个更温和版本；
4. 一个更坚定版本；
5. 下一步沟通建议；
6. 下一轮不要说的话。

话术要自然、低压力、可直接复制。
""".strip()


# =========================================================
# 4. 三个 LLM Agent
# =========================================================

class PredictionAgent:
    """
    预测型 Agent：
    负责 success_probability、likely_outcome、主要影响因素。
    """

    async def run(self, request: ReportRequest) -> PredictionResult:
        result = await generate_structured(
            system_prompt=PREDICTION_SYSTEM_PROMPT,
            user_prompt=_build_prediction_prompt(request),
            output_model=PredictionResult,
            temperature=0.2,
        )
        return self.post_process(result, request)

    def post_process(
        self,
        result: PredictionResult,
        request: ReportRequest,
    ) -> PredictionResult:
        result.success_probability = _clamp(result.success_probability, 0, 100)
        result.likely_outcome = _clean_text(
            result.likely_outcome,
            default=_default_likely_outcome(result.success_probability),
        )
        result.probability_reasoning = _clean_text(
            result.probability_reasoning,
            default="该成功率基于当前模拟对话、目标人物画像和用户表达质量综合估计。",
        )

        result.main_influence_factors = _normalize_factors(
            result.main_influence_factors
        )

        if not _has_user_messages(request.messages):
            result.success_probability = min(result.success_probability, 50)
            result.confidence = "low"

        return result


class AnalysisAgent:
    """
    分析型 Agent：
    负责优点、问题、风险、核心瓶颈、逐轮诊断。
    """

    async def run(
        self,
        request: ReportRequest,
        prediction: PredictionResult,
    ) -> AnalysisResult:
        result = await generate_structured(
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            user_prompt=_build_analysis_prompt(request, prediction),
            output_model=AnalysisResult,
            temperature=0.3,
        )
        return self.post_process(result, request)

    def post_process(
        self,
        result: AnalysisResult,
        request: ReportRequest,
    ) -> AnalysisResult:
        result.strengths = _normalize_list(
            result.strengths,
            defaults=["能够主动表达沟通目标。"],
            max_items=5,
        )
        result.problems = _normalize_list(
            result.problems,
            defaults=["部分表达仍需要补充具体背景、时间安排或对对方成本的考虑。"],
            max_items=5,
        )
        result.key_risks = _normalize_list(
            result.key_risks,
            defaults=["如果请求过于直接或缺少缓冲，可能让对方感到压力。"],
            max_items=5,
        )
        result.primary_bottleneck = _clean_text(
            result.primary_bottleneck,
            default="当前核心瓶颈是表达还不够具体，且对对方成本和顾虑的照顾不足。",
        )
        result.turn_diagnostics = _normalize_turn_diagnostics(
            result.turn_diagnostics
        )

        if not _has_user_messages(request.messages):
            result.key_risks.append(
                "尚未形成有效模拟对话，当前分析只能基于目标人物画像和沟通目标进行初步判断。"
            )

        return result


class RewriteAgent:
    """
    改写型 Agent：
    负责可复制话术和下一步策略。
    """

    async def run(
        self,
        request: ReportRequest,
        prediction: PredictionResult,
        analysis: AnalysisResult,
    ) -> RewriteResult:
        result = await generate_structured(
            system_prompt=REWRITE_SYSTEM_PROMPT,
            user_prompt=_build_rewrite_prompt(request, prediction, analysis),
            output_model=RewriteResult,
            temperature=0.35,
        )
        return self.post_process(result, request)

    def post_process(
        self,
        result: RewriteResult,
        request: ReportRequest,
    ) -> RewriteResult:
        result.suggested_rewrite = _clean_text(
            result.suggested_rewrite,
            default=_default_rewrite(request),
        )
        result.minimal_edit = _clean_text(
            result.minimal_edit,
            default=result.suggested_rewrite,
        )
        result.warmer_version = _clean_text(
            result.warmer_version,
            default=result.suggested_rewrite,
        )
        result.firmer_version = _clean_text(
            result.firmer_version,
            default=result.suggested_rewrite,
        )
        result.next_step_advice = _clean_text(
            result.next_step_advice,
            default="下一步建议先补充具体背景和可执行方案，再以低压力方式提出请求。",
        )
        result.do_not_say = _normalize_list(
            result.do_not_say,
            defaults=["不要使用命令式、威胁式或让对方立刻表态的表达。"],
            max_items=5,
        )

        result.suggested_rewrite = _truncate(result.suggested_rewrite, 900)
        result.minimal_edit = _truncate(result.minimal_edit, 500)
        result.warmer_version = _truncate(result.warmer_version, 500)
        result.firmer_version = _truncate(result.firmer_version, 500)
        result.next_step_advice = _truncate(result.next_step_advice, 700)

        return result


# =========================================================
# 5. ReportAssembler
#    第一版先不调用 LLM，只做确定性组装。
# =========================================================

class ReportAssembler:
    """
    报告组装器：
    把 PredictionAgent、AnalysisAgent、RewriteAgent 的结果
    合并为当前前端和 API 已经使用的 ReportResponse。
    """

    def run(
        self,
        *,
        request: ReportRequest,
        prediction: PredictionResult,
        analysis: AnalysisResult,
        rewrite: RewriteResult,
    ) -> ReportResponse:
        likely_outcome = self._build_likely_outcome(prediction, analysis)
        problems = self._build_problems(prediction, analysis)
        key_risks = self._build_key_risks(prediction, analysis)
        next_step_advice = self._build_next_step_advice(analysis, rewrite)

        report = ReportResponse(
            success_probability=prediction.success_probability,
            likely_outcome=likely_outcome,
            strengths=analysis.strengths,
            problems=problems,
            key_risks=key_risks,
            suggested_rewrite=rewrite.suggested_rewrite,
            next_step_advice=next_step_advice,
        )

        return self.post_process(report, request)

    def _build_likely_outcome(
        self,
        prediction: PredictionResult,
        analysis: AnalysisResult,
    ) -> str:
        factor_summary = _format_factor_summary(prediction.main_influence_factors)

        text = (
            f"{prediction.likely_outcome}\n\n"
            f"成功率判断依据：{prediction.probability_reasoning}\n\n"
            f"主要影响因素：{factor_summary}\n\n"
            f"当前核心瓶颈：{analysis.primary_bottleneck}"
        )
        return _truncate(text, 1200)

    def _build_problems(
        self,
        prediction: PredictionResult,
        analysis: AnalysisResult,
    ) -> list[str]:
        problems = list(analysis.problems)

        for factor in prediction.main_influence_factors:
            if factor.direction in {"negative", "mixed"}:
                item = (
                    f"{factor.factor_name}：{factor.explanation}"
                    f" 建议：{factor.improvement_action}"
                )
                problems.append(item)

        for diagnostic in analysis.turn_diagnostics[:3]:
            item = (
                f"第 {diagnostic.turn_index} 轮：{diagnostic.issue_type}。"
                f"原话“{diagnostic.evidence_quote}”。"
                f"建议：{diagnostic.fix_direction}"
            )
            problems.append(item)

        return _normalize_list(
            problems,
            defaults=["部分表达仍需要补充具体背景、时间安排或对对方成本的考虑。"],
            max_items=5,
        )

    def _build_key_risks(
        self,
        prediction: PredictionResult,
        analysis: AnalysisResult,
    ) -> list[str]:
        risks = list(analysis.key_risks)

        for factor in prediction.main_influence_factors:
            if factor.direction == "negative" and factor.importance >= 4:
                risks.append(
                    f"{factor.factor_name}可能明显拉低沟通成功率：{factor.explanation}"
                )

        return _normalize_list(
            risks,
            defaults=["如果请求过于直接或缺少缓冲，可能让对方感到压力。"],
            max_items=5,
        )

    def _build_next_step_advice(
        self,
        analysis: AnalysisResult,
        rewrite: RewriteResult,
    ) -> str:
        do_not_say = "；".join(rewrite.do_not_say[:3])

        text = (
            f"{rewrite.next_step_advice}\n\n"
            f"优先修正：{analysis.primary_bottleneck}\n\n"
            f"不要这样说：{do_not_say}\n\n"
            f"备选表达方向：\n"
            f"1. 最小修改版：{rewrite.minimal_edit}\n"
            f"2. 更温和版：{rewrite.warmer_version}\n"
            f"3. 更坚定版：{rewrite.firmer_version}"
        )
        return _truncate(text, 1200)

    def post_process(
        self,
        result: ReportResponse,
        request: ReportRequest,
    ) -> ReportResponse:
        result.success_probability = _clamp(result.success_probability, 0, 100)

        result.likely_outcome = _clean_text(
            result.likely_outcome,
            default=_default_likely_outcome(result.success_probability),
        )

        result.strengths = _normalize_list(
            result.strengths,
            defaults=["能够主动表达沟通目标。"],
            max_items=5,
        )

        result.problems = _normalize_list(
            result.problems,
            defaults=["部分表达仍需要补充具体背景、时间安排或对对方成本的考虑。"],
            max_items=5,
        )

        result.key_risks = _normalize_list(
            result.key_risks,
            defaults=["如果请求过于直接或缺少缓冲，可能让对方感到压力。"],
            max_items=5,
        )

        result.suggested_rewrite = _clean_text(
            result.suggested_rewrite,
            default=_default_rewrite(request),
        )
        result.suggested_rewrite = _truncate(result.suggested_rewrite, 900)

        result.next_step_advice = _clean_text(
            result.next_step_advice,
            default="下一步建议先补充具体背景和可执行方案，再以低压力方式提出请求。",
        )
        result.next_step_advice = _truncate(result.next_step_advice, 1200)

        if not _has_user_messages(request.messages):
            result.success_probability = min(result.success_probability, 50)

            if "尚未形成有效模拟对话，当前报告只能基于目标人物画像和沟通目标进行初步判断。" not in result.key_risks:
                result.key_risks.append(
                    "尚未形成有效模拟对话，当前报告只能基于目标人物画像和沟通目标进行初步判断。"
                )

        return result


# =========================================================
# 6. CoachAgent 总入口
#    保留原类名，避免 api/report.py 需要修改。
# =========================================================

class CoachAgent:
    """
    CoachAgent 现在变成报告编排入口。

    内部流程：
    1. PredictionAgent 预测成功率和主要影响因素；
    2. AnalysisAgent 诊断表达问题；
    3. RewriteAgent 生成改写话术；
    4. ReportAssembler 合并为 ReportResponse。
    """

    def __init__(self) -> None:
        self.prediction_agent = PredictionAgent()
        self.analysis_agent = AnalysisAgent()
        self.rewrite_agent = RewriteAgent()
        self.report_assembler = ReportAssembler()

    async def run(self, request: ReportRequest) -> ReportResponse:
        prediction = await self.prediction_agent.run(request)

        analysis = await self.analysis_agent.run(
            request=request,
            prediction=prediction,
        )

        rewrite = await self.rewrite_agent.run(
            request=request,
            prediction=prediction,
            analysis=analysis,
        )

        return self.report_assembler.run(
            request=request,
            prediction=prediction,
            analysis=analysis,
            rewrite=rewrite,
        )


# =========================================================
# 7. 通用后处理工具函数
# =========================================================

def _has_user_messages(messages: list[ChatMessage]) -> bool:
    return any(
        message.role == "user" and message.content.strip()
        for message in messages
    )


def _last_user_message(messages: list[ChatMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user" and message.content.strip():
            return message.content.strip()
    return ""


def _normalize_list(
    values: list[str],
    *,
    defaults: list[str],
    max_items: int,
) -> list[str]:
    cleaned: list[str] = []

    for value in values:
        value = str(value).strip()
        if not value:
            continue
        if value not in cleaned:
            cleaned.append(value[:220])

    for value in defaults:
        if value not in cleaned:
            cleaned.append(value)

    return cleaned[:max_items]


def _normalize_factors(
    factors: list[InfluenceFactor],
) -> list[InfluenceFactor]:
    cleaned: list[InfluenceFactor] = []

    for factor in factors:
        factor.factor_name = _clean_text(
            factor.factor_name,
            default="未命名影响因素",
        )
        factor.explanation = _clean_text(
            factor.explanation,
            default="该因素会影响目标人物对当前沟通的接受程度。",
        )
        factor.improvement_action = _clean_text(
            factor.improvement_action,
            default="下一轮应补充具体背景、降低对方压力，并给出可执行选择。",
        )
        factor.evidence_quote = _clean_text(
            factor.evidence_quote,
            default="未找到明确原话证据。",
        )

        factor.importance = _clamp(factor.importance, 1, 5)
        factor.impact_score = _clamp(factor.impact_score, -20, 20)

        if factor.direction == "positive" and factor.impact_score < 0:
            factor.impact_score = abs(factor.impact_score)

        if factor.direction == "negative" and factor.impact_score > 0:
            factor.impact_score = -factor.impact_score

        cleaned.append(factor)

    cleaned.sort(
        key=lambda item: (item.importance, abs(item.impact_score)),
        reverse=True,
    )

    return cleaned[:5]


def _normalize_turn_diagnostics(
    diagnostics: list[TurnDiagnostic],
) -> list[TurnDiagnostic]:
    cleaned: list[TurnDiagnostic] = []

    for item in diagnostics:
        item.issue_type = _clean_text(
            item.issue_type,
            default="表达需要优化",
        )
        item.evidence_quote = _clean_text(
            item.evidence_quote,
            default="未找到明确原话证据。",
        )
        item.target_likely_feeling = _clean_text(
            item.target_likely_feeling,
            default="对方可能需要更多背景和更低压力的表达。",
        )
        item.relationship_impact = _clean_text(
            item.relationship_impact,
            default="可能降低对方继续沟通或配合的意愿。",
        )
        item.fix_direction = _clean_text(
            item.fix_direction,
            default="补充具体事实、降低压力，并给对方留出选择空间。",
        )

        item.turn_index = max(1, int(item.turn_index))
        cleaned.append(item)

    cleaned.sort(key=lambda item: item.turn_index)

    return cleaned[:5]


def _format_factor_summary(factors: list[InfluenceFactor]) -> str:
    if not factors:
        return "暂无明确主要影响因素。"

    parts: list[str] = []

    for factor in factors[:5]:
        direction_label = {
            "positive": "正向",
            "negative": "负向",
            "mixed": "混合",
        }.get(factor.direction, "混合")

        parts.append(
            f"{factor.factor_name}（{direction_label}，重要度 {factor.importance}/5，"
            f"影响分 {factor.impact_score}）：{factor.explanation}"
        )

    return "；".join(parts)


def _clean_text(value: Any, *, default: str) -> str:
    if not isinstance(value, str):
        return default
    value = value.strip()
    return value or default


def _truncate(value: str, max_length: int) -> str:
    value = value.strip()
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "…"


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


def _default_likely_outcome(probability: int) -> str:
    if probability >= 75:
        return "从模拟结果看，对方较可能接受或至少愿意继续讨论，但仍需要保持具体、尊重和低压力的表达。"
    if probability >= 50:
        return "从模拟结果看，对方可能不会直接拒绝，但仍会关注请求是否合理、成本是否清晰。"
    return "从模拟结果看，对方可能存在明显顾虑，需要先降低对方压力并补充更多背景。"


def _default_rewrite(request: ReportRequest) -> str:
    last_user_message = _last_user_message(request.messages)

    if last_user_message:
        return (
            f"我想重新更清楚地表达一下：{last_user_message}\n\n"
            "如果这件事对你来说不方便，也完全可以直接告诉我；"
            "我主要是想先把背景和我的想法说明清楚。"
        )

    if request.scenario == "advisor":
        return (
            "老师您好，我想向您说明一下目前的情况、已经尝试过的解决办法，"
            "以及我接下来的具体计划。希望您能看一下这个安排是否可行，"
            "如果不合适我也可以根据您的建议调整。"
        )

    if request.scenario == "work":
        return (
            "我想先同步一下这件事的背景、目前影响和我建议的处理方案。"
            "也想听听您这边是否有其他优先级或限制，我可以据此调整。"
        )

    if request.scenario == "social":
        return (
            "我想认真和你说一下这件事。我的本意不是给你压力，"
            "而是希望把我的想法说明白，也想听听你的感受。"
        )

    return (
        "我想更清楚地说明一下背景、我的想法和希望达成的结果。"
        "如果你觉得不方便，也可以直接告诉我。"
    )