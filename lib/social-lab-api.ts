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

type RequestOptions = {
  accessToken?: string | null;
  method?: "GET" | "POST" | "DELETE";
};

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
  persona_id?: string;
  saved?: boolean;
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
  session_id?: string;
  saved?: boolean;
};

type ReportResponse = {
  success_probability: number;
  likely_outcome: string;
  strengths: string[];
  problems: string[];
  key_risks: string[];
  suggested_rewrite: string;
  next_step_advice: string;
  report_id?: string;
  saved?: boolean;
};

export type CurrentUser = {
  id: string;
  email: string | null;
};

export type SavedPersonaRecord = {
  id: string;
  scenario: ScenarioKey;
  role: string;
  goal: string;
  persona: Persona;
  created_at: string;
};

export type SavedSessionRecord = {
  id: string;
  persona_id: string | null;
  scenario: ScenarioKey;
  goal: string;
  status: string;
  created_at: string;
  persona_title?: string | null;
  latest_report_id?: string | null;
};

export type SavedSessionDetail = SavedSessionRecord & {
  messages: ChatMessage[];
  report: SimulationReport | null;
  persona: Persona | null;
};

async function requestJson<T>(
  path: string,
  body?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 90_000);
  const headers: HeadersInit = {};

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (options.accessToken) {
    headers.Authorization = `Bearer ${options.accessToken}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: options.method ?? (body === undefined ? "GET" : "POST"),
      headers: Object.keys(headers).length > 0 ? headers : undefined,
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
  options: RequestOptions = {},
): Promise<PersonaCreateResponse> {
  return requestJson<PersonaCreateResponse>("/api/persona/create", {
    scenario,
    goal: form.goal,
    outcome: form.outcome,
    role: form.role,
    relation: form.relation,
    habit: form.habit,
    chatLog: form.chatLog,
  }, options);
}

export async function sendSessionMessage(
  scenario: ScenarioKey,
  form: FormData,
  persona: Persona,
  messages: ChatMessage[],
  userMessage: string,
  options: RequestOptions & { personaId?: string | null; sessionId?: string | null } = {},
): Promise<{
  targetMessage: ChatMessage;
  simulation: SimulationReply;
  updatedPersona: Persona;
  sessionId?: string;
  saved?: boolean;
}> {
  const result = await requestJson<SessionMessageResponse>(
    "/api/session/message",
    {
      scenario,
      goal: form.goal,
      outcome: form.outcome,
      persona,
      messages: toBackendMessages(messages),
      user_message: userMessage,
      persona_id: options.personaId,
      session_id: options.sessionId,
    },
    options,
  );

  return {
    targetMessage: toFrontendMessage(result.target_message),
    simulation: result.simulation,
    updatedPersona: {
      ...persona,
      state: result.updated_state,
    },
    sessionId: result.session_id,
    saved: result.saved,
  };
}

export async function createSimulationReport(
  scenario: ScenarioKey,
  form: FormData,
  persona: Persona,
  messages: ChatMessage[],
  options: RequestOptions & { personaId?: string | null; sessionId?: string | null } = {},
): Promise<SimulationReport> {
  const result = await requestJson<ReportResponse>("/api/session/report", {
    scenario,
    goal: form.goal,
    outcome: form.outcome,
    persona,
    messages: toBackendMessages(messages),
    persona_id: options.personaId,
    session_id: options.sessionId,
  }, options);

  return {
    ...mapReportResponse(result),
    id: result.report_id,
    saved: result.saved,
  };
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

export async function getCurrentUser(options: RequestOptions) {
  return requestJson<CurrentUser>("/api/me", undefined, options);
}

export async function listPersonas(options: RequestOptions) {
  return requestJson<SavedPersonaRecord[]>("/api/personas", undefined, options);
}

export async function listSessions(options: RequestOptions) {
  return requestJson<SavedSessionRecord[]>("/api/sessions", undefined, options);
}

export async function getSessionDetail(id: string, options: RequestOptions) {
  return requestJson<SavedSessionDetail>(`/api/sessions/${id}`, undefined, options);
}

export async function getReportRecord(id: string, options: RequestOptions) {
  return requestJson<{ id: string; report: Record<string, unknown> }>(
    `/api/reports/${id}`,
    undefined,
    options,
  );
}

export async function deleteSessionRecord(id: string, options: RequestOptions) {
  return requestJson<{ ok: boolean }>(`/api/sessions/${id}`, undefined, {
    ...options,
    method: "DELETE",
  });
}

export async function deletePersonaRecord(id: string, options: RequestOptions) {
  return requestJson<{ ok: boolean }>(`/api/personas/${id}`, undefined, {
    ...options,
    method: "DELETE",
  });
}

export async function importGuestRun(
  payload: {
    scenario: ScenarioKey;
    form: FormData;
    persona: Persona;
    messages: ChatMessage[];
    report?: SimulationReport | null;
  },
  options: RequestOptions,
) {
  return requestJson<{ saved: boolean; session_id?: string; persona_id?: string }>(
    "/api/guest-runs/import",
    {
      ...payload,
      messages: toBackendMessages(payload.messages),
    },
    options,
  );
}
