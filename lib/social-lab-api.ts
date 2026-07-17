import type {
  ChatMessage,
  FormData,
  Persona,
  ScenarioKey,
  SimulationReport,
} from "@/lib/social-lab-types";

const DEFAULT_API_BASE_URL = "https://social-lab-backend.onrender.com";

const API_BASE_URL = (
  (typeof process !== "undefined"
    ? process.env.NEXT_PUBLIC_AGENT_API_BASE_URL
    : undefined) || DEFAULT_API_BASE_URL
).replace(/\/$/, "");

const DEFAULT_REQUEST_TIMEOUT_MS = 90_000;
const REPORT_REQUEST_TIMEOUT_MS = 180_000;

type JsonObject = Record<string, unknown>;

type BackendChatMessage = {
  role: "user" | "target" | "system";
  content: string;
};

export type PersonaEvidence = {
  source: "goal" | "outcome" | "role" | "relation" | "habit" | "chatLog";
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

export type PersonaModelV2 = {
  persona_id: string;
  basic_profile: {
    name: string;
    role: string;
    age_range: string;
    relationship_type: string;
    relationship_duration: string;
    power_dynamic: string;
  };
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

export type ChatRecordAnalysis = {
  messages: Array<{
    message_id: string;
    speaker: "user" | "target";
    text: string;
    original_text: string;
    timestamp: string;
    merged_count: number;
    missing_message_before: boolean;
  }>;
  episodes: Array<{
    episode_id: string;
    message_ids: string[];
    context: string;
    user_behavior: string[];
    target_response: string[];
    outcome: string;
  }>;
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
  facts: Array<{
    fact_id: string;
    category: "identity" | "relationship" | "event" | "commitment" | "background";
    content: string;
    evidence_ids: string[];
    confidence: number;
  }>;
  evidence: Array<{
    evidence_id: string;
    source_type: "REAL_CHAT";
    content: string;
    supports: string[];
    confidence: number;
    scope: string[];
  }>;
  uncertainty_notes: string[];
  confidence: number;
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

export type SessionMemory = JsonObject;

export type RelationshipStateV2 = {
  trust: number;
  respect: number;
  warmth: number;
  patience: number;
  psychological_safety: number;
  willingness_to_engage: number;
};

export type EmotionalStateV2 = {
  irritation: number;
  hurt: number;
  anxiety: number;
  defensiveness: number;
  fatigue: number;
};

export type ConversationStateV2 = {
  turn_count: number;
  conflict_level: number;
  topic_resolution: number;
  boundary_pressure: number;
};

export type SimulationStateV2 = {
  session_id: string;
  persona_id: string;
  relationship_state: RelationshipStateV2;
  emotional_state: EmotionalStateV2;
  conversation_state: ConversationStateV2;
  version: "2.0";
};

export type SimulationContextV2 = {
  personaId: string;
  sessionId: string;
  state: SimulationStateV2 | null;
  memory?: SessionMemory | null;
  currentDynamics?: ConversationDynamics | null;
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

export type SessionMessageResponse = {
  target_message: BackendChatMessage;
  simulation: SimulationReply;
  updated_state: Persona["state"];

  response?: SessionActionResponse | null;
  updated_memory?: SessionMemory | null;
  simulation_state?: SimulationStateV2 | null;
  safety?: JsonObject | null;
  evidence_meta?: JsonObject | null;
  evaluation_meta?: JsonObject | null;
  runtime_meta?: JsonObject | null;

  dynamics_update?: ConversationDynamicsUpdate | null;
  state_metrics?: ConversationDynamics | null;
  rhythm_label?: RhythmLabel | null;
  pacing_label?: RhythmLabel | null;
  atmosphere_label?: AtmosphereLabel | null;
  recommended_next_move?: RecommendedNextMove | null;
  control_suggestions?: string[] | null;
};

type ReportResponse = {
  success_probability: number;
  likely_outcome: string;
  strengths: string[];
  problems: string[];
  key_risks: string[];
  suggested_rewrite: string;
  next_step_advice: string;
};

export type SendSessionMessageOptions = {
  simulationContext?: SimulationContextV2 | null;
  personaV2?: PersonaModelV2 | null;
  memory?: SessionMemory | null;
  currentDynamics?: ConversationDynamics | null;
};

export type SendSessionMessageResult = {
  targetMessage: ChatMessage | null;
  statusMessage: ChatMessage | null;
  simulation: SimulationReply;
  updatedPersona: Persona;

  response: SessionActionResponse | null;
  conversationEnded: boolean;
  simulationState: SimulationStateV2 | null;

  updatedMemory: SessionMemory | null;
  dynamicsUpdate: ConversationDynamicsUpdate | null;
  stateMetrics: ConversationDynamics | null;
  rhythmLabel: RhythmLabel | null;
  atmosphereLabel: AtmosphereLabel | null;
  recommendedNextMove: RecommendedNextMove | null;
  controlSuggestions: string[];
};

export type StateTimelineItem = {
  turnIndex: number;
  metrics: ConversationDynamics;
  rhythmLabel?: RhythmLabel | null;
  atmosphereLabel?: AtmosphereLabel | null;
  recommendedNextMove?: RecommendedNextMove | null;
  controlSuggestions?: string[];
  userMessage: string;
  targetReply: string;
};

type BackendStateTimelineItem = {
  turn_index: number;
  metrics: ConversationDynamics;
  rhythm_label?: RhythmLabel | null;
  atmosphere_label?: AtmosphereLabel | null;
  recommended_next_move?: RecommendedNextMove | null;
  control_suggestions?: string[];
  user_message: string;
  target_reply: string;
};

async function requestJson<T>(
  path: string,
  body?: unknown,
  timeoutMs: number = DEFAULT_REQUEST_TIMEOUT_MS,
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = globalThis.setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers:
        body === undefined
          ? undefined
          : {
              "Content-Type": "application/json",
            },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("AI 服务响应超时，请稍后再试。");
    }

    throw new Error("无法连接 AI 后端，请确认后端服务已启动。");
  } finally {
    globalThis.clearTimeout(timeoutId);
  }

  const contentType = response.headers.get("content-type") ?? "";
  const payload: unknown = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = extractErrorDetail(payload);
    throw new Error(`API ${path} failed with ${response.status}: ${detail}`);
  }

  return payload as T;
}

function extractErrorDetail(payload: unknown): string {
  if (typeof payload === "string") {
    return payload;
  }

  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    return typeof detail === "string" ? detail : JSON.stringify(detail, null, 2);
  }

  return JSON.stringify(payload, null, 2);
}

function createMessageId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `message_${Date.now()}_${Math.random().toString(36).slice(2)}`;
}

function toBackendMessages(messages: ChatMessage[]): BackendChatMessage[] {
  return messages.map((message) => ({
    role: message.role,
    content: message.text,
  }));
}

function toFrontendMessage(
  message: BackendChatMessage,
  fallbackRole: ChatMessage["role"] = "target",
): ChatMessage {
  return {
    id: createMessageId(),
    role: message.role ?? fallbackRole,
    text: message.content,
  };
}

function createTextMessage(
  role: ChatMessage["role"],
  text: string,
): ChatMessage | null {
  const cleaned = text.trim();

  if (!cleaned) {
    return null;
  }

  return {
    id: createMessageId(),
    role,
    text: cleaned,
  };
}

function toBackendStateTimeline(
  timeline: StateTimelineItem[],
): BackendStateTimelineItem[] {
  return timeline.map((item) => ({
    turn_index: item.turnIndex,
    metrics: item.metrics,
    rhythm_label: item.rhythmLabel ?? item.metrics.rhythm_label ?? null,
    atmosphere_label:
      item.atmosphereLabel ?? item.metrics.atmosphere_label ?? null,
    recommended_next_move:
      item.recommendedNextMove ?? item.metrics.recommended_next_move ?? null,
    control_suggestions: item.controlSuggestions ?? [],
    user_message: item.userMessage,
    target_reply: item.targetReply,
  }));
}

function isSimulationContextV2(
  value: SimulationContextV2 | SendSessionMessageOptions | null | undefined,
): value is SimulationContextV2 {
  return Boolean(
    value &&
      typeof value === "object" &&
      "personaId" in value &&
      "sessionId" in value &&
      "state" in value,
  );
}

function normalizeSendOptions(
  contextOrOptions:
    | SimulationContextV2
    | SendSessionMessageOptions
    | null
    | undefined,
  legacyPersonaV2: PersonaModelV2 | null | undefined,
): SendSessionMessageOptions {
  if (isSimulationContextV2(contextOrOptions)) {
    return {
      simulationContext: contextOrOptions,
      personaV2: legacyPersonaV2 ?? null,
      memory: contextOrOptions.memory,
      currentDynamics: contextOrOptions.currentDynamics,
    };
  }

  return {
    ...(contextOrOptions ?? {}),
    personaV2:
      legacyPersonaV2 !== undefined
        ? legacyPersonaV2
        : contextOrOptions?.personaV2,
  };
}

export async function checkAgentHealth(): Promise<{
  status: string;
  service?: string;
}> {
  return requestJson<{ status: string; service?: string }>("/health");
}

export async function createPersona(
  scenario: ScenarioKey,
  form: FormData,
): Promise<PersonaCreateResponse> {
  return requestJson<PersonaCreateResponse>("/api/persona/create", {
    scenario,
    goal: form.goal,
    outcome: form.outcome,
    role: form.role,
    relation: form.relation,
    habit: form.habit,
    chatLog: form.chatLog,
  });
}

/**
 * 同时兼容两种调用方式：
 *
 * 1. 当前 SocialLabApp 的 V2 位置参数：
 *    sendSessionMessage(..., simulationContext, personaV2)
 *
 * 2. 推荐的新 options 参数：
 *    sendSessionMessage(..., { simulationContext, personaV2, memory, currentDynamics })
 */
export async function sendSessionMessage(
  scenario: ScenarioKey,
  form: FormData,
  persona: Persona,
  messages: ChatMessage[],
  userMessage: string,
  contextOrOptions:
    | SimulationContextV2
    | SendSessionMessageOptions
    | null = null,
  legacyPersonaV2: PersonaModelV2 | null = null,
): Promise<SendSessionMessageResult> {
  const options = normalizeSendOptions(contextOrOptions, legacyPersonaV2);
  const context = options.simulationContext ?? null;

  const requestBody: Record<string, unknown> = {
    scenario,
    goal: form.goal,
    outcome: form.outcome,
    role: form.role,
    relation: form.relation,
    persona,
    messages: toBackendMessages(messages),
    user_message: userMessage,
  };

  if (options.personaV2) {
    requestBody.persona_v2 = options.personaV2;
  }

  const memory = options.memory ?? context?.memory;
  if (memory !== undefined && memory !== null) {
    requestBody.memory = memory;
  }

  const currentDynamics =
    options.currentDynamics ?? context?.currentDynamics;
  if (currentDynamics !== undefined && currentDynamics !== null) {
    requestBody.current_dynamics = currentDynamics;
  }

  if (context) {
    requestBody.persona_id = context.personaId;
    requestBody.session_id = context.sessionId;

    if (context.state) {
      requestBody.simulation_state = context.state;
    }
  }

  const result = await requestJson<SessionMessageResponse>(
    "/api/session/message",
    requestBody,
  );

  const stateMetrics =
    result.state_metrics ?? result.dynamics_update?.updated_dynamics ?? null;

  const rhythmLabel =
    result.rhythm_label ??
    result.pacing_label ??
    stateMetrics?.rhythm_label ??
    null;

  const atmosphereLabel =
    result.atmosphere_label ?? stateMetrics?.atmosphere_label ?? null;

  const recommendedNextMove =
    result.recommended_next_move ??
    stateMetrics?.recommended_next_move ??
    null;

  const controlSuggestions =
    result.control_suggestions ??
    result.dynamics_update?.control_suggestions ??
    [];

  const visibleReply =
    result.response?.text?.trim() ||
    result.target_message?.content?.trim() ||
    result.simulation?.reply?.trim() ||
    "";

  const targetMessage = visibleReply
    ? createTextMessage("target", visibleReply)
    : null;

  const statusText = result.response?.status_text?.trim() ?? "";
  const statusMessage =
    statusText && statusText !== visibleReply
      ? createTextMessage("system", statusText)
      : null;

  return {
    targetMessage,
    statusMessage,
    simulation: result.simulation,
    updatedPersona: {
      ...persona,
      state: result.updated_state,
    },
    response: result.response ?? null,
    conversationEnded: result.response?.conversation_ended ?? false,
    simulationState: result.simulation_state ?? null,
    updatedMemory: result.updated_memory ?? null,
    dynamicsUpdate: result.dynamics_update ?? null,
    stateMetrics,
    rhythmLabel,
    atmosphereLabel,
    recommendedNextMove,
    controlSuggestions,
  };
}

export async function createSimulationReport(
  scenario: ScenarioKey,
  form: FormData,
  persona: Persona,
  messages: ChatMessage[],
  stateTimeline: StateTimelineItem[] = [],
): Promise<SimulationReport> {
  const requestBody: Record<string, unknown> = {
    scenario,
    goal: form.goal,
    outcome: form.outcome,
    persona,
    messages: toBackendMessages(messages),
  };

  if (stateTimeline.length > 0) {
    requestBody.state_timeline = toBackendStateTimeline(stateTimeline);
  }

  const result = await requestJson<ReportResponse>(
    "/api/session/report",
    requestBody,
    REPORT_REQUEST_TIMEOUT_MS,
  );

  return mapReportResponse(result);
}

function mapReportResponse(result: ReportResponse): SimulationReport {
  const score = clampPercentage(result.success_probability);
  const remaining = 100 - score;
  const hesitate = Math.round(remaining * 0.55);
  const reject = Math.round(remaining * 0.3);
  const ignore = Math.max(0, remaining - hesitate - reject);

  return {
      score,
      reason: result.likely_outcome,

      outcomes: [
        {
          label: "接受",
          value: score,
          color: "#c8f47a",
        },
        {
          label: "犹豫",
          value: hesitate,
          color: "#f2d59b",
        },
        {
          label: "拒绝",
          value: reject,
          color: "#e8b7b0",
        },
        {
          label: "冷处理",
          value: ignore,
          color: "#b9c4d3",
        },
      ],

      /*
       * 主要影响因素只保留 AnalysisAgent 的诊断信息。
       * 不再把 next_step_advice 塞进 factors。
       */
      factors: [
        ...result.strengths.map(
          (item) => `优点：${item}`,
        ),
        ...result.problems.map(
          (item) => `问题：${item}`,
        ),
        ...result.key_risks.map(
          (item) => `风险：${item}`,
        ),
      ].filter(Boolean),

      /*
       * 下一步行动单独保存。
       */
      nextStepAdvice:
        result.next_step_advice?.trim() ||
        "根据对方最新回应，选择一个低压力、可执行的推进动作。",

      /*
       * 推荐改写由 RewriteAgent 提供。
       */
          rewrite: result.suggested_rewrite,
        };
}

function clampPercentage(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }

  return Math.max(0, Math.min(100, Math.round(value)));
}
