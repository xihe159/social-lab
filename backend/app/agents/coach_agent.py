from __future__ import annotations

import json
import logging
import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.agents.prediction_agent import PredictionAgent
from app.llm.client import generate_structured
from app.schemas.prediction import PredictionResult
from app.schemas.report import ReportRequest, ReportResponse
from app.schemas.session import ChatMessage


logger = logging.getLogger(__name__)


class TurnDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_index: int
    issue_type: str
    evidence_quote: str
    target_likely_feeling: str
    relationship_impact: str
    fix_direction: str


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strengths: list[str]
    problems: list[str]
    key_risks: list[str]
    primary_bottleneck: str
    turn_diagnostics: list[TurnDiagnostic]


class RewriteResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggested_rewrite: str
    minimal_edit: str
    warmer_version: str
    firmer_version: str
    next_step_advice: str
    do_not_say: list[str]


ANALYSIS_SYSTEM_PROMPT = """
你是 Social Lab 的 AnalysisAgent。

你的任务是诊断用户表达，不负责预测成功率，也不负责最终完整改写。

你必须：
1. 指出用户表达中的优点；
2. 指出具体问题和关键风险；
3. 找出当前最核心的沟通瓶颈；
4. 对最需要修改的轮次给出 turn_diagnostics；
5. 尽量引用用户原话；
6. 结合 PredictionAgent 的主要影响因素，但不要篡改其成功评分；
7. 不要把“主要影响因素”和“下一步建议”混在一起。

输出必须严格符合 AnalysisResult JSON Schema，不要输出 Markdown。
""".strip()

REWRITE_SYSTEM_PROMPT = """
你是 Social Lab 的 RewriteAgent。

你的任务是根据预测结果和诊断结果，生成用户可以直接使用的表达和下一步行动。

你必须输出：
1. suggested_rewrite：综合最推荐版本；
2. minimal_edit：尽量保留原意的最小修改版；
3. warmer_version：更温和、更照顾对方感受；
4. firmer_version：更坚定但尊重边界；
5. next_step_advice：下一步沟通建议；
6. do_not_say：下一轮应避免的表达。

原则：
- 不操控、威胁、欺骗、道德绑架或施压；
- 不重复 PredictionAgent 的成功率计算；
- 推荐改写和下一步建议应放在同一报告区域；
- 话术自然、具体、低压力并保留对方选择空间。

输出必须严格符合 RewriteResult JSON Schema，不要输出 Markdown。
""".strip()


class AnalysisAgent:
    async def run(
        self,
        *,
        request: ReportRequest,
        prediction: PredictionResult,
    ) -> AnalysisResult:
        result = await generate_structured(
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            user_prompt=self._build_prompt(request, prediction),
            output_model=AnalysisResult,
            temperature=0.25,
        )
        return self.post_process(result, request)

    def post_process(
        self,
        result: AnalysisResult,
        request: ReportRequest,
    ) -> AnalysisResult:
        result.strengths = _normalize_list(
            result.strengths,
            defaults=["能够主动表达当前沟通目标。"],
            max_items=5,
        )
        result.problems = _normalize_list(
            result.problems,
            defaults=["部分表达仍需补充具体背景、时间或可执行方案。"],
            max_items=5,
        )
        result.key_risks = _normalize_list(
            result.key_risks,
            defaults=["如果继续施压或重复请求，对方可能降低互动意愿。"],
            max_items=5,
        )
        result.primary_bottleneck = _clean_text(
            result.primary_bottleneck,
            "当前核心瓶颈是表达信息不足，或没有充分回应对方顾虑。",
            320,
        )
        result.turn_diagnostics = self._normalize_diagnostics(
            result.turn_diagnostics,
            message_count=len(request.messages),
        )

        if not _has_user_messages(request.messages):
            result.key_risks = _normalize_list(
                [
                    *result.key_risks,
                    "尚未形成有效模拟对话，当前诊断只能作为初步判断。",
                ],
                defaults=[],
                max_items=5,
            )
        return result

    def _build_prompt(
        self,
        request: ReportRequest,
        prediction: PredictionResult,
    ) -> str:
        return f"""
请输出 AnalysisResult。

{_build_base_context(request)}

【PredictionAgent 结果】
{_to_pretty_json(prediction.model_dump())}

请重点分析：
- 哪些用户原话推动了目标；
- 哪些用户原话带来压力、模糊、责任逃避或边界风险；
- 当前最需要修正的一个核心瓶颈；
- turn_diagnostics 最多 5 条；
- 不要在问题列表中重复输出成功率公式；
- 不要生成最终完整话术。
""".strip()

    @staticmethod
    def _normalize_diagnostics(
        diagnostics: list[TurnDiagnostic],
        *,
        message_count: int,
    ) -> list[TurnDiagnostic]:
        cleaned: list[TurnDiagnostic] = []
        for item in diagnostics[:5]:
            item.turn_index = max(1, min(max(1, message_count), int(item.turn_index)))
            item.issue_type = _clean_text(item.issue_type, "表达需要优化", 80)
            item.evidence_quote = _clean_text(
                item.evidence_quote,
                "未找到明确原话证据。",
                180,
            )
            item.target_likely_feeling = _clean_text(
                item.target_likely_feeling,
                "对方可能需要更多背景或更低压力的表达。",
                220,
            )
            item.relationship_impact = _clean_text(
                item.relationship_impact,
                "可能降低继续沟通或配合的意愿。",
                220,
            )
            item.fix_direction = _clean_text(
                item.fix_direction,
                "补充具体事实、回应顾虑并保留选择空间。",
                220,
            )
            cleaned.append(item)

        cleaned.sort(key=lambda item: item.turn_index)
        return cleaned


class RewriteAgent:
    async def run(
        self,
        *,
        request: ReportRequest,
        prediction: PredictionResult,
        analysis: AnalysisResult,
    ) -> RewriteResult:
        result = await generate_structured(
            system_prompt=REWRITE_SYSTEM_PROMPT,
            user_prompt=self._build_prompt(request, prediction, analysis),
            output_model=RewriteResult,
            temperature=0.30,
        )
        return self.post_process(result, request)

    def post_process(
        self,
        result: RewriteResult,
        request: ReportRequest,
    ) -> RewriteResult:
        default = _default_rewrite(request)
        result.suggested_rewrite = _clean_text(
            result.suggested_rewrite,
            default,
            900,
        )
        result.minimal_edit = _clean_text(
            result.minimal_edit,
            result.suggested_rewrite,
            600,
        )
        result.warmer_version = _clean_text(
            result.warmer_version,
            result.suggested_rewrite,
            600,
        )
        result.firmer_version = _clean_text(
            result.firmer_version,
            result.suggested_rewrite,
            600,
        )
        result.next_step_advice = _clean_text(
            result.next_step_advice,
            "下一步先回应对方最新顾虑，再提出一个具体且可拒绝的小步骤。",
            700,
        )
        result.do_not_say = _normalize_list(
            result.do_not_say,
            defaults=["不要使用命令、威胁、道德绑架或要求立即表态的表达。"],
            max_items=5,
        )
        return result

    def _build_prompt(
        self,
        request: ReportRequest,
        prediction: PredictionResult,
        analysis: AnalysisResult,
    ) -> str:
        return f"""
请输出 RewriteResult。

{_build_base_context(request)}

【PredictionAgent 结果】
{_to_pretty_json(prediction.model_dump())}

【AnalysisAgent 结果】
{_to_pretty_json(analysis.model_dump())}

请生成可以直接使用的表达。
推荐改写与 next_step_advice 必须相互一致：
- 如果预测显示压力高，降低催促与立即表态要求；
- 如果清晰度低，补充背景、时间和具体方案；
- 如果对方明确拒绝，优先暂停或修复，不继续强推；
- 如果对方条件接受，回应其前置条件。
""".strip()


class ReportAssembler:
    def run(
        self,
        *,
        request: ReportRequest,
        prediction: PredictionResult,
        analysis: AnalysisResult,
        rewrite: RewriteResult,
    ) -> ReportResponse:
        return ReportResponse(
            success_probability=prediction.success_probability,
            probability_low=prediction.probability_low,
            probability_high=prediction.probability_high,
            confidence_score=prediction.confidence_score,
            confidence=prediction.confidence,
            evidence_sufficiency=prediction.evidence_sufficiency,
            likely_outcome=_clean_text(
                prediction.likely_outcome,
                _default_likely_outcome(prediction.success_probability),
                900,
            ),
            probability_reasoning=prediction.probability_reasoning,
            outcome_distribution=prediction.outcome_distribution,
            main_influence_factors=prediction.main_influence_factors,
            prediction_trace=prediction.calculation_trace,
            calibration_version=prediction.calibration_version,
            strengths=analysis.strengths,
            problems=self._build_problems(analysis),
            key_risks=self._build_risks(analysis, prediction),
            suggested_rewrite=rewrite.suggested_rewrite,
            next_step_advice=self._build_next_step(analysis, rewrite),
        )

    @staticmethod
    def _build_problems(analysis: AnalysisResult) -> list[str]:
        problems = list(analysis.problems)
        for diagnostic in analysis.turn_diagnostics[:3]:
            problems.append(
                f"第 {diagnostic.turn_index} 轮：{diagnostic.issue_type}。"
                f"原话“{diagnostic.evidence_quote}”。"
                f"修正方向：{diagnostic.fix_direction}"
            )
        return _normalize_list(
            problems,
            defaults=["部分表达仍需补充具体背景、时间或可执行方案。"],
            max_items=5,
        )

    @staticmethod
    def _build_risks(
        analysis: AnalysisResult,
        prediction: PredictionResult,
    ) -> list[str]:
        risks = list(analysis.key_risks)

        for factor in prediction.main_influence_factors:
            if factor.direction == "negative" and factor.importance >= 4:
                risks.append(
                    f"{factor.factor_name}可能明显拉低模拟成功评分："
                    f"{factor.explanation}"
                )

        return _normalize_list(
            risks,
            defaults=["如果继续施压，对方可能降低互动意愿。"],
            max_items=5,
        )

    @staticmethod
    def _build_next_step(
        analysis: AnalysisResult,
        rewrite: RewriteResult,
    ) -> str:
        avoid = "；".join(rewrite.do_not_say[:3])
        return _clean_text(
            (
                f"{rewrite.next_step_advice}\n\n"
                f"优先修正：{analysis.primary_bottleneck}\n\n"
                f"避免表达：{avoid}\n\n"
                f"备选版本：\n"
                f"1. 最小修改：{rewrite.minimal_edit}\n"
                f"2. 更温和：{rewrite.warmer_version}\n"
                f"3. 更坚定：{rewrite.firmer_version}"
            ),
            rewrite.next_step_advice,
            1500,
        )


class CoachAgent:
    """
    报告编排入口。

    PredictionAgent 先产生可解释预测；
    AnalysisAgent 只负责诊断；
    RewriteAgent 只负责改写与下一步；
    ReportAssembler 保持职责边界并输出兼容字段。
    """

    def __init__(self) -> None:
        self.prediction_agent = PredictionAgent()
        self.analysis_agent = AnalysisAgent()
        self.rewrite_agent = RewriteAgent()
        self.report_assembler = ReportAssembler()

    async def run(self, request: ReportRequest) -> ReportResponse:
        started = time.perf_counter()

        phase = time.perf_counter()
        prediction = await self.prediction_agent.run(request)
        logger.info(
            "PredictionAgent finished in %.2fs",
            time.perf_counter() - phase,
        )

        phase = time.perf_counter()
        analysis = await self.analysis_agent.run(
            request=request,
            prediction=prediction,
        )
        logger.info(
            "AnalysisAgent finished in %.2fs",
            time.perf_counter() - phase,
        )

        phase = time.perf_counter()
        rewrite = await self.rewrite_agent.run(
            request=request,
            prediction=prediction,
            analysis=analysis,
        )
        logger.info(
            "RewriteAgent finished in %.2fs",
            time.perf_counter() - phase,
        )

        report = self.report_assembler.run(
            request=request,
            prediction=prediction,
            analysis=analysis,
            rewrite=rewrite,
        )
        logger.info(
            "CoachAgent report finished in %.2fs",
            time.perf_counter() - started,
        )
        return report


def _build_base_context(request: ReportRequest) -> str:
    messages = "\n".join(
        f"{index}. {message.role}: {message.content}"
        for index, message in enumerate(request.messages, start=1)
    ) or "暂无历史对话。"

    dynamics = (
        _to_pretty_json(request.current_dynamics.model_dump())
        if request.current_dynamics is not None
        else "未提供"
    )
    history = (
        _to_pretty_json(
            [item.model_dump() for item in request.dynamics_history[-5:]]
        )
        if request.dynamics_history
        else "未提供"
    )

    return f"""
【场景类型】
{request.scenario}

【用户沟通目标】
{request.goal}

【期望结果】
{request.outcome or "未提供"}

【目标人物画像】
{_to_pretty_json(request.persona.model_dump())}

【完整模拟对话】
{messages}

【当前 Dynamics】
{dynamics}

【最近 Dynamics 趋势】
{history}
""".strip()


def _to_pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


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
        item = str(value).strip()
        if item and item not in cleaned:
            cleaned.append(item[:260])

    for default in defaults:
        if default and default not in cleaned:
            cleaned.append(default)

    return cleaned[:max_items]


def _clean_text(
    value: object,
    default: str,
    max_length: int,
) -> str:
    text = value.strip() if isinstance(value, str) else ""
    text = text or default
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "…"


def _default_likely_outcome(score: int) -> str:
    if score >= 70:
        return "当前模拟更可能继续推进或进入具体协商。"
    if score >= 45:
        return "当前模拟更可能出现犹豫、补充信息要求或附加条件。"
    return "当前模拟更可能出现拒绝、延后回应或降低互动意愿。"


def _default_rewrite(request: ReportRequest) -> str:
    last_user_message = _last_user_message(request.messages)
    if last_user_message:
        return (
            f"我想重新更清楚地表达一下：{last_user_message}\n\n"
            "如果这件事对你来说不方便，也可以直接告诉我；"
            "我想先把背景、我的责任和可执行方案说明清楚。"
        )

    if request.scenario == "advisor":
        return (
            "老师您好，我想说明一下目前的情况、已经采取的处理措施，"
            "以及接下来的具体计划。想请您看看这个安排是否可行，"
            "如果不合适我会根据您的意见调整。"
        )
    if request.scenario == "work":
        return (
            "我想先同步这件事的背景、当前影响和建议方案。"
            "也想确认您这边的优先级或限制，我可以据此调整。"
        )
    return (
        "我想认真说明一下这件事。我的本意不是给你压力，"
        "而是把我的想法说清楚，也听听你的感受和边界。"
    )
