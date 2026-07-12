from __future__ import annotations

from typing import Any

from app.agents.prompts import PERSONA_SYSTEM_PROMPT, build_persona_user_prompt
from app.llm.client import generate_structured
from app.schemas.persona import (
    PersonaCreateRequest,
    PersonaCreateResponse,
    PersonaEvidence,
)


class PersonaAgent:
    """
    PersonaAgent 负责根据用户输入生成目标人物画像。

    设计原则：
    1. Agent 层只负责业务流程，不直接接触 OpenAI / Qwen SDK。
    2. LLM 调用统一交给 app.llm.client.generate_structured。
    3. 输出必须是 PersonaCreateResponse，并经过业务级 post_process 修正。
    """

    async def run(self, request: PersonaCreateRequest) -> PersonaCreateResponse:
        """
        生成目标人物画像。

        Args:
            request: 前端提交的人物建模信息。

        Returns:
            PersonaCreateResponse: 可直接返回给 API 层的结构化人物画像。
        """

        payload = request.model_dump()

        result = await generate_structured(
            system_prompt=PERSONA_SYSTEM_PROMPT,
            user_prompt=build_persona_user_prompt(payload),
            output_model=PersonaCreateResponse,
        )

        return self.post_process(result=result, request=request)

    def post_process(
        self,
        *,
        result: PersonaCreateResponse,
        request: PersonaCreateRequest,
    ) -> PersonaCreateResponse:
        """
        对 LLM 已经通过 Pydantic 校验的结果进行业务级修正。

        Pydantic 负责结构合法性，例如字段是否存在、数值是否越界。
        post_process 负责业务合理性，例如：
        - 导师 / 领导关系的 authority 不应过低；
        - 没有聊天记录时 confidence 不应过高；
        - strategy、rules、evidence 等关键字段不应为空。
        """

        self._normalize_persona_text_fields(result)
        self._normalize_relationship_state(result, request)
        self._normalize_opening_message(result, request)
        self._normalize_communication_rules(result)
        self._normalize_evidence(result, request)
        self._normalize_assumptions(result, request)
        self._normalize_confidence(result, request)

        return result

    def _normalize_persona_text_fields(self, result: PersonaCreateResponse) -> None:
        persona = result.persona

        persona.title = self._clean_text(
            persona.title,
            default="基于用户输入生成的沟通模拟画像",
        )
        persona.style = self._clean_text(
            persona.style,
            default="谨慎、结合关系背景进行回应",
        )
        persona.speed = self._clean_text(
            persona.speed,
            default="正常",
        )
        persona.focus = self._clean_text(
            persona.focus,
            default="关注沟通请求是否合理，以及用户是否尊重自己的处境。",
        )
        persona.risk = self._clean_text(
            persona.risk,
            default="表达过于直接、催促或缺少背景说明，可能引发对方防御。",
        )
        persona.strategy = self._clean_text(
            persona.strategy,
            default="先说明背景，再提出具体请求，同时降低对方的行动成本。",
        )

    def _normalize_relationship_state(
        self,
        result: PersonaCreateResponse,
        request: PersonaCreateRequest,
    ) -> None:
        state = result.persona.state

        # 基础数值保护。虽然 Pydantic 已经校验初始结果，
        # 但后续业务修正会直接赋值，因此这里再次 clamp。
        state.trust = self._clamp(state.trust, 0, 100)
        state.respect = self._clamp(state.respect, 0, 100)
        state.familiarity = self._clamp(state.familiarity, 0, 100)
        state.affinity = self._clamp(state.affinity, 0, 100)
        state.authority = self._clamp(state.authority, 0, 100)
        state.emotional = self._clamp(state.emotional, -100, 100)

        text = self._join_request_text(request)
        title = result.persona.title

        advisor_keywords = ["导师", "老师", "教授", "课题组", "advisor", "supervisor"]
        leader_keywords = ["领导", "上级", "老板", "主管", "经理", "leader", "manager", "boss"]

        if request.scenario == "advisor" or self._contains_any(text + title, advisor_keywords):
            state.authority = max(state.authority, 60)
            state.respect = max(state.respect, 50)

        if request.scenario == "work" or self._contains_any(text + title, leader_keywords):
            state.authority = max(state.authority, 45)
            state.respect = max(state.respect, 45)

        # 社交场景中，如果没有明显权威关键词，不要让权威距离过高。
        if request.scenario == "social" and not self._contains_any(text + title, advisor_keywords + leader_keywords):
            state.authority = min(state.authority, 60)

        # 用户提供了沟通习惯或聊天记录，说明双方并非完全陌生。
        if request.habit.strip() or request.chatLog.strip():
            state.familiarity = max(state.familiarity, 35)

        # 如果关系描述明显偏亲近，可以适当提高 familiarity / affinity 下限。
        close_keywords = ["朋友", "同学", "室友", "伴侣", "家人", "熟悉", "friend", "classmate", "roommate"]
        if self._contains_any(request.relation, close_keywords):
            state.familiarity = max(state.familiarity, 45)
            state.affinity = max(state.affinity, 35)

    def _normalize_opening_message(
        self,
        result: PersonaCreateResponse,
        request: PersonaCreateRequest,
    ) -> None:
        result.opening_message = self._clean_text(
            result.opening_message,
            default=self._default_opening_message(request),
        )

    def _normalize_communication_rules(self, result: PersonaCreateResponse) -> None:
        default_rules = [
            "始终以目标人物身份回应，不跳出角色。",
            "回复应符合人物画像、关系状态和当前沟通场景。",
            "不要直接替用户做沟通教学，除非对方角色本身会这样回应。",
            "对用户表达中的压力、冒犯、模糊请求保持符合角色的自然反应。",
        ]

        cleaned_rules = [rule.strip() for rule in result.communication_rules if rule and rule.strip()]

        for rule in default_rules:
            if rule not in cleaned_rules:
                cleaned_rules.append(rule)

        result.communication_rules = cleaned_rules[:8]

    def _normalize_evidence(
        self,
        result: PersonaCreateResponse,
        request: PersonaCreateRequest,
    ) -> None:
        valid_sources = {"goal", "outcome", "role", "relation", "habit", "chatLog"}

        cleaned: list[PersonaEvidence] = []
        for item in result.evidence:
            if item.source not in valid_sources:
                continue

            quote = item.quote.strip()
            inference = item.inference.strip()
            if not quote or not inference:
                continue

            cleaned.append(
                PersonaEvidence(
                    source=item.source,
                    quote=quote[:300],
                    inference=inference[:300],
                )
            )

        existing_sources = {item.source for item in cleaned}

        fallback_items = self._build_fallback_evidence(request)
        for item in fallback_items:
            if item.source not in existing_sources:
                cleaned.append(item)
                existing_sources.add(item.source)

        # evidence 不宜过长，否则前端展示和调试都不方便。
        result.evidence = cleaned[:6]

    def _normalize_assumptions(
        self,
        result: PersonaCreateResponse,
        request: PersonaCreateRequest,
    ) -> None:
        assumptions = [item.strip() for item in result.assumptions if item and item.strip()]

        if not request.chatLog.strip():
            assumptions.append("用户未提供完整聊天记录，画像主要基于目标、关系和背景描述推断。")

        if not request.habit.strip():
            assumptions.append("用户未提供对方沟通习惯，回复风格存在一定假设成分。")

        # 去重并限制数量。
        result.assumptions = self._dedupe_keep_order(assumptions)[:6]

    def _normalize_confidence(
        self,
        result: PersonaCreateResponse,
        request: PersonaCreateRequest,
    ) -> None:
        result.confidence = float(max(0.0, min(1.0, result.confidence)))

        # 没有聊天记录时，不能过度自信。
        if not request.chatLog.strip():
            result.confidence = min(result.confidence, 0.75)

        # 如果用户输入信息较少，进一步降低可信度上限。
        meaningful_inputs = [
            request.goal.strip(),
            request.outcome.strip(),
            request.role.strip(),
            request.relation.strip(),
            request.habit.strip(),
            request.chatLog.strip(),
        ]
        non_empty_count = sum(1 for item in meaningful_inputs if item)

        if non_empty_count <= 3:
            result.confidence = min(result.confidence, 0.65)

        if len(result.evidence) <= 2:
            result.confidence = min(result.confidence, 0.70)

    def _build_fallback_evidence(self, request: PersonaCreateRequest) -> list[PersonaEvidence]:
        candidates: list[tuple[str, str, str]] = [
            ("goal", request.goal, "用户沟通目标是构建人物画像和策略的主要依据。"),
            ("outcome", request.outcome, "用户期待结果可反映本次沟通的成败标准。"),
            ("role", request.role, "目标人物身份会影响其权威感、关注点和回应方式。"),
            ("relation", request.relation, "双方关系会影响熟悉度、亲近感和表达边界。"),
            ("habit", request.habit, "对方沟通习惯可用于推断其回复风格。"),
            ("chatLog", request.chatLog, "聊天记录可作为判断对方语气和关系状态的直接依据。"),
        ]

        evidence: list[PersonaEvidence] = []
        for source, quote, inference in candidates:
            quote = quote.strip()
            if not quote:
                continue
            evidence.append(
                PersonaEvidence(
                    source=source,  # type: ignore[arg-type]
                    quote=quote[:300],
                    inference=inference,
                )
            )

        return evidence

    def _default_opening_message(self, request: PersonaCreateRequest) -> str:
        if request.scenario == "advisor":
            return "你先说说目前具体遇到了什么问题，以及你希望我怎么配合。"
        if request.scenario == "work":
            return "你可以先把事情背景和你希望达成的结果说清楚。"
        if request.scenario == "social":
            return "嗯，你想和我聊什么？"
        return "你可以先说说具体情况。"

    @staticmethod
    def _clean_text(value: str, *, default: str) -> str:
        if value is None:
            return default
        value = str(value).strip()
        return value if value else default

    @staticmethod
    def _clamp(value: int, low: int, high: int) -> int:
        return max(low, min(high, int(value)))

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        lowered = text.lower()
        return any(keyword.lower() in lowered for keyword in keywords)

    @staticmethod
    def _join_request_text(request: PersonaCreateRequest) -> str:
        return "\n".join(
            [
                request.goal,
                request.outcome,
                request.role,
                request.relation,
                request.habit,
                request.chatLog,
            ]
        )

    @staticmethod
    def _dedupe_keep_order(items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result
