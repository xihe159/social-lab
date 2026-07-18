from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from threading import RLock

from app.schemas.evaluation import FailureAttribution
from app.schemas.simulation_adjustment import SimulationAdjustmentProfile


_REQUIRED_CONSECUTIVE_TURNS = 3
_PROFILE_LIFETIME_TURNS = 3

_ADJUSTMENTS: dict[str, tuple[str, str]] = {
    "reply_too_long": ("style", "下一轮回复长度控制在两句以内。"),
    "over_comforting": ("style", "减少解释和主动安慰。"),
    "punctuation_mismatch": ("style", "遵循 Persona 证据中的标点习惯。"),
    "over_cooperative": ("strategy", "不要默认帮助用户推进目标或扩大承诺。"),
}


@dataclass(frozen=True)
class AdjustmentTurnContext:
    turn_number: int
    profile: SimulationAdjustmentProfile | None
    remaining_turns: int


@dataclass(frozen=True)
class AdjustmentObservationResult:
    activated_this_turn: bool
    profile: SimulationAdjustmentProfile | None


@dataclass
class _SignalStreak:
    count: int = 0
    last_turn: int = 0
    evaluation_ids: list[str] = field(default_factory=list)


@dataclass
class _SessionAdjustmentState:
    turn_counter: int = 0
    last_processed_turn: int = 0
    pending_observations: dict[int, "_PendingObservation"] = field(
        default_factory=dict
    )
    streaks: dict[str, _SignalStreak] = field(default_factory=dict)
    active_profile: SimulationAdjustmentProfile | None = None
    profile_expires_at_turn: int = 0


@dataclass(frozen=True)
class _PendingObservation:
    turn_number: int
    evaluation_id: str
    signals: list[str]
    confidence: float
    failure_attribution: FailureAttribution


class SimulationAdjustmentManager:
    """Compress repeated Evaluation signals into bounded, expiring controls.

    The manager deliberately stores no Persona fields, chat content, memory facts, or
    evaluator free-form advice. Only four allow-listed issue categories can activate
    a profile after three reliable consecutive observations.
    """

    def __init__(self, *, max_sessions: int = 500) -> None:
        self.max_sessions = max(1, max_sessions)
        self._states: OrderedDict[str, _SessionAdjustmentState] = OrderedDict()
        self._lock = RLock()

    def begin_turn(self, session_id: str) -> AdjustmentTurnContext:
        with self._lock:
            state = self._get_or_create(session_id)
            state.turn_counter += 1
            self._expire_if_needed(state)
            profile = self._copy_profile(state.active_profile)
            remaining = (
                max(0, state.profile_expires_at_turn - state.turn_counter + 1)
                if profile is not None
                else 0
            )
            return AdjustmentTurnContext(
                turn_number=state.turn_counter,
                profile=profile,
                remaining_turns=remaining,
            )

    def observe(
        self,
        *,
        session_id: str,
        turn_number: int,
        evaluation_id: str,
        signals: list[str],
        confidence: float,
        failure_attribution: FailureAttribution,
    ) -> AdjustmentObservationResult:
        with self._lock:
            state = self._get_or_create(session_id)
            if turn_number > state.turn_counter or turn_number <= state.last_processed_turn:
                return AdjustmentObservationResult(
                    activated_this_turn=False,
                    profile=self._copy_profile(state.active_profile),
                )

            self._expire_if_needed(state)
            state.pending_observations[turn_number] = _PendingObservation(
                turn_number=turn_number,
                evaluation_id=evaluation_id,
                signals=list(signals),
                confidence=confidence,
                failure_attribution=failure_attribution,
            )
            activated = False
            next_turn = state.last_processed_turn + 1
            while next_turn in state.pending_observations:
                observation = state.pending_observations.pop(next_turn)
                activated = self._apply_observation(
                    session_id=session_id,
                    state=state,
                    observation=observation,
                ) or activated
                state.last_processed_turn = next_turn
                next_turn += 1
            return AdjustmentObservationResult(
                activated_this_turn=activated,
                profile=self._copy_profile(state.active_profile),
            )

    def has_repeated_issue(
        self,
        session_id: str,
        *,
        minimum_count: int = 2,
    ) -> bool:
        with self._lock:
            state = self._states.get(session_id.strip())
            if state is None:
                return False
            return any(
                streak.count >= max(1, minimum_count)
                for streak in state.streaks.values()
            )

    def clear(self) -> None:
        with self._lock:
            self._states.clear()

    def _get_or_create(self, session_id: str) -> _SessionAdjustmentState:
        key = session_id.strip()
        if not key:
            raise ValueError("session_id must not be blank")
        state = self._states.get(key)
        if state is None:
            state = _SessionAdjustmentState()
            self._states[key] = state
            while len(self._states) > self.max_sessions:
                self._states.popitem(last=False)
        else:
            self._states.move_to_end(key)
        return state

    def _apply_observation(
        self,
        *,
        session_id: str,
        state: _SessionAdjustmentState,
        observation: _PendingObservation,
    ) -> bool:
        if state.active_profile is not None:
            return False

        categories = {
            category
            for signal in observation.signals
            if (category := _normalize_signal(signal)) is not None
        }
        reliable = (
            observation.confidence >= 0.6
            and observation.failure_attribution != FailureAttribution.CONTEXT_GAP
            and bool(categories)
        )
        if not reliable:
            state.streaks.clear()
            return False

        for category in tuple(state.streaks):
            if category not in categories:
                state.streaks.pop(category, None)

        activated_categories: list[str] = []
        for category in sorted(categories):
            streak = state.streaks.setdefault(category, _SignalStreak())
            if streak.last_turn == observation.turn_number - 1:
                streak.count += 1
            else:
                streak.count = 1
                streak.evaluation_ids.clear()
            streak.last_turn = observation.turn_number
            if (
                observation.evaluation_id
                and observation.evaluation_id not in streak.evaluation_ids
            ):
                streak.evaluation_ids.append(observation.evaluation_id[:200])
                streak.evaluation_ids = streak.evaluation_ids[-3:]
            if streak.count >= _REQUIRED_CONSECUTIVE_TURNS:
                activated_categories.append(category)

        if not activated_categories:
            return False

        style_adjustments: list[str] = []
        strategy_adjustments: list[str] = []
        source_ids: list[str] = []
        for category in activated_categories:
            owner, adjustment = _ADJUSTMENTS[category]
            if owner == "style":
                style_adjustments.append(adjustment)
            else:
                strategy_adjustments.append(adjustment)
            for source_id in state.streaks[category].evaluation_ids:
                if source_id not in source_ids:
                    source_ids.append(source_id)

        state.active_profile = SimulationAdjustmentProfile(
            session_id=session_id,
            style_adjustments=style_adjustments,
            strategy_adjustments=strategy_adjustments,
            source_evaluation_ids=source_ids,
            expires_after_turns=_PROFILE_LIFETIME_TURNS,
        )
        state.profile_expires_at_turn = (
            max(state.turn_counter, observation.turn_number)
            + _PROFILE_LIFETIME_TURNS
        )
        state.streaks.clear()
        return True

    @staticmethod
    def _copy_profile(
        profile: SimulationAdjustmentProfile | None,
    ) -> SimulationAdjustmentProfile | None:
        return profile.model_copy(deep=True) if profile is not None else None

    @staticmethod
    def _expire_if_needed(state: _SessionAdjustmentState) -> None:
        if (
            state.active_profile is not None
            and state.turn_counter > state.profile_expires_at_turn
        ):
            state.active_profile = None
            state.profile_expires_at_turn = 0
            state.streaks.clear()


def _normalize_signal(value: str) -> str | None:
    signal = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if signal in _ADJUSTMENTS:
        return signal

    compact = signal.replace("_", "")
    if any(marker in compact for marker in ("回复过长", "回复太长", "总是过长", "长度过长")):
        return "reply_too_long"
    if any(
        marker in compact
        for marker in ("过度安慰", "主动安慰", "过度温和", "解释过多", "过多解释")
    ):
        return "over_comforting"
    if any(
        marker in compact
        for marker in ("标点不匹配", "标点风格", "标点习惯", "punctuationmismatch")
    ):
        return "punctuation_mismatch"
    if any(
        marker in compact
        for marker in (
            "过度配合",
            "过度合作",
            "默认帮助",
            "推进用户目标",
            "扩大承诺",
            "无条件承诺",
        )
    ):
        return "over_cooperative"
    return None


simulation_adjustment_manager = SimulationAdjustmentManager()
