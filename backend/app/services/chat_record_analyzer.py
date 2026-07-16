from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256

from app.schemas.chat_record import (
    ChatEvidence,
    ChatRecordAnalysis,
    ChatRecordFact,
    ConversationEpisode,
    NormalizedChatMessage,
    RelationshipCharacteristics,
)
from app.schemas.persona_v2 import (
    BehaviorPattern,
    BehaviorTrigger,
    CommunicationStyle,
    ObservedResponse,
    PersonaModelV2,
)


_LINE_PATTERN = re.compile(
    r"^\s*(?:[\[【(（]?\s*(?P<time>\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}(?:日)?(?:\s+[0-2]?\d[:：][0-5]\d(?::[0-5]\d)?)?)\s*[\]】)）]?\s*)?"
    r"(?P<speaker>[^:：]{1,30})\s*[:：]\s*(?P<text>.*)$"
)
_SYSTEM_MARKERS = (
    "以下为新消息",
    "撤回了一条消息",
    "消息已撤回",
    "你们已经是好友",
    "聊天记录",
    "system message",
)
_MISSING_MARKERS = ("[消息缺失]", "[已删除]", "消息已删除", "[missing]")
_EMOJI_PATTERN = re.compile(
    r"[\U0001F300-\U0001FAFF\u2600-\u27BF]|(?:\[[^\]\n]{1,8}\])"
)


@dataclass(frozen=True)
class _ParsedLine:
    speaker: str
    text: str
    original: str
    timestamp: str
    missing_before: bool = False


class ChatRecordAnalyzer:
    """Deterministic, serial Phase 5 pipeline for user-provided chat logs."""

    def analyze(
        self,
        chat_log: str,
        *,
        target_role: str = "",
        relation: str = "",
        persona: PersonaModelV2 | None = None,
    ) -> ChatRecordAnalysis | None:
        messages = self.preprocess(chat_log, target_role=target_role)
        if not messages or not any(item.speaker == "target" for item in messages):
            return None

        episodes = self.build_episodes(messages)
        style = self.analyze_style(messages)
        relationship = self.analyze_relationship(
            messages,
            episodes,
            target_role=target_role,
            relation=relation,
        )
        evidence = self.build_evidence(messages, episodes)
        patterns = self.analyze_trigger_response(episodes, messages)
        facts = self.extract_facts(messages)
        confidence, uncertainty = self.analyze_uncertainty(
            messages,
            episodes,
            patterns,
        )

        return ChatRecordAnalysis(
            messages=messages,
            episodes=episodes,
            communication_style=style,
            behavior_patterns=patterns,
            relationship_characteristics=relationship,
            facts=facts,
            evidence=evidence,
            uncertainty_notes=uncertainty,
            confidence=confidence,
        )

    def preprocess(
        self,
        chat_log: str,
        *,
        target_role: str = "",
    ) -> list[NormalizedChatMessage]:
        parsed: list[_ParsedLine] = []
        missing_before = False
        aliases = self._speaker_aliases(target_role)

        for raw_line in chat_log.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            lowered = line.lower()
            if any(marker.lower() in lowered for marker in _MISSING_MARKERS):
                missing_before = True
                continue
            if any(marker.lower() in lowered for marker in _SYSTEM_MARKERS):
                continue

            match = _LINE_PATTERN.match(line)
            if not match:
                if parsed:
                    previous = parsed[-1]
                    parsed[-1] = _ParsedLine(
                        speaker=previous.speaker,
                        text=f"{previous.text}\n{line}",
                        original=f"{previous.original}\n{raw_line}",
                        timestamp=previous.timestamp,
                        missing_before=previous.missing_before,
                    )
                continue

            speaker = self._normalize_speaker(match.group("speaker"), aliases)
            text = match.group("text").strip()
            if speaker is None or not text:
                continue
            parsed.append(
                _ParsedLine(
                    speaker=speaker,
                    text=text,
                    original=raw_line,
                    timestamp=self._normalize_timestamp(match.group("time") or ""),
                    missing_before=missing_before,
                )
            )
            missing_before = False

        merged: list[_ParsedLine] = []
        merged_counts: list[int] = []
        for item in parsed:
            if merged and merged[-1].speaker == item.speaker and not item.missing_before:
                previous = merged[-1]
                merged[-1] = _ParsedLine(
                    speaker=previous.speaker,
                    text=f"{previous.text}\n{item.text}",
                    original=f"{previous.original}\n{item.original}",
                    timestamp=previous.timestamp or item.timestamp,
                    missing_before=previous.missing_before,
                )
                merged_counts[-1] += 1
            else:
                merged.append(item)
                merged_counts.append(1)

        return [
            NormalizedChatMessage(
                message_id=f"message_{index:04d}",
                speaker=item.speaker,  # type: ignore[arg-type]
                text=item.text,
                original_text=item.original,
                timestamp=item.timestamp,
                merged_count=merged_counts[index - 1],
                missing_message_before=item.missing_before,
            )
            for index, item in enumerate(merged, start=1)
        ]

    def build_episodes(
        self,
        messages: list[NormalizedChatMessage],
    ) -> list[ConversationEpisode]:
        groups: list[list[NormalizedChatMessage]] = []
        current: list[NormalizedChatMessage] = []
        for message in messages:
            should_split = bool(
                current
                and message.speaker == "user"
                and any(item.speaker == "target" for item in current)
            )
            if should_split:
                groups.append(current)
                current = []
            current.append(message)
        if current:
            groups.append(current)

        episodes: list[ConversationEpisode] = []
        for index, group in enumerate(groups, start=1):
            user_text = " ".join(item.text for item in group if item.speaker == "user")
            target_text = " ".join(item.text for item in group if item.speaker == "target")
            episodes.append(
                ConversationEpisode(
                    episode_id=f"episode_{index:04d}",
                    message_ids=[item.message_id for item in group],
                    context=self._infer_context(user_text),
                    user_behavior=self._classify_user_behavior(user_text),
                    target_response=self._classify_target_response(target_text),
                    outcome=self._infer_outcome(target_text),
                )
            )
        return episodes

    def analyze_style(
        self,
        messages: list[NormalizedChatMessage],
    ) -> CommunicationStyle:
        targets = [item for item in messages if item.speaker == "target"]
        texts = [item.text for item in targets]
        lengths = [len(re.sub(r"\s+", "", text)) for text in texts]
        average = sum(lengths) / max(1, len(lengths))
        all_text = "".join(texts)

        openings = [self._first_fragment(text) for text in texts]
        closings = [self._last_fragment(text) for text in texts]
        opening_counts = Counter(item for item in openings if item)
        closing_counts = Counter(item for item in closings if item)

        return CommunicationStyle(
            average_reply_length="short" if average <= 18 else "long" if average >= 60 else "medium",
            formality=self._formality_score(all_text),
            emoji_frequency=self._ratio(sum(len(_EMOJI_PATTERN.findall(text)) for text in texts), len(texts)),
            question_frequency=self._ratio(sum("?" in text or "？" in text for text in texts), len(texts)),
            uses_periods=("。" in all_text or "." in all_text),
            uses_multiple_messages=self._ratio(sum(item.merged_count > 1 for item in targets), len(targets)) >= 0.3,
            typical_openings=[item for item, _ in opening_counts.most_common(3)],
            typical_closings=[item for item, _ in closing_counts.most_common(3)],
            preferred_sentence_patterns=self._sentence_patterns(texts),
        )

    def analyze_relationship(
        self,
        messages: list[NormalizedChatMessage],
        episodes: list[ConversationEpisode],
        *,
        target_role: str,
        relation: str,
    ) -> RelationshipCharacteristics:
        starts = Counter(
            next((message.speaker for message in messages if message.message_id in episode.message_ids), "user")
            for episode in episodes
        )
        total_starts = max(1, sum(starts.values()))
        target_text = " ".join(item.text for item in messages if item.speaker == "target")
        authority_text = f"{target_role} {relation}".lower()
        decision_power = 0.75 if any(word in authority_text for word in ("导师", "老师", "领导", "老板", "主管", "manager")) else 0.5
        formality = self._formality_score(target_text)
        warmth = self._lexical_score(
            target_text,
            positive=("谢谢", "辛苦", "理解", "没关系", "可以", "好呀", "哈哈", "加油"),
            negative=("不行", "别再", "够了", "没必要", "随便", "呵呵"),
        )
        trust = self._lexical_score(
            target_text,
            positive=("相信", "交给你", "没问题", "可以", "同意"),
            negative=("不相信", "再确认", "证明", "不能", "不确定"),
        )
        expectation = self._lexical_score(
            target_text,
            positive=("希望", "需要你", "应该", "请你", "务必"),
            negative=("无所谓", "不用", "算了"),
        )
        summary = [
            "用户更常发起互动" if starts["user"] >= starts["target"] else "目标人物更常发起互动",
            "目标人物在关系中拥有较高决策权" if decision_power >= 0.7 else "双方决策权相对接近",
            "表达较正式、关系距离较明显" if formality >= 0.65 else "表达较自然，关系距离相对较近",
        ]
        return RelationshipCharacteristics(
            user_initiative=round(starts["user"] / total_starts, 3),
            target_initiative=round(starts["target"] / total_starts, 3),
            target_decision_power=decision_power,
            communication_distance=round((formality + decision_power) / 2, 3),
            expectation=expectation,
            trust=trust,
            warmth=warmth,
            summary=summary,
        )

    def analyze_trigger_response(
        self,
        episodes: list[ConversationEpisode],
        messages: list[NormalizedChatMessage],
    ) -> list[BehaviorPattern]:
        grouped: dict[tuple[str, str], list[ConversationEpisode]] = defaultdict(list)
        for episode in episodes:
            triggers = episode.user_behavior or ["general_message"]
            responses = episode.target_response or ["neutral_response"]
            grouped[(triggers[0], responses[0])].append(episode)

        patterns: list[BehaviorPattern] = []
        for (trigger, response), matches in sorted(
            grouped.items(), key=lambda item: (-len(item[1]), item[0])
        ):
            target_messages = [
                message
                for episode in matches
                for message in messages
                if message.message_id in episode.message_ids and message.speaker == "target"
            ]
            average_length = sum(len(item.text) for item in target_messages) / max(1, len(target_messages))
            confidence = min(0.9, 0.45 + len(matches) * 0.12)
            patterns.append(
                BehaviorPattern(
                    pattern_id=f"pattern_{len(patterns) + 1:03d}",
                    trigger=BehaviorTrigger(
                        user_behavior=[trigger],
                        context=sorted({item.context for item in matches}),
                    ),
                    observed_response=ObservedResponse(
                        reply_length_change="shorter" if average_length <= 18 else "longer" if average_length >= 60 else "unchanged",
                        warmth_change="decrease" if response in {"rejects", "sets_boundary"} else "increase" if response in {"accepts", "reassures"} else "unchanged",
                        directness_change="increase" if response in {"rejects", "sets_boundary", "asks_for_details"} else "unchanged",
                    ),
                    inferred_tendency=f"when_{trigger}_tends_to_{response}",
                    confidence=round(confidence, 3),
                    evidence_ids=[f"evidence_{item.episode_id.split('_')[-1]}" for item in matches],
                )
            )

        self._append_style_patterns(patterns, messages)
        return patterns[:8]

    def build_evidence(
        self,
        messages: list[NormalizedChatMessage],
        episodes: list[ConversationEpisode],
    ) -> list[ChatEvidence]:
        by_id = {item.message_id: item for item in messages}
        evidence: list[ChatEvidence] = []
        for episode in episodes:
            content = "\n".join(
                f"{'我' if by_id[mid].speaker == 'user' else '对方'}：{by_id[mid].text}"
                for mid in episode.message_ids
                if mid in by_id
            )
            evidence.append(
                ChatEvidence(
                    evidence_id=f"evidence_{episode.episode_id.split('_')[-1]}",
                    content=content[:800],
                    supports=[*episode.user_behavior, *episode.target_response],
                    confidence=0.8 if len(episode.message_ids) >= 2 else 0.55,
                    scope=[episode.context],
                )
            )
        return evidence

    def extract_facts(
        self,
        messages: list[NormalizedChatMessage],
    ) -> list[ChatRecordFact]:
        facts: list[ChatRecordFact] = []
        patterns = (
            ("commitment", re.compile(r"(?:我会|我可以|我来|答应|约定|保证)[^。！？!?]{1,60}")),
            ("event", re.compile(r"(?:已经|刚才|昨天|今天|上次|之前)[^。！？!?]{1,60}")),
            ("relationship", re.compile(r"(?:我们|同事|同学|导师|老师|朋友)[^。！？!?]{1,60}")),
        )
        for message in messages:
            for category, pattern in patterns:
                for match in pattern.findall(message.text):
                    content = match.strip()
                    if not content or any(item.content == content for item in facts):
                        continue
                    facts.append(
                        ChatRecordFact(
                            fact_id=f"fact_{len(facts) + 1:03d}",
                            category=category,  # type: ignore[arg-type]
                            content=content,
                            evidence_ids=[message.message_id],
                            confidence=0.7,
                        )
                    )
        return facts[:12]

    def analyze_uncertainty(
        self,
        messages: list[NormalizedChatMessage],
        episodes: list[ConversationEpisode],
        patterns: list[BehaviorPattern],
    ) -> tuple[float, list[str]]:
        target_count = sum(item.speaker == "target" for item in messages)
        missing_count = sum(item.missing_message_before for item in messages)
        notes: list[str] = []
        if target_count < 5:
            notes.append("目标人物消息较少，风格和行为结论仅适用于当前样本。")
        if len(episodes) < 3:
            notes.append("可识别的完整互动片段不足 3 个，触发—反应模式置信度较低。")
        if missing_count:
            notes.append("记录中存在缺失消息，部分上下文可能不完整。")
        if len(patterns) < 3:
            notes.append("当前记录不足以支持 3 个彼此独立的高置信行为模式。")
        confidence = 0.35 + min(target_count, 12) * 0.025 + min(len(episodes), 6) * 0.04
        confidence -= min(0.2, missing_count * 0.05)
        return round(max(0.2, min(0.9, confidence)), 3), notes

    def compile_persona(
        self,
        base: PersonaModelV2,
        analysis: ChatRecordAnalysis,
    ) -> PersonaModelV2:
        relationship = analysis.relationship_characteristics
        result = base.model_copy(deep=True)
        result.communication_style = analysis.communication_style
        result.behavior_patterns = analysis.behavior_patterns
        result.dyadic_profile.trust = relationship.trust
        result.dyadic_profile.warmth = relationship.warmth
        result.dyadic_profile.expectation = relationship.expectation
        result.dyadic_profile.communication_distance = relationship.communication_distance
        result.evidence_summary.evidence_count = len(analysis.evidence)
        result.evidence_summary.chat_record_available = True
        result.evidence_summary.overall_confidence = analysis.confidence
        return PersonaModelV2.model_validate(result.model_dump())

    @staticmethod
    def _speaker_aliases(target_role: str) -> dict[str, str]:
        aliases = {
            "我": "user", "本人": "user", "me": "user", "user": "user", "用户": "user", "我方": "user",
            "对方": "target", "target": "target", "ta": "target", "目标人物": "target",
        }
        cleaned_role = target_role.strip().lower()
        if cleaned_role:
            aliases[cleaned_role] = "target"
        return aliases

    @staticmethod
    def _normalize_speaker(speaker: str, aliases: dict[str, str]) -> str | None:
        cleaned = re.sub(r"\s+", "", speaker).strip("[]【】()（）").lower()
        if cleaned in aliases:
            return aliases[cleaned]
        if cleaned.startswith(("我", "user", "me")):
            return "user"
        if cleaned.startswith(("对方", "target")):
            return "target"
        return None

    @staticmethod
    def _normalize_timestamp(value: str) -> str:
        if not value:
            return ""
        cleaned = value.replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-").replace(".", "-").replace("：", ":")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(cleaned.strip(), fmt).isoformat(timespec="seconds")
            except ValueError:
                continue
        return cleaned.strip()

    @staticmethod
    def _infer_context(text: str) -> str:
        lowered = text.lower()
        for context, words in (
            ("request_help", ("帮", "麻烦", "能否", "可以请", "please")),
            ("apology", ("抱歉", "对不起", "不好意思", "sorry")),
            ("work", ("项目", "工作", "截止", "汇报", "会议")),
            ("relationship", ("关系", "在意", "喜欢", "感受")),
        ):
            if any(word in lowered for word in words):
                return context
        return "general_conversation"

    @staticmethod
    def _classify_user_behavior(text: str) -> list[str]:
        rules = (
            ("apologizes", ("抱歉", "对不起", "不好意思", "sorry")),
            ("takes_responsibility", ("是我的问题", "我负责", "我来承担", "我的错")),
            ("explains_reason", ("因为", "原因", "所以", "due to")),
            ("makes_request", ("能不能", "能否", "麻烦", "请你", "希望你", "可以吗")),
            ("expresses_urgency", ("尽快", "马上", "急", "今天必须", "立刻")),
            ("asks_question", ("?", "？", "吗", "么")),
        )
        result = [label for label, words in rules if any(word in text.lower() for word in words)]
        return result or (["general_message"] if text else [])

    @staticmethod
    def _classify_target_response(text: str) -> list[str]:
        rules = (
            ("sets_boundary", ("不要", "不能", "不可以", "到此为止", "别再")),
            ("rejects", ("不行", "拒绝", "没办法", "做不到")),
            ("accepts", ("可以", "好的", "没问题", "行", "同意")),
            ("asks_for_details", ("?", "？", "具体", "什么时候", "为什么", "哪些")),
            ("reassures", ("没关系", "理解", "别担心", "辛苦", "加油")),
        )
        result = [label for label, words in rules if any(word in text.lower() for word in words)]
        if text and len(re.sub(r"\s+", "", text)) <= 18:
            result.append("brief_response")
        return result or (["neutral_response"] if text else [])

    @staticmethod
    def _infer_outcome(text: str) -> str:
        if any(word in text for word in ("可以", "好的", "没问题", "同意")):
            return "accepted"
        if any(word in text for word in ("不行", "拒绝", "没办法", "不能")):
            return "rejected_or_bounded"
        if "?" in text or "？" in text:
            return "needs_clarification"
        return "unresolved"

    @staticmethod
    def _formality_score(text: str) -> float:
        if not text:
            return 0.5
        formal = sum(text.count(word) for word in ("您", "请", "麻烦", "感谢", "您好"))
        casual = sum(text.count(word) for word in ("哈", "呀", "啦", "诶", "哈哈", "～", "~"))
        return round(max(0.0, min(1.0, 0.5 + formal * 0.08 - casual * 0.06)), 3)

    @staticmethod
    def _lexical_score(text: str, *, positive: tuple[str, ...], negative: tuple[str, ...]) -> float:
        score = 0.5 + sum(text.count(word) for word in positive) * 0.06 - sum(text.count(word) for word in negative) * 0.08
        return round(max(0.0, min(1.0, score)), 3)

    @staticmethod
    def _ratio(value: int | float, total: int) -> float:
        return round(max(0.0, min(1.0, value / max(1, total))), 3)

    @staticmethod
    def _first_fragment(text: str) -> str:
        return re.split(r"[，,。.!！?？\n]", text.strip(), maxsplit=1)[0][:12]

    @staticmethod
    def _last_fragment(text: str) -> str:
        parts = [item for item in re.split(r"[，,。.!！?？\n]", text.strip()) if item]
        return parts[-1][-12:] if parts else ""

    @staticmethod
    def _sentence_patterns(texts: list[str]) -> list[str]:
        patterns: list[str] = []
        joined = " ".join(texts)
        if "？" in joined or "?" in joined:
            patterns.append("question_oriented")
        if any(word in joined for word in ("先", "然后", "再", "具体")):
            patterns.append("step_or_detail_oriented")
        if any(word in joined for word in ("但是", "不过", "所以", "因为")):
            patterns.append("reasoning_or_contrast")
        return patterns or ["plain_statement"]

    @staticmethod
    def _append_style_patterns(
        patterns: list[BehaviorPattern],
        messages: list[NormalizedChatMessage],
    ) -> None:
        targets = [item for item in messages if item.speaker == "target"]
        if not targets:
            return
        features = [
            (
                "target_reply_length",
                "responds_briefly" if sum(len(item.text) for item in targets) / len(targets) <= 18 else "responds_with_detail",
                "shorter" if sum(len(item.text) for item in targets) / len(targets) <= 18 else "longer",
            ),
            (
                "target_question_style",
                "uses_questions" if any("?" in item.text or "？" in item.text for item in targets) else "rarely_asks_questions",
                "unchanged",
            ),
            (
                "target_message_cadence",
                "sends_multiple_messages" if any(item.merged_count > 1 for item in targets) else "sends_single_message",
                "unchanged",
            ),
        ]
        existing = {item.inferred_tendency for item in patterns}
        evidence_ids = [item.message_id for item in targets[:5]]
        for trigger, tendency, length_change in features:
            if len(patterns) >= 3 or tendency in existing:
                break
            digest = sha256(tendency.encode("utf-8")).hexdigest()[:6]
            patterns.append(
                BehaviorPattern(
                    pattern_id=f"pattern_style_{digest}",
                    trigger=BehaviorTrigger(user_behavior=[trigger], context=["chat_record"]),
                    observed_response=ObservedResponse(reply_length_change=length_change),
                    inferred_tendency=tendency,
                    confidence=min(0.75, 0.4 + len(targets) * 0.04),
                    evidence_ids=evidence_ids,
                )
            )
