# social-lab/backend/app/schemas/__init__.py
# 2026/07/01
# 修改内容：新增 StrategyAgent 相关 schema 的统一导出。

from app.schemas.common import ScenarioKey, RelationshipState

from app.schemas.persona import (
    Persona,
    PersonaEvidence,
    PersonaCreateRequest,
    PersonaDraftResponse,
    PersonaCreateResponse,
)

from app.schemas.persona_v2 import (
    BasicProfile,
    StableTraits,
    CommunicationStyle,
    DyadicProfile,
    BehaviorPattern,
    EvidenceSummary,
    PersonaModelV2,
)

from app.schemas.chat_record import (
    NormalizedChatMessage,
    ConversationEpisode,
    ChatRecordFact,
    ChatEvidence,
    RelationshipCharacteristics,
    ChatRecordAnalysis,
)

from app.schemas.evidence_retrieval import (
    RetrievalQuery,
    RetrievedEvidence,
    EvidenceRetrievalResult,
    SessionEvidenceMeta,
)

from app.schemas.consistency_evaluation import (
    ConsistencyScores,
    ConsistencyIssue,
    ConsistencyEvaluationInput,
    ConsistencyEvaluationOutput,
    EvaluatorTriggerResult,
)

from app.schemas.feedback import InternalCorrection

from app.schemas.simulation_adjustment import (
    SimulationAdjustmentProfile,
    SessionAdjustmentMeta,
)

from app.schemas.runtime_metrics import (
    AgentRuntimeMetric,
    AgentMetricSummary,
    RuntimeMetricsSnapshot,
)

from app.schemas.simulation_turn import (
    SessionRuntimeMeta,
    SafeTurnAnalysis,
    SimulationTurnRecord,
)

from app.schemas.simulation_state import (
    RelationshipStateV2,
    EmotionalState,
    ConversationState,
    SimulationState,
)

from app.schemas.simulation_decision import (
    DecisionMessage,
    TurnDecisionInput,
    BehaviorSignals,
    TurnAnalysis,
    SimulationStateDelta,
    ResponsePolicy,
    TurnDecisionOutput,
    TurnDecisionResult,
)

from app.schemas.simulation_generation import (
    ResponseGenerationInput,
    GeneratedResponse,
)

from app.schemas.memory import (
    SessionMemory,
    MemoryUpdateRequest,
    MemoryUpdateResponse,
)

from app.schemas.session import (
    ChatMessage,
    StateDelta,
    SessionMessageRequest,
    SimulationReply,
    SessionActionResponse,
    SessionStrategyMeta,
    SessionMessageResponse,
)

from app.schemas.state import (
    StateEvaluateRequest,
    StateEvaluationResponse,
)

from app.schemas.safety import (
    SafetyCheckRequest,
    SafetyCheckResponse,
)

from app.schemas.strategy import (
    ResponseAction as StrategyResponseAction,
    StrategyMessage,
    TargetInterpretation,
    ToneProfile,
    TargetResponsePolicy,
    TargetResponseStrategyRequest,
)

from app.schemas.evaluation import (
    EvaluationVerdict,
    FailureAttribution,
    FeedbackAction,
    SimulationEvaluationResult,
    SimulationEvaluationRequest,
    EvaluationScoreItem,
    SimulationEvaluationResponse,
    SessionEvaluationMeta,
)

from app.schemas.report import (
    ReportRequest,
    ReportResponse,
)



__all__ = [
    "ScenarioKey",
    "RelationshipState",

    "Persona",
    "PersonaEvidence",
    "PersonaCreateRequest",
    "PersonaDraftResponse",
    "PersonaCreateResponse",

    "BasicProfile",
    "StableTraits",
    "CommunicationStyle",
    "DyadicProfile",
    "BehaviorPattern",
    "EvidenceSummary",
    "PersonaModelV2",

    "NormalizedChatMessage",
    "ConversationEpisode",
    "ChatRecordFact",
    "ChatEvidence",
    "RelationshipCharacteristics",
    "ChatRecordAnalysis",

    "RetrievalQuery",
    "RetrievedEvidence",
    "EvidenceRetrievalResult",
    "SessionEvidenceMeta",

    "ConsistencyScores",
    "ConsistencyIssue",
    "ConsistencyEvaluationInput",
    "ConsistencyEvaluationOutput",
    "EvaluatorTriggerResult",
    "SessionEvaluationMeta",

    "InternalCorrection",

    "SimulationAdjustmentProfile",
    "SessionAdjustmentMeta",

    "AgentRuntimeMetric",
    "AgentMetricSummary",
    "RuntimeMetricsSnapshot",

    "SessionRuntimeMeta",
    "SafeTurnAnalysis",
    "SimulationTurnRecord",

    "RelationshipStateV2",
    "EmotionalState",
    "ConversationState",
    "SimulationState",

    "DecisionMessage",
    "TurnDecisionInput",
    "BehaviorSignals",
    "TurnAnalysis",
    "SimulationStateDelta",
    "ResponsePolicy",
    "TurnDecisionOutput",
    "TurnDecisionResult",

    "ResponseGenerationInput",
    "GeneratedResponse",

    "SessionMemory",
    "MemoryUpdateRequest",
    "MemoryUpdateResponse",

    "ChatMessage",
    "StateDelta",
    "SessionMessageRequest",
    "SimulationReply",
    "SessionActionResponse",
    "SessionStrategyMeta",
    "SessionMessageResponse",

    "StateEvaluateRequest",
    "StateEvaluationResponse",

    "SafetyCheckRequest",
    "SafetyCheckResponse",

    "StrategyResponseAction",
    "StrategyMessage",
    "TargetInterpretation",
    "ToneProfile",
    "TargetResponsePolicy",
    "TargetResponseStrategyRequest",

    "EvaluationVerdict",
    "FailureAttribution",
    "FeedbackAction",
    "SimulationEvaluationResult",
    "SimulationEvaluationRequest",
    "EvaluationScoreItem",
    "SimulationEvaluationResponse",

    "ReportRequest",
    "ReportResponse",
]
