import type {
  ChatMessage,
  FormData,
  Persona,
  ScenarioKey,
  SimulationReport,
} from "@/lib/social-lab-types";

const API_BASE_URL = process.env.NEXT_PUBLIC_AGENT_API_BASE_URL?.replace(
  /\/$/,
  "",
);

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

export type SessionMessageResponse = {
  target_message: BackendChatMessage;
  simulation: SimulationReply;
  updated_state: Persona["state"];
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

async function requestJson<T>(path: string, body?: unknown): Promise<T> {
  if (!API_BASE_URL) {
    throw new Error(
      "缺少 NEXT_PUBLIC_AGENT_API_BASE_URL，请先配置后端 API 地址。",
    );
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers:
      body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

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
): Promise<{
  targetMessage: ChatMessage;
  simulation: SimulationReply;
  updatedPersona: Persona;
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
    },
  );

  return {
    targetMessage: toFrontendMessage(result.target_message),
    simulation: result.simulation,
    updatedPersona: {
      ...persona,
      state: result.updated_state,
    },
  };
}

export async function createSimulationReport(
  scenario: ScenarioKey,
  form: FormData,
  persona: Persona,
  messages: ChatMessage[],
): Promise<SimulationReport> {
  const result = await requestJson<ReportResponse>("/api/session/report", {
    scenario,
    goal: form.goal,
    outcome: form.outcome,
    persona,
    messages: toBackendMessages(messages),
  });

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
