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
  trigger: { user_behavior: string[]; context: string[] };
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

export type SessionMessageResponse = {
  target_message: BackendChatMessage;
  simulation: SimulationReply;
  updated_state: Persona["state"];
  response?: SessionActionResponse | null;
  simulation_state?: SimulationStateV2 | null;
  evidence_meta?: {
    retrieval_mode: string;
    evidence_ids: string[];
    episode_ids: string[];
    relevance_scores: number[];
  } | null;
  evaluation_meta?: {
    evaluated: boolean;
    trigger_reasons: string[];
    result: {
      pass: boolean;
      scores: Record<string, number>;
      issues: Array<{
        dimension: string;
        severity: string;
        message: string;
        retry_instruction: string;
      }>;
    } | null;
    retry_count: number;
    evaluator_failed: boolean;
  } | null;
  runtime_meta?: {
    decision_fallback_used: boolean;
    generator_retry_count: number;
    generator_fallback_used: boolean;
  } | null;
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

type ReportResponse = {
  success_probability: number;
  likely_outcome: string;
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
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

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
    window.clearTimeout(timeoutId);
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
  simulationContext?: SimulationContextV2 | null,
  personaV2?: PersonaModelV2 | null,
): Promise<{
  targetMessage: ChatMessage | null;
  statusMessage: ChatMessage | null;
  action: ResponseAction;
  conversationEnded: boolean;
  simulation: SimulationReply;
  updatedPersona: Persona;
  simulationState: SimulationStateV2 | null;
}> {
  const result = await requestJson<SessionMessageResponse>(
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
      persona_id: simulationContext?.personaId,
      session_id: simulationContext?.sessionId,
      simulation_state: simulationContext?.state,
    },
  );

  const action = result.response?.action ?? "REPLY_NORMAL";
  const responseText = result.response?.text ?? result.target_message.content;
  const statusText =
    result.response?.status_text ??
    (result.target_message.role === "system" ? result.target_message.content : "");

  return {
    targetMessage: responseText
      ? toFrontendMessage({ role: "target", content: responseText })
      : null,
    statusMessage: statusText
      ? toFrontendMessage({ role: "system", content: statusText })
      : null,
    action,
    conversationEnded: result.response?.conversation_ended ?? false,
    simulation: result.simulation,
    updatedPersona: {
      ...persona,
      state: result.updated_state,
    },
    simulationState: result.simulation_state ?? null,
  };
}

export async function createSimulationReport(
  scenario: ScenarioKey,
  form: FormData,
  persona: Persona,
  messages: ChatMessage[],
): Promise<SimulationReport> {
  const result = await requestJson<ReportResponse>(
    "/api/session/report",
    {
      scenario,
      goal: form.goal,
      outcome: form.outcome,
      persona,
      messages: toBackendMessages(messages),
    },
    REPORT_REQUEST_TIMEOUT_MS,
  );

  return mapReportResponse(result);
}

function mapReportResponse(result: ReportResponse): SimulationReport {
  const score = Math.max(0, Math.min(100, Math.round(result.success_probability)));
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
