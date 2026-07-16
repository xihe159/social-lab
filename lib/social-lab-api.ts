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

type BackendChatMessage = {
  role: "user" | "target";
  content: string;
};

export type PersonaEvidence = {
  source: "goal" | "outcome" | "role" | "relation" | "habit" | "chatLog";
  quote: string;
  inference: string;
};

export type PersonaCreateResponse = {
  persona: Persona;
  opening_message: string;
  communication_rules: string[];
  evidence: PersonaEvidence[];
  assumptions: string[];
  confidence: number;
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

/**
 * 第一阶段前端可以先用宽松类型承接 updated_memory。
 * 等 memory schema 稳定后，再把这里改成完整 TS 类型。
 */
export type SessionMemory = Record<string, unknown>;

export type SessionMessageResponse = {
  target_message: BackendChatMessage;
  simulation: SimulationReply;
  updated_state: Persona["state"];

  updated_memory?: SessionMemory | null;

  dynamics_update?: ConversationDynamicsUpdate | null;
  state_metrics?: ConversationDynamics | null;

  rhythm_label?: RhythmLabel | null;

  /**
   * 兼容早期命名。
   * 如果后端曾经返回 pacing_label，这里也可以接住。
   */
  pacing_label?: RhythmLabel | null;

  atmosphere_label?: AtmosphereLabel | null;
  recommended_next_move?: RecommendedNextMove | null;
  control_suggestions?: string[];
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
  memory?: SessionMemory | null;
  currentDynamics?: ConversationDynamics | null;
};

export type SendSessionMessageResult = {
  targetMessage: ChatMessage;
  simulation: SimulationReply;
  updatedPersona: Persona;

  updatedMemory?: SessionMemory | null;

  dynamicsUpdate?: ConversationDynamicsUpdate | null;
  stateMetrics?: ConversationDynamics | null;

  rhythmLabel?: RhythmLabel | null;
  atmosphereLabel?: AtmosphereLabel | null;
  recommendedNextMove?: RecommendedNextMove | null;
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
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers:
        body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("AI 服务响应超时，请稍后再试。");
    }

    throw new Error("无法连接 AI 后端，请确认 Render 服务已启动。");
  } finally {
    clearTimeout(timeoutId);
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? JSON.stringify(payload.detail, null, 2)
        : typeof payload === "string"
          ? payload
          : JSON.stringify(payload, null, 2);

    throw new Error(`API ${path} failed with ${response.status}: ${detail}`);
  }

  return payload as T;
}

function toBackendMessages(messages: ChatMessage[]): BackendChatMessage[] {
  return messages.map((message) => ({
    role: message.role,
    content: message.text,
  }));
}

function toFrontendMessage(message: BackendChatMessage): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role: message.role,
    text: message.content,
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

export async function checkAgentHealth() {
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

export async function sendSessionMessage(
  scenario: ScenarioKey,
  form: FormData,
  persona: Persona,
  messages: ChatMessage[],
  userMessage: string,
  options: SendSessionMessageOptions = {},
): Promise<SendSessionMessageResult> {
  const requestBody: Record<string, unknown> = {
    scenario,
    goal: form.goal,
    outcome: form.outcome,
    persona,
    messages: toBackendMessages(messages),
    user_message: userMessage,
  };

  if (options.memory !== undefined) {
    requestBody.memory = options.memory;
  }

  if (options.currentDynamics !== undefined) {
    requestBody.current_dynamics = options.currentDynamics;
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

  return {
    targetMessage: toFrontendMessage(result.target_message),
    simulation: result.simulation,
    updatedPersona: {
      ...persona,
      state: result.updated_state,
    },

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
  const score = Math.max(
    0,
    Math.min(100, Math.round(result.success_probability)),
  );

  const reject = Math.max(4, Math.round((100 - score) * 0.22));
  const ignore = Math.max(3, 100 - score - Math.max(8, 88 - score) - reject);
  const hesitate = Math.max(0, 100 - score - reject - ignore);

  return {
    score,
    reason: result.likely_outcome,
    outcomes: [
      { label: "接受", value: score, color: "#c8f47a" },
      { label: "犹豫", value: hesitate, color: "#f2d59b" },
      { label: "拒绝", value: reject, color: "#e8b7b0" },
      { label: "冷处理", value: ignore, color: "#b9c4d3" },
    ],
    factors: [
      ...result.strengths.map((item) => `优点：${item}`),
      ...result.problems.map((item) => `问题：${item}`),
      ...result.key_risks.map((item) => `风险：${item}`),
      `下一步：${result.next_step_advice}`,
    ].filter(Boolean),
    rewrite: result.suggested_rewrite,
  };
}
