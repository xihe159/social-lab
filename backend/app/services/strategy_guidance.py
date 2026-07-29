from __future__ import annotations

from app.schemas.strategy import (
    ResponseAction,
    ResponseMode,
    ResponseModeHypothesis,
    TargetResponseGuidance,
    TargetResponsePolicy,
    ToneRange,
)


LEGACY_ACTION_TO_MODE: dict[ResponseAction, ResponseMode] = {
    ResponseAction.ANSWER: ResponseMode.ENGAGE,
    ResponseAction.ACKNOWLEDGE: ResponseMode.ENGAGE,
    ResponseAction.ASK_CLARIFICATION: ResponseMode.SEEK_INFORMATION,
    ResponseAction.ACCEPT: ResponseMode.CONDITIONAL_SUPPORT,
    ResponseAction.ACCEPT_WITH_CONDITION: ResponseMode.CONDITIONAL_SUPPORT,
    ResponseAction.PARTIAL_ACCEPT: ResponseMode.LIMITED_SUPPORT,
    ResponseAction.REFUSE: ResponseMode.DECLINE,
    ResponseAction.CHALLENGE: ResponseMode.CHALLENGE,
    ResponseAction.SET_BOUNDARY: ResponseMode.SET_BOUNDARY,
    ResponseAction.DEFER: ResponseMode.DEFER,
    ResponseAction.NO_REPLY: ResponseMode.NO_REPLY,
    ResponseAction.END_CONVERSATION: ResponseMode.END_CONVERSATION,
}


def guidance_from_legacy_policy(
    policy: TargetResponsePolicy,
) -> TargetResponseGuidance:
    """Convert a deprecated Policy without preserving its lossy action mapping."""

    mode = LEGACY_ACTION_TO_MODE[policy.action]
    warmth = policy.tone_profile.warmth
    directness = policy.tone_profile.directness
    return TargetResponseGuidance(
        guidance_id=policy.policy_id,
        interpretation=policy.interpretation,
        possible_response_modes=[
            ResponseModeHypothesis(
                mode=mode,
                probability=1.0,
                reason=(
                    "由兼容版 response_policy 转换；Simulation 必须结合人物与"
                    "当前状态重新判断，不能机械执行旧 action。"
                ),
            )
        ],
        recommended_mode=mode,
        communication_goal=policy.response_goal,
        required_content=list(policy.required_content),
        forbidden_content=list(policy.forbidden_content),
        tone_range=ToneRange(
            warmth_min=max(0, warmth - 15),
            warmth_max=min(100, warmth + 15),
            directness_min=max(0, directness - 15),
            directness_max=min(100, directness + 15),
            formality=policy.tone_profile.formality,
            emotional_intensity_max=policy.tone_profile.emotional_intensity,
            preferred_length=policy.tone_profile.length,
        ),
        persona_evidence_refs=list(policy.persona_evidence_refs),
        memory_evidence_refs=list(policy.memory_evidence_refs),
        confidence=min(policy.confidence, 0.75),
        uncertainty_notes=[
            *policy.uncertainty_notes,
            "该 Guidance 来自已弃用的 response_policy 兼容转换。",
        ][:8],
    )
