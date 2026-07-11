import { getCloudBaseDb } from "@/lib/cloudbase-client";
import type {
  ChatMessage,
  FormData,
  Persona,
  ScenarioKey,
  SimulationReport,
} from "@/lib/social-lab-types";
import type { SavedPersonaRecord, SavedSessionRecord } from "@/lib/social-lab-api";
import type { CloudBaseUser } from "@/components/social-lab/auth-provider";

const COLLECTIONS = {
  personas: "personas",
  sessions: "sessions",
  messages: "messages",
  reports: "reports",
  relationshipStates: "relationship_states",
};

async function ensureDb() {
  const cloudbaseDb = await getCloudBaseDb();
  if (!cloudbaseDb) {
    throw new Error("CloudBase 尚未配置，无法保存数据。");
  }
  return cloudbaseDb;
}

function ownerId(user: CloudBaseUser) {
  return user.id;
}

function now() {
  return new Date().toISOString();
}

export async function savePersonaToCloudBase({
  user,
  scenario,
  form,
  persona,
}: {
  user: CloudBaseUser;
  scenario: ScenarioKey;
  form: FormData;
  persona: Persona;
}) {
  const db = await ensureDb();
  const response = await db.collection(COLLECTIONS.personas).add({
    owner_id: ownerId(user),
    scenario,
    role: form.role,
    goal: form.goal,
    persona_json: persona,
    created_at: now(),
  });

  return response.id || response.ids?.[0] || response.insertedIds?.[0] || null;
}

export async function createSessionInCloudBase({
  user,
  scenario,
  form,
  personaId,
}: {
  user: CloudBaseUser;
  scenario: ScenarioKey;
  form: FormData;
  personaId?: string | null;
}) {
  const db = await ensureDb();
  const response = await db.collection(COLLECTIONS.sessions).add({
    owner_id: ownerId(user),
    persona_id: personaId || null,
    scenario,
    goal: form.goal,
    status: "active",
    created_at: now(),
  });

  return response.id || response.ids?.[0] || response.insertedIds?.[0] || null;
}

export async function saveMessageToCloudBase({
  sessionId,
  message,
}: {
  sessionId: string;
  message: ChatMessage;
}) {
  const db = await ensureDb();
  await db.collection(COLLECTIONS.messages).add({
    session_id: sessionId,
    role: message.role,
    content: message.text,
    created_at: now(),
  });
}

export async function saveRelationshipStateToCloudBase({
  sessionId,
  state,
}: {
  sessionId: string;
  state: Persona["state"];
}) {
  const db = await ensureDb();
  await db.collection(COLLECTIONS.relationshipStates).doc(sessionId).set({
    session_id: sessionId,
    ...state,
    updated_at: now(),
  });
}

export async function saveReportToCloudBase({
  sessionId,
  report,
}: {
  sessionId: string;
  report: SimulationReport;
}) {
  const db = await ensureDb();
  const response = await db.collection(COLLECTIONS.reports).add({
    session_id: sessionId,
    report_json: report,
    created_at: now(),
  });

  await db.collection(COLLECTIONS.sessions).doc(sessionId).update({
    status: "completed",
  });

  return response.id || response.ids?.[0] || response.insertedIds?.[0] || null;
}

export async function listCloudBasePersonas(user: CloudBaseUser) {
  const db = await ensureDb();
  const response = await db
    .collection(COLLECTIONS.personas)
    .where({ owner_id: ownerId(user) })
    .orderBy("created_at", "desc")
    .get();

  return response.data.map((item: any) => ({
    id: item._id || item.id,
    scenario: item.scenario,
    role: item.role || "",
    goal: item.goal || "",
    persona: item.persona_json,
    created_at: item.created_at,
  })) as SavedPersonaRecord[];
}

export async function listCloudBaseSessions(user: CloudBaseUser) {
  const db = await ensureDb();
  const response = await db
    .collection(COLLECTIONS.sessions)
    .where({ owner_id: ownerId(user) })
    .orderBy("created_at", "desc")
    .get();

  const records = await Promise.all(
    response.data.map(async (item: any) => {
      let personaTitle: string | null = null;
      if (item.persona_id) {
        const persona = await db.collection(COLLECTIONS.personas).doc(item.persona_id).get();
        personaTitle = persona.data?.[0]?.persona_json?.title || null;
      }

      const reports = await db
        .collection(COLLECTIONS.reports)
        .where({ session_id: item._id || item.id })
        .orderBy("created_at", "desc")
        .limit(1)
        .get();

      return {
        id: item._id || item.id,
        persona_id: item.persona_id || null,
        scenario: item.scenario,
        goal: item.goal || "",
        status: item.status || "active",
        created_at: item.created_at,
        persona_title: personaTitle,
        latest_report_id: reports.data?.[0]?._id || reports.data?.[0]?.id || null,
      };
    }),
  );

  return records as SavedSessionRecord[];
}

export async function getCloudBaseReport(reportId: string) {
  const db = await ensureDb();
  const response = await db.collection(COLLECTIONS.reports).doc(reportId).get();
  const item = response.data?.[0];
  if (!item) throw new Error("报告不存在。");
  return { id: item._id || item.id, report: item.report_json as Record<string, unknown> };
}

export async function deleteCloudBaseSession(sessionId: string) {
  const db = await ensureDb();
  await db.collection(COLLECTIONS.messages).where({ session_id: sessionId }).remove();
  await db.collection(COLLECTIONS.reports).where({ session_id: sessionId }).remove();
  await db.collection(COLLECTIONS.relationshipStates).doc(sessionId).remove();
  await db.collection(COLLECTIONS.sessions).doc(sessionId).remove();
}

export async function deleteCloudBasePersona(personaId: string) {
  const db = await ensureDb();
  await db.collection(COLLECTIONS.personas).doc(personaId).remove();
}
