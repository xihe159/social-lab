from __future__ import annotations

from typing import Iterable, List, Tuple

from app.agents.prompts import SAFETY_SYSTEM_PROMPT, build_safety_user_prompt
from app.llm.client import LLMClientError, generate_structured
from app.schemas.safety import SafetyCheckRequest, SafetyCheckResponse


class SafetyAgent:
    """
    SafetyAgent 负责在 PersonaAgent / SimulationAgent 等主流程前进行安全检查。

    设计原则：
    1. 先做轻量规则检查，明显高风险时直接 block，避免不必要的 LLM 调用。
    2. 中低风险或不确定时调用 LLM 做结构化判断。
    3. LLM 调用失败时回退到规则结果，不让安全模块拖垮主流程。
    """

    HIGH_RISK_KEYWORDS: Tuple[Tuple[str, str], ...] = (
        ("manipulation", "操控"),
        ("manipulation", "PUA"),
        ("manipulation", "让他必须"),
        ("manipulation", "逼他"),
        ("manipulation", "威胁"),
        ("manipulation", "否则"),
        ("manipulation", "报复"),
        ("manipulation", "欺骗"),
        ("manipulation", "骗他"),
        ("manipulation", "套话"),
        ("harassment", "骚扰"),
        ("harassment", "一直发"),
        ("harassment", "不停打电话"),
        ("harassment", "堵他"),
        ("harassment", "跟踪"),
        ("harassment", "人肉"),
        ("harassment", "曝光"),
        ("privacy", "身份证"),
        ("privacy", "银行卡"),
        ("privacy", "密码"),
        ("privacy", "验证码"),
        ("privacy", "家庭住址"),
        ("violence", "打他"),
        ("violence", "杀"),
        ("self_harm", "自杀"),
        ("self_harm", "伤害自己"),
    )

    PRIVACY_KEYWORDS: Tuple[Tuple[str, str], ...] = (
        ("privacy", "手机号"),
        ("privacy", "电话"),
        ("privacy", "邮箱"),
        ("privacy", "地址"),
        ("privacy", "定位"),
        ("privacy", "聊天记录"),
    )

    MEDIUM_RISK_KEYWORDS: Tuple[Tuple[str, str], ...] = (
        ("pressure", "催"),
        ("pressure", "立刻"),
        ("pressure", "马上"),
        ("pressure", "必须答应"),
        ("high_stakes", "法律"),
        ("high_stakes", "诊断"),
        ("high_stakes", "心理疾病"),
        ("high_stakes", "抑郁症"),
        ("high_stakes", "药"),
    )

    async def run(self, request: SafetyCheckRequest) -> SafetyCheckResponse:
        rule_result = self._rule_check(request)

        # 明显高风险直接阻断，不继续调用 LLM。
        if rule_result.risk_level == "high" or rule_result.action == "block":
            return rule_result

        try:
            payload = request.model_dump()
            result = await generate_structured(
                system_prompt=SAFETY_SYSTEM_PROMPT,
                user_prompt=build_safety_user_prompt(payload),
                output_model=SafetyCheckResponse,
            )
            return self.post_process(result=result, rule_result=rule_result)

        except LLMClientError as exc:
            print("[SafetyAgent] LLM failed, fallback to rule result:", str(exc))
            return rule_result

        except Exception as exc:
            print("[SafetyAgent] unexpected failed, fallback to rule result:", repr(exc))
            return rule_result

    def _rule_check(self, request: SafetyCheckRequest) -> SafetyCheckResponse:
        text = self._collect_text(request)
        risk_types: List[str] = []
        redacted_fields: List[str] = []

        for risk_type, keyword in self.HIGH_RISK_KEYWORDS:
            if keyword.lower() in text.lower():
                self._append_unique(risk_types, risk_type)

        for risk_type, keyword in self.PRIVACY_KEYWORDS:
            if keyword.lower() in text.lower():
                self._append_unique(risk_types, risk_type)
                self._append_unique(redacted_fields, keyword)

        if any(risk in risk_types for risk in ["manipulation", "harassment", "violence", "self_harm"]):
            return SafetyCheckResponse(
                allowed=False,
                risk_level="high",
                action="block",
                risk_types=risk_types,
                user_notice="当前输入包含操控、骚扰、暴力或自伤等高风险意图，已停止继续模拟。可以改为练习如何清晰表达需求、尊重对方边界，并接受对方拒绝。",
                safe_rewrite_hint="请将目标改写为：如何礼貌、诚实地表达需求，同时尊重对方选择。",
                should_redact=len(redacted_fields) > 0,
                redacted_fields=redacted_fields,
            )

        medium_risks: List[str] = []
        for risk_type, keyword in self.MEDIUM_RISK_KEYWORDS:
            if keyword.lower() in text.lower():
                self._append_unique(medium_risks, risk_type)

        if medium_risks or redacted_fields:
            combined = risk_types + [item for item in medium_risks if item not in risk_types]
            return SafetyCheckResponse(
                allowed=True,
                risk_level="medium",
                action="warn",
                risk_types=combined,
                user_notice="当前输入可能包含施压、隐私或高风险建议倾向。系统会继续模拟，但建议保持诚实、克制，并避免透露或利用敏感隐私。",
                safe_rewrite_hint="可以改为更安全的表达：说明事实、表达感受、提出请求，并明确尊重对方决定。",
                should_redact=len(redacted_fields) > 0,
                redacted_fields=redacted_fields,
            )

        return SafetyCheckResponse(
            allowed=True,
            risk_level="none",
            action="allow",
            risk_types=[],
            user_notice="",
            safe_rewrite_hint="",
            should_redact=False,
            redacted_fields=[],
        )

    def post_process(
        self,
        *,
        result: SafetyCheckResponse,
        rule_result: SafetyCheckResponse,
    ) -> SafetyCheckResponse:
        risk_types = self._clean_list(result.risk_types)
        redacted_fields = self._clean_list(result.redacted_fields)

        # 规则层发现的风险不能被 LLM 完全抹掉。
        for risk_type in rule_result.risk_types:
            self._append_unique(risk_types, risk_type)
        for field in rule_result.redacted_fields:
            self._append_unique(redacted_fields, field)

        risk_level = result.risk_level
        action = result.action
        allowed = result.allowed

        if rule_result.risk_level == "medium" and risk_level == "none":
            risk_level = "medium"
            action = "warn"
            allowed = True

        if risk_level == "high" or action == "block":
            allowed = False
            action = "block"
        elif risk_level == "medium" and action == "allow":
            action = "warn"
            allowed = True
        elif risk_level in ("none", "low") and action == "block":
            action = "warn"
            allowed = True

        user_notice = result.user_notice.strip()
        safe_rewrite_hint = result.safe_rewrite_hint.strip()

        if action == "block" and not user_notice:
            user_notice = "当前输入包含较高安全风险，已停止继续模拟。"
        if action in ("warn", "block") and not safe_rewrite_hint:
            safe_rewrite_hint = "建议改为练习如何礼貌、诚实地表达需求，并尊重对方选择。"

        return SafetyCheckResponse(
            allowed=allowed,
            risk_level=risk_level,
            action=action,
            risk_types=risk_types,
            user_notice=user_notice,
            safe_rewrite_hint=safe_rewrite_hint,
            should_redact=bool(result.should_redact or rule_result.should_redact or redacted_fields),
            redacted_fields=redacted_fields,
        )

    def _collect_text(self, request: SafetyCheckRequest) -> str:
        parts = [
            request.context,
            request.scenario,
            request.goal,
            request.outcome,
            request.role,
            request.relation,
            request.habit,
            request.chatLog,
            request.user_message,
            str(request.persona),
            str(request.messages),
            str(request.current_memory),
        ]
        return "\n".join(part for part in parts if part)

    def _clean_list(self, values: Iterable[str]) -> List[str]:
        result: List[str] = []
        for value in values:
            text = str(value).strip()
            if text and text not in result:
                result.append(text)
        return result

    def _append_unique(self, values: List[str], value: str) -> None:
        value = value.strip()
        if value and value not in values:
            values.append(value)
