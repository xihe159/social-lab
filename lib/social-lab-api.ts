import type {
  ChatMessage,
  FormData,
  Persona,
  PredictionFactorDirection,
  PredictionFactorSource,
  ScenarioKey,
  SimulationReport,
} from "@/lib/social-lab-types";

const DEFAULT_API_BASE_URL =
  "https://social-lab-backend.onrender.com";

const API_BASE_URL = (
  (typeof process !== "undefined"
    ? process.env.NEXT_PUBLIC_AGENT_API_BASE_URL
    : undefined) || DEFAULT_API_BASE_URL
).replace(/\/$/, "");

const DEFAULT_REQUEST_TIMEOUT_MS = 90_000;
const REPORT_REQUEST_TIMEOUT_MS = 180_000;

type BackendChatMessage = {
  role: "user" | "target" | "system";
  content: string;
};

export type ResponseAction =
  | "REPLY_NORMAL"
  | "REPLY_BRIEF"
  | "REPLY_COLD"
  | "ASK_CLARIFICATION"
  | "SET_BOUNDARY"
  | "CONFRONT"
  | "DEFER_REPLY"
  | "READ_NO_REPLY"
  | "END_CONVERSATION";

export type SessionActionResponse = {
  action: ResponseAction;
  text: string;
  status_text: string;
  conversation_ended: boolean;
};

export type PersonaEvidence = {
  source:
    | "goal"
    | "outcome"
    | "role"
    | "relation"
    | "habit"
    | "chatLog";
  quote: string;
  inference: string;
};

export type CommunicationStyleV2 = {
  average_reply_length: "short" | "medium" | "long";
  formality: number;
  emoji_frequency: number;
  question_frequency: number;
  uses_periods: boolean;
  uses_multiple_messages: boolean;
  typical_openings: string[];
  typical_closings: string[];
  preferred_sentence_patterns: string[];
};

export type BehaviorPatternV2 = {
  pattern_id: string;
  trigger: {
    user_behavior: string[];
    context: string[];
  };
  observed_response: {
    reply_length_change: string;
    warmth_change: string;
    directness_change: string;
  };
  inferred_tendency: string;
  confidence: number;
  evidence_ids: string[];
  counter_evidence_ids: string[];
};

export type ChatRecordAnalysis = {
  communication_style: CommunicationStyleV2;
  behavior_patterns: BehaviorPatternV2[];
  relationship_characteristics: {
    user_initiative: number;
    target_initiative: number;
    target_decision_power: number;
    communication_distance: number;
    expectation: number;
    trust: number;
    warmth: number;
    summary: string[];
  };
  confidence: number;
  uncertainty_notes: string[];
};

export type PersonaModelV2 = {
  persona_id: string;
  basic_profile: Record<string, string>;
  stable_traits: Record<string, number>;
  communication_style: CommunicationStyleV2;
  dyadic_profile: Record<string, number>;
  behavior_patterns: BehaviorPatternV2[];
  evidence_summary: {
    evidence_count: number;
    chat_record_available: boolean;
    overall_confidence: number;
  };
  version: "2.0";
};

export type PersonaCreateResponse = {
  persona: Persona;
  opening_message: string;
  communication_rules: string[];
  evidence: PersonaEvidence[];
  assumptions: string[];
  confidence: number;
  chat_analysis?: ChatRecordAnalysis | null;
  persona_v2?: PersonaModelV2 | null;
};

export type StateDelta = {
  trust: number;
  respect: number;
  familiarity: number;
  affinity: number;
  authority: number;
  emotional: number;
};

export type SimulationReply = {
  reply: string;
  attitude: string;
  emotion: string;
  perceived_user_tone: string;
  state_delta: StateDelta;
  risk_flags: string[];
};

export type RhythmLabel =
  | "too_fast"
  | "slightly_fast"
  | "balanced"
  | "slightly_slow"
  | "stalled";

export type AtmosphereLabel =
  | "safe"
  | "warm"
  | "neutral"
  | "tense"
  | "defensive"
  | "blocked";

export type RecommendedNextMove =
  | "advance"
  | "clarify"
  | "slow_down"
  | "repair"
  | "set_boundary"
  | "pause";

export type ConversationDynamics = {
  atmosphere_score: number;
  pace_score: number;
  pressure_level: number;
  clarity_score: number;
  responsiveness_score: number;
  progress_score: number;
  repairability_score: number;
  boundary_score: number;

  rhythm_label: RhythmLabel;
  atmosphere_label: AtmosphereLabel;
  recommended_next_move: RecommendedNextMove;
  dynamics_reason: string;
};

export type ConversationDynamicsDelta = {
  atmosphere_score: number;
  pace_score: number;
  pressure_level: number;
  clarity_score: number;
  responsiveness_score: number;
  progress_score: number;
  repairability_score: number;
  boundary_score: number;
};

export type ConversationDynamicsUpdate = {
  dynamics_delta: ConversationDynamicsDelta;
  updated_dynamics: ConversationDynamics;
  control_suggestions: string[];
};

export type ConversationDynamicsSnapshot = {
  turn_index: number;

  atmosphere_score: number;
  pace_score: number;
  pressure_level: number;
  clarity_score: number;
  responsiveness_score: number;
  progress_score: number;
  repairability_score: number;
  boundary_score: number;

  rhythm_label: RhythmLabel;
  atmosphere_label: AtmosphereLabel;
  recommended_next_move: RecommendedNextMove;
  reason: string;
};

export type SessionMemory = Record<string, unknown>;

export type DynamicsContext = {
  currentDynamics?: ConversationDynamics | null;
  history?: ConversationDynamicsSnapshot[];
  memory?: SessionMemory | null;
};

export type SimulationStateV2 = {
  session_id: string;
  persona_id: string;
  relationship_state: {
    trust: number;
    respect: number;
    warmth: number;
    patience: number;
    psychological_safety: number;
    willingness_to_engage: number;
  };
  emotional_state: {
    irritation: number;
    hurt: number;
    anxiety: number;
    defensiveness: number;
    fatigue: number;
  };
  conversation_state: {
    turn_count: number;
    conflict_level: number;
    topic_resolution: number;
    boundary_pressure: number;
  };
  version: "2.0";
};

export type SimulationContextV2 = {
  personaId: string;
  sessionId: string;
  state: SimulationStateV2 | null;
};

export type SessionMessageResponse = {
  target_message: BackendChatMessage;
  simulation: SimulationReply;
  updated_state: Persona["state"];

  dynamics_update?: ConversationDynamicsUpdate | null;
  updated_memory?: SessionMemory | null;

  response?: SessionActionResponse | null;
  strategy_meta?: {
    policy_id: string;
    strategy_action: string;
    simulation_action: ResponseAction;
    confidence: number;
    persona_evidence_refs: string[];
    memory_evidence_refs: string[];
    prompt_version: string;
    fallback_used: boolean;
  } | null;

  simulation_state?: SimulationStateV2 | null;

  evidence_meta?: {
    retrieval_mode: string;
    evidence_ids: string[];
    episode_ids: string[];
    relevance_scores: number[];
  } | null;

  evaluation_meta?: {
    evaluated: boolean;
    execution_mode:
      | "synchronous"
      | "background"
      | "not_run";
    background_scheduled: boolean;
    critical_reasons: string[];
    initial_evaluation_id: string | null;
    final_evaluation_id: string | null;
    initial_score: number | null;
    final_score: number | null;
    score_delta: number | null;
    initial_verdict: string | null;
    final_verdict: string | null;
    initial_failure_attribution: string | null;
    final_failure_attribution: string | null;
    feedback_action:
      | "none"
      | "revise_simulation"
      | "replan_and_regenerate";
    retry_count: number;
    correction_applied: boolean;
    evaluator_failed: boolean;
    final_evaluator_failed: boolean;
  } | null;

  adjustment_meta?: {
    applied: boolean;
    activated_this_turn: boolean;
    style_adjustment_count: number;
    strategy_adjustment_count: number;
    remaining_turns: number;
  } | null;

  runtime_meta?: {
    decision_fallback_used: boolean;
    strategy_fallback_used: boolean;
    generator_retry_count: number;
    generator_fallback_used: boolean;
    evaluation_call_count: number;
    feedback_retry_count: number;
    strategy_replan_count: number;
    simulation_revision_count: number;
    rejected_candidate_discarded: boolean;
  } | null;
};

export type PredictionInfluenceFactorResponse = {
  factor_name: string;
  direction: PredictionFactorDirection;
  importance: number;
  contribution: number;
  source: PredictionFactorSource;

  metric_name?: string | null;
  metric_value?: number | null;

  evidence_turns: number[];
  evidence_quote: string;
  explanation: string;
};

type ReportResponse = {
  success_probability: number;
  probability_low: number;
  probability_high: number;

  confidence_score: number;
  confidence: "low" | "medium" | "high";
  evidence_sufficiency:
    | "insufficient"
    | "partial"
    | "sufficient";

  likely_outcome: string;
  probability_reasoning: string;

  outcome_distribution: {
    accept: number;
    conditional_accept: number;
    hesitate: number;
    refuse: number;
    no_response: number;
  };

  main_influence_factors:
    PredictionInfluenceFactorResponse[];

  prediction_trace: {
    scenario_prior: number;
    dynamics_contribution: number;
    relationship_contribution: number;
    trend_contribution: number;
    semantic_adjustment: number;
    pre_guardrail_score: number;
    guardrail_adjustment: number;
    final_score: number;
    uncertainty_width: number;
    volatility_score: number;
  };

  calibration_version: string;

  strengths: string[];
  problems: string[];
  key_risks: string[];
  suggested_rewrite: string;
  next_step_advice: string;
};

async function requestJson<T>(
  path: string,
  body?: unknown,
  timeoutMs: number = DEFAULT_REQUEST_TIMEOUT_MS,
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = globalThis.setTimeout(
    () => controller.abort(),
    timeoutMs,
  );

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers:
        body === undefined
          ? undefined
          : { "Content-Type": "application/json" },
      body:
        body === undefined
          ? undefined
          : JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (error) {
    if (
      error instanceof DOMException &&
      error.name === "AbortError"
    ) {
      throw new Error(
        "AI 服务响应超时，请稍后再试。",
      );
    }

    throw new Error(
      "无法连接 AI 后端，请确认 Render 服务已启动。",
    );
  } finally {
    globalThis.clearTimeout(timeoutId);
  }

  const contentType =
    response.headers.get("content-type") || "";

  const payload = contentType.includes(
    "application/json",
  )
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload
        ? JSON.stringify(payload.detail, null, 2)
        : typeof payload === "string"
          ? payload
          : JSON.stringify(payload, null, 2);

    throw new Error(
      `API ${path} failed with ${response.status}: ${detail}`,
    );
  }

  return payload as T;
}

function toBackendMessages(
  messages: ChatMessage[],
): BackendChatMessage[] {
  return messages.map((message) => ({
    role: message.role,
    content: message.text,
  }));
}

function toFrontendMessage(
  message: BackendChatMessage,
): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role: message.role,
    text: message.content,
  };
}

export function buildDynamicsSnapshot(
  dynamics: ConversationDynamics,
  turnIndex: number,
): ConversationDynamicsSnapshot {
  return {
    turn_index: Math.max(1, Math.round(turnIndex)),

    atmosphere_score: dynamics.atmosphere_score,
    pace_score: dynamics.pace_score,
    pressure_level: dynamics.pressure_level,
    clarity_score: dynamics.clarity_score,
    responsiveness_score:
      dynamics.responsiveness_score,
    progress_score: dynamics.progress_score,
    repairability_score:
      dynamics.repairability_score,
    boundary_score: dynamics.boundary_score,

    rhythm_label: dynamics.rhythm_label,
    atmosphere_label: dynamics.atmosphere_label,
    recommended_next_move:
      dynamics.recommended_next_move,

    reason: dynamics.dynamics_reason,
  };
}

export async function checkAgentHealth() {
  return requestJson<{
    status: string;
    service?: string;
  }>("/health");
}

export async function createPersona(
  scenario: ScenarioKey,
  form: FormData,
): Promise<PersonaCreateResponse> {
  return requestJson<PersonaCreateResponse>(
    "/api/persona/create",
    {
      scenario,
      goal: form.goal,
      outcome: form.outcome,
      role: form.role,
      relation: form.relation,
      habit: form.habit,
      chatLog: form.chatLog,
    },
  );
}

export async function sendSessionMessage(
  scenario: ScenarioKey,
  form: FormData,
  persona: Persona,
  messages: ChatMessage[],
  userMessage: string,
  simulationContext?: SimulationContextV2 | null,
  personaV2?: PersonaModelV2 | null,
  dynamicsContext: DynamicsContext = {},
): Promise<{
  targetMessage: ChatMessage | null;
  statusMessage: ChatMessage | null;
  action: ResponseAction;
  conversationEnded: boolean;

  simulation: SimulationReply;
  updatedPersona: Persona;
  updatedMemory: SessionMemory | null;

  simulationState: SimulationStateV2 | null;
  dynamicsUpdate: ConversationDynamicsUpdate | null;
  currentDynamics: ConversationDynamics | null;
}> {
  const result =
    await requestJson<SessionMessageResponse>(
      "/api/session/message",
      {
        scenario,
        goal: form.goal,
        outcome: form.outcome,
        role: form.role,
        relation: form.relation,

        persona,
        persona_v2: personaV2,

        messages: toBackendMessages(messages),
        user_message: userMessage,

        memory: dynamicsContext.memory ?? null,
        current_dynamics:
          dynamicsContext.currentDynamics ?? null,

        persona_id: simulationContext?.personaId,
        session_id: simulationContext?.sessionId,
        simulation_state: simulationContext?.state,
      },
    );

  const action =
    result.response?.action ?? "REPLY_NORMAL";

  const responseText =
    result.response?.text ??
    result.target_message.content;

  const statusText =
    result.response?.status_text ??
    (result.target_message.role === "system"
      ? result.target_message.content
      : "");

  const dynamicsUpdate =
    result.dynamics_update ?? null;

  return {
    targetMessage: responseText
      ? toFrontendMessage({
          role: "target",
          content: responseText,
        })
      : null,

    statusMessage: statusText
      ? toFrontendMessage({
          role: "system",
          content: statusText,
        })
      : null,

    action,
    conversationEnded:
      result.response?.conversation_ended ?? false,

    simulation: result.simulation,

    updatedPersona: {
      ...persona,
      state: result.updated_state,
    },

    updatedMemory:
      result.updated_memory ?? null,

    simulationState:
      result.simulation_state ?? null,

    dynamicsUpdate,

    currentDynamics:
      dynamicsUpdate?.updated_dynamics ??
      dynamicsContext.currentDynamics ??
      null,
  };
}

export async function createSimulationReport(
  scenario: ScenarioKey,
  form: FormData,
  persona: Persona,
  messages: ChatMessage[],
  dynamicsContext: DynamicsContext = {},
): Promise<SimulationReport> {
  const result = await requestJson<ReportResponse>(
    "/api/session/report",
    {
      scenario,
      goal: form.goal,
      outcome: form.outcome,
      persona,
      messages: toBackendMessages(messages),

      current_dynamics:
        dynamicsContext.currentDynamics ?? null,

      dynamics_history:
        dynamicsContext.history ?? [],
    },
    REPORT_REQUEST_TIMEOUT_MS,
  );

  return mapReportResponse(result);
}

function mapReportResponse(
  result: ReportResponse,
): SimulationReport {
  const score = Math.max(
    0,
    Math.min(
      100,
      Math.round(result.success_probability),
    ),
  );

  const factorStrings =
    result.main_influence_factors.map((factor) => {
      const contribution =
        factor.contribution >= 0
          ? `+${factor.contribution.toFixed(1)}`
          : factor.contribution.toFixed(1);

      return (
        `${factor.factor_name}（${contribution}）：` +
        factor.explanation
      );
    });

  return {
    score,

    scoreRange: {
      low: result.probability_low,
      high: result.probability_high,
    },

    confidence: result.confidence,
    confidenceScore: result.confidence_score,
    evidenceSufficiency:
      result.evidence_sufficiency,

    reason: result.probability_reasoning,
    likelyOutcome: result.likely_outcome,

    outcomes: [
      {
        label: "接受",
        value:
          result.outcome_distribution.accept,
        color: "#c8f47a",
      },
      {
        label: "条件接受",
        value:
          result.outcome_distribution
            .conditional_accept,
        color: "#d7e9a9",
      },
      {
        label: "犹豫",
        value:
          result.outcome_distribution.hesitate,
        color: "#f2d59b",
      },
      {
        label: "拒绝",
        value:
          result.outcome_distribution.refuse,
        color: "#e8b7b0",
      },
      {
        label: "暂不回应",
        value:
          result.outcome_distribution.no_response,
        color: "#b9c4d3",
      },
    ],

    outcomeDistribution: {
      accept:
        result.outcome_distribution.accept,
      conditionalAccept:
        result.outcome_distribution
          .conditional_accept,
      hesitate:
        result.outcome_distribution.hesitate,
      refuse:
        result.outcome_distribution.refuse,
      noResponse:
        result.outcome_distribution.no_response,
    },

    // 兼容当前页面，不再把“下一步”混入主要影响因素。
    factors: factorStrings,

    influenceFactors:
      result.main_influence_factors.map(
        (factor) => ({
          name: factor.factor_name,
          direction: factor.direction,
          impact: factor.contribution,
          importance: factor.importance,
          source: factor.source,
          metricName: factor.metric_name,
          metricValue: factor.metric_value,
          evidenceTurns: factor.evidence_turns,
          evidence: factor.evidence_quote,
          explanation: factor.explanation,
        }),
      ),

    strengths: result.strengths,
    problems: result.problems,
    risks: result.key_risks,

    rewrite: result.suggested_rewrite,
    nextStep: result.next_step_advice,

    predictionTrace: {
      scenarioPrior:
        result.prediction_trace.scenario_prior,
      dynamicsContribution:
        result.prediction_trace
          .dynamics_contribution,
      relationshipContribution:
        result.prediction_trace
          .relationship_contribution,
      trendContribution:
        result.prediction_trace
          .trend_contribution,
      semanticAdjustment:
        result.prediction_trace
          .semantic_adjustment,
      preGuardrailScore:
        result.prediction_trace
          .pre_guardrail_score,
      guardrailAdjustment:
        result.prediction_trace
          .guardrail_adjustment,
      finalScore:
        result.prediction_trace.final_score,
      uncertaintyWidth:
        result.prediction_trace
          .uncertainty_width,
      volatilityScore:
        result.prediction_trace
          .volatility_score,
    },

    calibrationVersion:
      result.calibration_version,
  };
}
