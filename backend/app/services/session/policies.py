# social-lab/backend/app/services/session/policies.py
# 保存纯规则逻辑
# 2026/07/28

from __future__ import annotations

from app.schemas.safety import SafetyCheckResponse
from app.schemas.session import (
    ChatMessage,
    SessionMessageRequest,
    SessionMessageResponse,
    SimulationReply,
    StateDelta,
)


def should_block(safety_result: SafetyCheckResponse) -> bool:
    return (
        not safety_result.allowed
        or safety_result.action == "block"
        or safety_result.risk_level == "high"
    )


def append_safety_warning_if_needed(
    *,
    risk_flags: list[str],
    safety_result: SafetyCheckResponse,
) -> None:
    """将 SafetyAgent 的 warn/rewrite 提醒并入风险列表。"""

    if safety_result.action not in ("warn", "rewrite"):
        return

    warning = safety_result.user_notice.strip()
    if warning and warning not in risk_flags:
        risk_flags.append(warning)


def merge_risk_flags(*groups: list[str]) -> list[str]:
    """保持原顺序去重，避免同一风险被多个 Agent 重复写入。"""

    merged: list[str] = []
    seen: set[str] = set()

    for group in groups:
        for item in group:
            normalized = item.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            merged.append(normalized)

    return merged


def build_blocked_response(
    *,
    request: SessionMessageRequest,
    safety_result: SafetyCheckResponse,
) -> SessionMessageResponse:
    zero_delta = StateDelta(
        trust=0,
        respect=0,
        familiarity=0,
        affinity=0,
        authority=0,
        emotional=0,
    )

    notice = (
        safety_result.user_notice.strip()
        or "当前输入包含安全风险，已停止继续模拟。"
    )
    safe_rewrite_hint = safety_result.safe_rewrite_hint.strip()

    if safe_rewrite_hint:
        notice = f"{notice}\n\n安全改写建议：{safe_rewrite_hint}"

    return SessionMessageResponse(
        target_message=ChatMessage(role="target", content=notice),
        simulation=SimulationReply(
            reply=notice,
            attitude="安全拦截",
            emotion="中立",
            perceived_user_tone="存在安全风险",
            state_delta=zero_delta,
            risk_flags=list(safety_result.risk_types),
        ),
        updated_state=request.persona.state,
        dynamics_update=None,
        updated_memory=request.memory,
        safety=safety_result,
    )
