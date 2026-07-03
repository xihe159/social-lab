# social-lab/backend/app/schemas/__init__.py
# 2026/07/01
# 修改内容：新增 StrategyAgent 相关 schema 的统一导出。

from app.schemas.common import ScenarioKey, RelationshipState

from app.schemas.persona import (
    Persona,
    PersonaEvidence,
    PersonaCreateRequest,
    PersonaCreateResponse,
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
    StrategyAdviceRequest,
    StrategyAdviceResponse,
    StrategyCandidateMessage,
    StrategyAlternativeMessage,
)

from app.schemas.evaluation import (
    EvaluationMode,
    EvaluationRequest,
    EvaluationScoreItem,
    EvaluationResponse,
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
    "PersonaCreateResponse",

    "SessionMemory",
    "MemoryUpdateRequest",
    "MemoryUpdateResponse",

    "ChatMessage",
    "StateDelta",
    "SessionMessageRequest",
    "SimulationReply",
    "SessionMessageResponse",

    "StateEvaluateRequest",
    "StateEvaluationResponse",

    "SafetyCheckRequest",
    "SafetyCheckResponse",

    "StrategyAdviceRequest",
    "StrategyAdviceResponse",
    "StrategyCandidateMessage",
    "StrategyAlternativeMessage",

    "EvaluationMode",
    "EvaluationRequest",
    "EvaluationScoreItem",
    "EvaluationResponse",

    "ReportRequest",
    "ReportResponse",
]
