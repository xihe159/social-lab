from __future__ import annotations

import hashlib
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.llm.client import generate_structured
from app.schemas.memory import (
    MemoryEvidence,
    MemoryItem,
    MemoryUpdateRequest,
    MemoryUpdateResponse,
    SessionMemory,
)


# =========================================================
# 1. Extractor 内部结构化输出
# =========================================================

ExtractedCategory = Literal[
    "user_dialogue_pattern",
    "target_sensitive_point",
    "focus_issue",
    "key_info_repetition_risk",
    "resolved_point",
    "important_event",
]


class ExtractedMemoryCandidate(BaseModel):
    """
    MemoryExtractor 提取出来的候选记忆。
    这是 LLM 输出结构，不直接作为最终 memory 保存。
    """

    model_config = ConfigDict(extra="forbid")

    category: ExtractedCategory = Field(description="候选记忆类型")
    content: str = Field(description="候选记忆内容")
    importance: int = Field(ge=1, le=5, description="重要程度")
    confidence: Literal["low", "medium", "high"] = Field(description="置信度")
    evidence_role: Literal["user", "target"] = Field(description="证据来源")
    evidence_quote: str = Field(description="支持这条记忆的原话证据")
    tags: list[str] = Field(description="搜索标签")


class MemoryExtractionResult(BaseModel):
    """
    MemoryExtractor 的结构化输出。
    """

    model_config = ConfigDict(extra="forbid")

    turn_summary: str = Field(description="本轮对话摘要")
    candidates: list[ExtractedMemoryCandidate] = Field(description="候选记忆列表")
    resolved_focus: list[str] = Field(description="本轮被解决或部分解决的问题")
    unresolved_focus: list[str] = Field(description="本轮后仍未解决的问题")
    repetition_risks: list[str] = Field(description="关键信息重复或遗漏风险")
    next_focus: str = Field(description="下一轮最应该关注的重点")
    memory_reason: str = Field(description="本轮记忆更新理由")


MEMORY_EXTRACTOR_SYSTEM_PROMPT = """
你是 Social Lab 的 MemoryExtractor。
你的任务不是写报告，也不是给用户建议，而是从一轮模拟对话中提取“会话短期记忆候选项”。

你只记录当前 session 内对后续模拟、策略和报告有用的信息。

必须重点识别以下四类内容：
1. 用户对话模式：
   例如表达是否模糊、是否急于推进、是否重复解释、是否缺少具体方案、
   是否能承认责任、是否能降低对方成本、是否给对方选择空间。

2. 目标人物敏感点：
   例如目标人物是否在意时间成本、责任边界、尊重感、具体计划、
   是否被催促、是否需要更多证据、是否担心用户只是口头承诺。

3. 对话聚焦问题：
   例如当前对话真正卡住的问题是什么，下一轮最应该补充什么。

4. 关键信息重复风险：
   例如用户是否重复解释同一件事但没有回应对方顾虑，
   是否多次遗漏关键事实，是否反复要求对方表态。

记忆原则：
- 不保存手机号、住址、身份证号、账号、精确地址等敏感隐私。
- 不把模拟推断说成现实事实。
- 每个候选记忆必须有 evidence_quote。
- 不要输出 Markdown。
- 输出必须严格符合 MemoryExtractionResult JSON Schema。
""".strip()


# =========================================================
# 2. 通用工具函数
# =========================================================

def _get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _truncate(text: str, limit: int) -> str:
    text = _safe_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _dedupe_texts(values: list[str], *, limit: int, item_limit: int = 220) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        text = _truncate(_safe_text(value), item_limit)
        if not text or text in seen:
            continue
        result.append(text)
        seen.add(text)

    return result[:limit]


def _turn_index(request: MemoryUpdateRequest) -> int:
    """
    估算当前轮次。

    如果 request.messages 已经包含当前 user_message，
    就直接使用已有 user 消息数量；
    如果不包含当前 user_message，就在历史 user 数量基础上 +1。
    """

    user_count = 0
    current_user_message = _safe_text(request.user_message)

    current_message_already_in_history = False

    for message in request.messages or []:
        role = _get_value(message, "role", "")
        content = _safe_text(_get_value(message, "content", ""))

        if role == "user":
            user_count += 1

            if current_user_message and content == current_user_message:
                current_message_already_in_history = True

    if not current_message_already_in_history:
        user_count += 1

    return max(1, user_count)


def _make_memory_id(category: str, content: str) -> str:
    raw = f"{category}:{content.strip().lower()}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"mem_{digest}"


def _build_extractor_prompt(request: MemoryUpdateRequest) -> str:
    current_memory = (
        request.current_memory.model_dump(mode="json")
        if request.current_memory
        else None
    )

    return f"""
请根据以下本轮模拟对话，提取短期会话记忆候选项。

【场景】
{request.scenario}

【用户沟通目标】
{request.goal}

【用户期待结果】
{request.outcome or "未提供"}

【目标人物画像】
{request.persona}

【上一轮 memory】
{current_memory or "暂无"}

【用户本轮发言】
{request.user_message}

【目标人物本轮回复】
{request.target_reply}

【本轮关系状态变化 state_delta】
{request.state_delta}

【本轮风险标记 risk_flags】
{request.risk_flags}

请输出：
1. 本轮摘要；
2. 3 到 8 条候选记忆；
3. 已解决问题；
4. 未解决问题；
5. 关键信息重复风险；
6. 下一轮重点；
7. 本轮更新理由。

特别注意：
- 候选记忆必须覆盖用户对话模式、目标人物敏感点、对话聚焦问题、关键信息重复风险中的重要项；
- 不要保存真实敏感隐私；
- 每条候选记忆必须有 evidence_quote。
""".strip()


# =========================================================
# 3. MemoryExtractor
# =========================================================

class MemoryExtractor:
    """
    从本轮对话中提取候选记忆。

    这是唯一直接调用 LLM 的部分。
    """

    async def run(self, request: MemoryUpdateRequest) -> MemoryExtractionResult:
        result = await generate_structured(
            system_prompt=MEMORY_EXTRACTOR_SYSTEM_PROMPT,
            user_prompt=_build_extractor_prompt(request),
            output_model=MemoryExtractionResult,
            temperature=0.2,
        )
        return self.post_process(result, request)

    def post_process(
        self,
        result: MemoryExtractionResult,
        request: MemoryUpdateRequest,
    ) -> MemoryExtractionResult:
        result.turn_summary = _truncate(
            result.turn_summary,
            400,
        ) or self._fallback_turn_summary(request)

        cleaned_candidates: list[ExtractedMemoryCandidate] = []

        for candidate in result.candidates or []:
            candidate.content = _truncate(candidate.content, 240)
            candidate.evidence_quote = _truncate(candidate.evidence_quote, 180)
            candidate.tags = _dedupe_texts(candidate.tags, limit=6, item_limit=40)
            candidate.importance = max(1, min(5, int(candidate.importance)))

            if not candidate.content or not candidate.evidence_quote:
                continue

            cleaned_candidates.append(candidate)

        if not cleaned_candidates:
            cleaned_candidates = self._fallback_candidates(request)

        result.candidates = cleaned_candidates[:8]
        result.resolved_focus = _dedupe_texts(result.resolved_focus, limit=5)
        result.unresolved_focus = _dedupe_texts(result.unresolved_focus, limit=5)
        result.repetition_risks = _dedupe_texts(result.repetition_risks, limit=5)
        result.next_focus = _truncate(
            result.next_focus,
            300,
        ) or "下一轮优先回应对方最在意的问题，并补充具体事实、时间安排和可执行方案。"
        result.memory_reason = _truncate(
            result.memory_reason,
            300,
        ) or "已根据本轮用户表达、目标人物回复、状态变化和风险标记更新短期记忆。"

        return result

    def _fallback_turn_summary(self, request: MemoryUpdateRequest) -> str:
        return _truncate(
            f"用户本轮表达：{request.user_message}；目标人物回应：{request.target_reply}",
            400,
        )

    def _fallback_candidates(
        self,
        request: MemoryUpdateRequest,
    ) -> list[ExtractedMemoryCandidate]:
        return [
            ExtractedMemoryCandidate(
                category="important_event",
                content=f"用户提出：{_truncate(request.user_message, 120)}；目标人物回应：{_truncate(request.target_reply, 120)}",
                importance=3,
                confidence="medium",
                evidence_role="user",
                evidence_quote=_truncate(request.user_message, 160),
                tags=["本轮对话", "重要事件"],
            ),
            ExtractedMemoryCandidate(
                category="focus_issue",
                content="下一轮仍需围绕目标人物最关注的问题补充更具体的信息。",
                importance=3,
                confidence="medium",
                evidence_role="target",
                evidence_quote=_truncate(request.target_reply, 160),
                tags=["聚焦问题", "下一轮重点"],
            ),
        ]


# =========================================================
# 4. MemoryReducer
# =========================================================

class MemoryReducer:
    """
    负责压缩、合并、去重和控制 memory 长度。
    """

    CATEGORY_LIMITS = {
        "user_dialogue_pattern": 6,
        "target_sensitive_point": 6,
        "focus_issue": 6,
        "key_info_repetition_risk": 5,
        "resolved_point": 6,
        "important_event": 8,
    }

    def reduce(self, memory: SessionMemory) -> SessionMemory:
        memory.memory_items = self._merge_duplicate_items(memory.memory_items)
        memory.memory_items = self._limit_by_category(memory.memory_items)
        memory.memory_items = self._sort_items(memory.memory_items)
        return memory

    def _merge_duplicate_items(
        self,
        items: list[MemoryItem],
    ) -> list[MemoryItem]:
        merged: dict[str, MemoryItem] = {}

        for item in items:
            key = f"{item.category}:{item.content.strip().lower()}"

            if key not in merged:
                merged[key] = item
                continue

            existing = merged[key]
            existing.importance = max(existing.importance, item.importance)
            existing.last_seen_turn = max(existing.last_seen_turn, item.last_seen_turn)
            existing.seen_count += item.seen_count
            existing.tags = _dedupe_texts(existing.tags + item.tags, limit=8, item_limit=40)

            combined_evidence = existing.evidence + item.evidence
            existing.evidence = combined_evidence[-4:]

            if existing.confidence != "high" and item.confidence == "high":
                existing.confidence = "high"
            elif existing.confidence == "low" and item.confidence == "medium":
                existing.confidence = "medium"

        return list(merged.values())

    def _limit_by_category(
        self,
        items: list[MemoryItem],
    ) -> list[MemoryItem]:
        kept: list[MemoryItem] = []

        for category, limit in self.CATEGORY_LIMITS.items():
            category_items = [item for item in items if item.category == category]
            category_items = self._sort_items(category_items)
            kept.extend(category_items[:limit])

        return kept

    def _sort_items(
        self,
        items: list[MemoryItem],
    ) -> list[MemoryItem]:
        return sorted(
            items,
            key=lambda item: (
                item.status != "forgotten",
                item.importance,
                item.seen_count,
                item.last_seen_turn,
            ),
            reverse=True,
        )


# =========================================================
# 5. MemorySelector
# =========================================================

class MemorySelector:
    """
    为不同 Agent 选择不同的 memory context。

    第一阶段先实现能力，不强制接入其他 Agent。
    后续可以给 SimulationAgent / StrategyAgent / ReportAgent 使用。
    """

    def search(
        self,
        memory: SessionMemory,
        *,
        query: str = "",
        category: str | None = None,
        limit: int = 5,
    ) -> list[MemoryItem]:
        query = query.strip().lower()
        scored: list[tuple[int, MemoryItem]] = []

        for item in memory.memory_items:
            if item.status == "forgotten":
                continue

            if category and item.category != category:
                continue

            score = item.importance * 10 + item.seen_count * 3 + item.last_seen_turn

            if query:
                haystack = " ".join(
                    [
                        item.content,
                        " ".join(item.tags),
                        " ".join(e.quote for e in item.evidence),
                    ]
                ).lower()

                if query in haystack:
                    score += 30
                else:
                    # 简单关键词召回
                    for token in query.split():
                        if token and token in haystack:
                            score += 8

            scored.append((score, item))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def select_for_simulation(self, memory: SessionMemory) -> dict[str, Any]:
        return {
            "target_sensitive_points": [
                item.content
                for item in self.search(
                    memory,
                    category="target_sensitive_point",
                    limit=4,
                )
            ],
            "active_focus_issues": memory.active_focus_issues[:4],
            "repetition_risks": memory.key_info_repetition_risks[:3],
            "next_suggested_focus": memory.next_suggested_focus,
        }

    def select_for_strategy(self, memory: SessionMemory) -> dict[str, Any]:
        return {
            "user_dialogue_patterns": [
                item.content
                for item in self.search(
                    memory,
                    category="user_dialogue_pattern",
                    limit=4,
                )
            ],
            "target_sensitive_points": [
                item.content
                for item in self.search(
                    memory,
                    category="target_sensitive_point",
                    limit=4,
                )
            ],
            "focus_issues": memory.active_focus_issues[:4],
            "repetition_risks": memory.key_info_repetition_risks[:4],
            "next_suggested_focus": memory.next_suggested_focus,
        }

    def select_for_report(self, memory: SessionMemory) -> dict[str, Any]:
        return {
            "important_events": memory.important_events[:8],
            "user_dialogue_patterns": memory.user_strategy_pattern[:6],
            "target_sensitive_points": memory.target_sensitive_points[:6],
            "focus_issues": memory.active_focus_issues[:6],
            "repetition_risks": memory.key_info_repetition_risks[:5],
            "resolved_points": memory.resolved_points[:6],
            "unresolved_points": memory.unresolved_points[:6],
        }


# =========================================================
# 6. MemoryManager
# =========================================================

class MemoryManager:
    """
    Memory 统筹管理器。

    内部机制：
    - add：加入新记忆；
    - search：检索相关记忆；
    - forget：遗忘低价值、过期或已解决记忆；
    - consolidate：把结构化记忆压缩成兼容旧字段的 summary。
    """

    def __init__(self) -> None:
        self.reducer = MemoryReducer()
        self.selector = MemorySelector()

    def update(
        self,
        *,
        request: MemoryUpdateRequest,
        extraction: MemoryExtractionResult,
    ) -> SessionMemory:
        memory = self._ensure_memory(request)
        turn_index = _turn_index(request)

        memory.last_turn_index = turn_index

        memory = self.add(
            memory=memory,
            extraction=extraction,
            turn_index=turn_index,
        )

        # search 机制：找出和本轮最相关的记忆，后续 consolidate 使用。
        related_items = self.search(
            memory=memory,
            query=f"{request.user_message} {request.target_reply}",
            limit=6,
        )

        memory = self.forget(memory=memory, current_turn=turn_index)
        memory = self.consolidate(
            memory=memory,
            request=request,
            extraction=extraction,
            related_items=related_items,
        )
        memory = self.reducer.reduce(memory)

        return memory

    def add(
        self,
        *,
        memory: SessionMemory,
        extraction: MemoryExtractionResult,
        turn_index: int,
    ) -> SessionMemory:
        for candidate in extraction.candidates:
            memory_id = _make_memory_id(candidate.category, candidate.content)

            evidence = MemoryEvidence(
                turn_index=turn_index,
                role=candidate.evidence_role,
                quote=_truncate(candidate.evidence_quote, 180),
            )

            existing = self._find_existing(memory, candidate.category, candidate.content)

            if existing:
                existing.importance = max(existing.importance, candidate.importance)
                existing.last_seen_turn = turn_index
                existing.seen_count += 1
                existing.confidence = self._merge_confidence(
                    existing.confidence,
                    candidate.confidence,
                )
                existing.tags = _dedupe_texts(
                    existing.tags + candidate.tags,
                    limit=8,
                    item_limit=40,
                )
                existing.evidence = (existing.evidence + [evidence])[-4:]
                existing.status = "active"
                continue

            memory.memory_items.append(
                MemoryItem(
                    memory_id=memory_id,
                    category=candidate.category,
                    content=_truncate(candidate.content, 240),
                    importance=candidate.importance,
                    confidence=candidate.confidence,
                    status="active",
                    evidence=[evidence],
                    tags=_dedupe_texts(candidate.tags, limit=8, item_limit=40),
                    first_seen_turn=turn_index,
                    last_seen_turn=turn_index,
                    seen_count=1,
                )
            )

        return memory

    def search(
        self,
        *,
        memory: SessionMemory,
        query: str = "",
        category: str | None = None,
        limit: int = 5,
    ) -> list[MemoryItem]:
        return self.selector.search(
            memory,
            query=query,
            category=category,
            limit=limit,
        )

    def forget(
        self,
        *,
        memory: SessionMemory,
        current_turn: int,
    ) -> SessionMemory:
        """
        Forget 规则：
        1. 低重要度、低置信度、长时间未出现的记忆会被 forgotten；
        2. resolved_point 中太旧的内容会被降权；
        3. 每类记忆超过上限时，由 Reducer 裁剪；
        4. 不保存敏感隐私。
        """

        forgotten_summaries: list[str] = []

        for item in memory.memory_items:
            age = current_turn - item.last_seen_turn

            should_forget = (
                item.importance <= 2
                and item.confidence == "low"
                and age >= 4
            )

            should_forget_resolved = (
                item.category == "resolved_point"
                and age >= 6
                and item.importance <= 3
            )

            if should_forget or should_forget_resolved:
                item.status = "forgotten"
                forgotten_summaries.append(item.content)

        memory.forgotten_items = _dedupe_texts(
            memory.forgotten_items + forgotten_summaries,
            limit=20,
        )

        # 真实删除 forgotten 中低价值内容，避免 memory 无限膨胀。
        memory.memory_items = [
            item
            for item in memory.memory_items
            if not (
                item.status == "forgotten"
                and item.importance <= 2
                and current_turn - item.last_seen_turn >= 5
            )
        ]

        return memory

    def consolidate(
        self,
        *,
        memory: SessionMemory,
        request: MemoryUpdateRequest,
        extraction: MemoryExtractionResult,
        related_items: list[MemoryItem],
    ) -> SessionMemory:
        """
        Consolidate：
        把结构化 memory_items 压缩回兼容旧版的字段，
        方便 SimulationAgent / StrategyAgent / ReportAgent 继续读取。
        """

        active_items = [
            item
            for item in memory.memory_items
            if item.status == "active"
        ]

        memory.user_strategy_pattern = self._contents_by_category(
            active_items,
            "user_dialogue_pattern",
            limit=6,
            fallback=["用户正在尝试通过对话达成沟通目标。"],
        )

        memory.target_sensitive_points = self._contents_by_category(
            active_items,
            "target_sensitive_point",
            limit=6,
            fallback=["对方关注用户表达是否清楚、请求是否合理、是否有具体方案。"],
        )

        focus_items = self._contents_by_category(
            active_items,
            "focus_issue",
            limit=6,
            fallback=extraction.unresolved_focus
            or ["后续仍需根据目标人物反馈继续调整表达。"],
        )

        memory.unresolved_points = _dedupe_texts(
            extraction.unresolved_focus + focus_items,
            limit=6,
        )

        resolved_items = self._contents_by_category(
            active_items,
            "resolved_point",
            limit=6,
            fallback=extraction.resolved_focus,
        )

        memory.resolved_points = _dedupe_texts(
            memory.resolved_points + resolved_items,
            limit=6,
        )

        memory.important_events = self._contents_by_category(
            active_items,
            "important_event",
            limit=8,
            fallback=[extraction.turn_summary],
        )

        repetition_items = self._contents_by_category(
            active_items,
            "key_info_repetition_risk",
            limit=5,
            fallback=extraction.repetition_risks,
        )

        # seen_count >= 2 的 focus/risk 也视为重复风险来源。
        repeated_items = [
            item.content
            for item in active_items
            if item.seen_count >= 2
            and item.category in {"focus_issue", "key_info_repetition_risk"}
        ]

        memory.key_info_repetition_risks = _dedupe_texts(
            extraction.repetition_risks + repetition_items + repeated_items,
            limit=5,
        )

        memory.active_focus_issues = _dedupe_texts(
            memory.unresolved_points + [
                item.content
                for item in related_items
                if item.category == "focus_issue"
            ],
            limit=6,
        )

        memory.conversation_summary = self._build_conversation_summary(
            memory=memory,
            request=request,
            extraction=extraction,
        )

        memory.next_suggested_focus = _truncate(
            extraction.next_focus or self._fallback_next_focus(memory),
            300,
        )

        memory.memory_version = "v2"

        return memory

    def _ensure_memory(self, request: MemoryUpdateRequest) -> SessionMemory:
        if request.current_memory:
            return request.current_memory

        return SessionMemory(
            conversation_summary="当前会话刚开始，尚未形成稳定摘要。",
            user_strategy_pattern=["用户正在尝试通过对话达成沟通目标。"],
            target_sensitive_points=["对方可能关注请求是否清楚、表达是否合适。"],
            resolved_points=[],
            unresolved_points=["仍需根据目标人物反馈继续明确问题。"],
            important_events=[],
            next_suggested_focus="下一轮应先回应对方最关注的问题，再补充具体事实和可执行方案。",
            memory_version="v2",
            memory_items=[],
            active_focus_issues=[],
            key_info_repetition_risks=[],
            forgotten_items=[],
            last_turn_index=0,
        )

    def _find_existing(
        self,
        memory: SessionMemory,
        category: str,
        content: str,
    ) -> MemoryItem | None:
        normalized = content.strip().lower()

        for item in memory.memory_items:
            if item.category != category:
                continue

            if item.content.strip().lower() == normalized:
                return item

            # 简单近似合并：短文本互相包含时认为是同一记忆。
            if normalized in item.content.strip().lower():
                return item

            if item.content.strip().lower() in normalized:
                return item

        return None

    def _merge_confidence(
        self,
        old: Literal["low", "medium", "high"],
        new: Literal["low", "medium", "high"],
    ) -> Literal["low", "medium", "high"]:
        order = {"low": 1, "medium": 2, "high": 3}
        reverse = {1: "low", 2: "medium", 3: "high"}
        return reverse[max(order[old], order[new])]  # type: ignore[return-value]

    def _contents_by_category(
        self,
        items: list[MemoryItem],
        category: str,
        *,
        limit: int,
        fallback: list[str],
    ) -> list[str]:
        values = [
            item.content
            for item in items
            if item.category == category and item.status == "active"
        ]
        return _dedupe_texts(values + fallback, limit=limit)

    def _build_conversation_summary(
        self,
        *,
        memory: SessionMemory,
        request: MemoryUpdateRequest,
        extraction: MemoryExtractionResult,
    ) -> str:
        previous = memory.conversation_summary.strip()

        if previous in {
            "",
            "当前会话刚开始，尚未形成稳定摘要。",
        }:
            base = extraction.turn_summary
        else:
            base = f"{previous}\n本轮更新：{extraction.turn_summary}"

        focus = "；".join(memory.active_focus_issues[:3])
        risks = "；".join(memory.key_info_repetition_risks[:3])

        if focus:
            base += f"\n当前聚焦问题：{focus}"

        if risks:
            base += f"\n重复风险：{risks}"

        return _truncate(base, 900)

    def _fallback_next_focus(self, memory: SessionMemory) -> str:
        if memory.active_focus_issues:
            return f"下一轮优先处理：{memory.active_focus_issues[0]}"
        return "下一轮应围绕对方最关注的问题，补充具体事实、时间安排和可执行方案。"


# =========================================================
# 7. MemorySnapshot
# =========================================================

class MemorySnapshot:
    """
    生成最终 MemoryUpdateResponse。
    """

    def build_response(
        self,
        *,
        memory: SessionMemory,
        extraction: MemoryExtractionResult,
    ) -> MemoryUpdateResponse:
        new_facts = [
            candidate.content
            for candidate in extraction.candidates
            if candidate.category in {
                "important_event",
                "focus_issue",
                "key_info_repetition_risk",
            }
        ]

        if not new_facts:
            new_facts = [extraction.turn_summary]

        return MemoryUpdateResponse(
            memory=memory,
            memory_reason=extraction.memory_reason,
            new_facts=_dedupe_texts(new_facts, limit=6),
            next_focus=memory.next_suggested_focus,
        )


# =========================================================
# 8. MemoryAgent 对外入口
# =========================================================

class MemoryAgent:
    """
    MemoryAgent 负责维护单次模拟会话中的短期记忆。

    外部接口保持不变：
    - 输入：MemoryUpdateRequest
    - 输出：MemoryUpdateResponse

    内部升级为：
    MemoryExtractor → MemoryManager(Add/Search/Forget/Consolidate)
    → MemoryReducer → MemorySelector → MemorySnapshot
    """

    def __init__(self) -> None:
        self.extractor = MemoryExtractor()
        self.manager = MemoryManager()
        self.snapshot = MemorySnapshot()

    async def run(self, request: MemoryUpdateRequest) -> MemoryUpdateResponse:
        extraction = await self.extractor.run(request)

        memory = self.manager.update(
            request=request,
            extraction=extraction,
        )

        return self.snapshot.build_response(
            memory=memory,
            extraction=extraction,
        )