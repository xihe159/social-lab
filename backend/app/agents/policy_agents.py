from __future__ import annotations

from app.agents.analysis_agent import AnalysisAgent
from app.agents.safety_agent import SafetyAgent
from app.llm.client import generate_structured
from app.prompts.report import ANALYSIS_PROMPT, build_analysis_user_prompt
from app.prompts.session import SAFETY_PROMPT, build_safety_user_prompt
from app.schemas.analysis import AnalysisSemanticResult, ConversationProcessAnalysis
from app.schemas.report import ReportRequest
from app.schemas.safety import SafetyCheckRequest, SafetyCheckResponse


class PolicyAnalysisAgent(AnalysisAgent):
    """AnalysisAgent variant whose LLM failure is owned by the shared failure runtime.

    AnalysisAgent normally has its own deterministic fallback. Report orchestration,
    however, needs the raw LLM failure to reach ``run_agent_call`` so the shared
    AgentFailurePolicy can record the failure and apply the configured fallback in
    one place.

    Prompt ownership remains in ``app.prompts``; this adapter must not re-introduce
    Agent-local prompt constants or prompt builders.
    """

    async def run(
        self,
        *,
        request: ReportRequest,
    ) -> ConversationProcessAnalysis:
        manifest, coverage = self.allocator.build_manifest(request.messages)

        if not manifest:
            semantic = self._empty_semantic()
            return self.allocator.build_analysis(
                request=request,
                semantic=semantic,
                manifest=[],
                coverage=coverage,
            )

        semantic = await generate_structured(
            system_prompt=ANALYSIS_PROMPT.system_prompt,
            user_prompt=build_analysis_user_prompt(
                request=request,
                manifest=manifest,
            ),
            output_model=AnalysisSemanticResult,
            temperature=ANALYSIS_PROMPT.temperature,
        )

        return self.allocator.build_analysis(
            request=request,
            semantic=semantic,
            manifest=manifest,
            coverage=coverage,
        )


class PolicySafetyAgent(SafetyAgent):
    """SafetyAgent adapter with deterministic rule checking separated from LLM enrichment.

    The rule result is always available as a safe deterministic fallback. LLM
    enrichment errors are intentionally *not* caught here: the caller's shared
    failure runtime decides how the failure is recorded and degraded.
    """

    def rule_check(self, request: SafetyCheckRequest) -> SafetyCheckResponse:
        return self._rule_check(request)

    async def enrich(
        self,
        request: SafetyCheckRequest,
        *,
        rule_result: SafetyCheckResponse,
    ) -> SafetyCheckResponse:
        result = await generate_structured(
            system_prompt=SAFETY_PROMPT.system_prompt,
            user_prompt=build_safety_user_prompt(request.model_dump()),
            output_model=SafetyCheckResponse,
            temperature=SAFETY_PROMPT.temperature,
        )
        return self.post_process(
            result=result,
            rule_result=rule_result,
        )
