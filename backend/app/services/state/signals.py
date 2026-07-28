from __future__ import annotations

from dataclasses import dataclass

from app.schemas.state import StateEvaluateRequest
from app.services.state.constants import (
    APOLOGY_WORDS,
    CONDITIONAL_ACCEPTANCE_WORDS,
    CONCRETE_WORDS,
    DEFENSIVE_REPLY_WORDS,
    DETAIL_REQUEST_WORDS,
    DYNAMICS_POLITE_WORDS,
    EXPLICIT_ACCEPTANCE_WORDS,
    EXPLICIT_REFUSAL_WORDS,
    GIVES_SPACE_WORDS,
    PRESSURE_WORDS,
    RELATIONSHIP_POLITE_WORDS,
    RESPONSIBILITY_WORDS,
    VAGUE_WORDS,
)
from app.services.state.utils import contains_any


@dataclass(frozen=True, slots=True)
class ConversationSignals:
    user_text: str
    target_text: str
    relationship_polite: bool
    dynamics_polite: bool
    concrete: bool
    pressure: bool
    vague: bool
    responsibility: bool
    apology: bool
    gives_space: bool
    explicit_acceptance: bool
    conditional_acceptance: bool
    explicit_refusal: bool
    defensive_reply: bool
    asks_for_detail: bool


class SignalDetector:
    """把用户消息和目标人物回复转换为可复用的布尔信号。"""

    def detect(self, request: StateEvaluateRequest) -> ConversationSignals:
        user_text = request.user_message.strip()
        target_text = request.target_reply.strip()
        user_lower = user_text.lower()
        target_lower = target_text.lower()

        return ConversationSignals(
            user_text=user_text,
            target_text=target_text,
            relationship_polite=contains_any(
                user_lower,
                RELATIONSHIP_POLITE_WORDS,
            ),
            dynamics_polite=contains_any(
                user_lower,
                DYNAMICS_POLITE_WORDS,
            ),
            concrete=contains_any(user_lower, CONCRETE_WORDS),
            pressure=contains_any(user_lower, PRESSURE_WORDS),
            vague=(
                contains_any(user_lower, VAGUE_WORDS)
                or len(user_text) < 8
            ),
            responsibility=contains_any(
                user_lower,
                RESPONSIBILITY_WORDS,
            ),
            apology=contains_any(user_lower, APOLOGY_WORDS),
            gives_space=contains_any(user_lower, GIVES_SPACE_WORDS),
            explicit_acceptance=contains_any(
                target_lower,
                EXPLICIT_ACCEPTANCE_WORDS,
            ),
            conditional_acceptance=contains_any(
                target_lower,
                CONDITIONAL_ACCEPTANCE_WORDS,
            ),
            explicit_refusal=contains_any(
                target_lower,
                EXPLICIT_REFUSAL_WORDS,
            ),
            defensive_reply=contains_any(
                target_lower,
                DEFENSIVE_REPLY_WORDS,
            ),
            asks_for_detail=(
                "?" in target_text
                or "？" in target_text
                or contains_any(target_lower, DETAIL_REQUEST_WORDS)
            ),
        )
