from __future__ import annotations

from app.schemas.dynamics import ConversationDynamics
from app.schemas.state import StateEvaluateRequest, StateEvaluationResponse
from app.services.state.dynamics_calculator import DynamicsCalculator
from app.services.state.dynamics_guardrails import DynamicsGuardrails
from app.services.state.normalizer import StateOutputNormalizer
from app.services.state.relationship_guardrails import RelationshipGuardrails
from app.services.state.signals import SignalDetector


class StateResultProcessor:
    """协调 StateAgent 的确定性后处理，但不调用 LLM。"""

    def __init__(
        self,
        *,
        normalizer: StateOutputNormalizer | None = None,
        signal_detector: SignalDetector | None = None,
        relationship_guardrails: RelationshipGuardrails | None = None,
        dynamics_guardrails: DynamicsGuardrails | None = None,
        dynamics_calculator: DynamicsCalculator | None = None,
    ) -> None:
        self.normalizer = normalizer or StateOutputNormalizer()
        self.signal_detector = signal_detector or SignalDetector()
        self.relationship_guardrails = (
            relationship_guardrails or RelationshipGuardrails()
        )
        self.dynamics_guardrails = (
            dynamics_guardrails or DynamicsGuardrails()
        )
        self.dynamics_calculator = (
            dynamics_calculator or DynamicsCalculator()
        )

    def build_baseline(
        self,
        request: StateEvaluateRequest,
    ) -> ConversationDynamics:
        return (
            request.current_dynamics
            or self.dynamics_calculator.build_initial(request)
        )

    def process(
        self,
        *,
        result: StateEvaluationResponse,
        request: StateEvaluateRequest,
        baseline: ConversationDynamics | None = None,
    ) -> StateEvaluationResponse:
        baseline = baseline or self.build_baseline(request)

        self.normalizer.normalize_before_guardrails(result)
        signals = self.signal_detector.detect(request)

        self.relationship_guardrails.apply(
            result=result,
            request=request,
            signals=signals,
        )
        self.dynamics_guardrails.apply(
            result=result,
            request=request,
            signals=signals,
        )
        self._filter_unconfirmed_risk_flags(result, signals=signals)

        self.normalizer.normalize_after_guardrails(result)

        updated = self.dynamics_calculator.rebuild(
            baseline=baseline,
            delta=result.dynamics_update.dynamics_delta,
            request=request,
            model_reason=(
                result.dynamics_update.updated_dynamics.dynamics_reason
            ),
        )
        result.dynamics_update.updated_dynamics = updated
        result.dynamics_update.control_suggestions = (
            self.dynamics_calculator.build_control_suggestions(updated)
        )

        self.normalizer.normalize_lists(result)
        return result

    @staticmethod
    def _filter_unconfirmed_risk_flags(
        result: StateEvaluationResponse,
        *,
        signals,
    ) -> None:
        """Prevent negated keyword guesses from becoming Session Memory facts."""

        filtered: list[str] = []
        for flag in result.risk_flags:
            normalized = flag.lower()
            pressure_claim = any(
                marker in normalized
                for marker in ("施压", "催促", "命令", "pressure", "threat")
            )
            refusal_claim = any(
                marker in normalized
                for marker in ("明确拒绝", "停止推进", "refusal")
            )
            if pressure_claim and not (
                signals.pressure or signals.defensive_reply
            ):
                continue
            if refusal_claim and not signals.explicit_refusal:
                continue
            filtered.append(flag)
        result.risk_flags = filtered
