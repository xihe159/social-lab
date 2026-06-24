// G 20260624
/*
    把前端表单数据发送到 /api/persona/create，然后拿回 LLM 生成的结构化 Persona。
*/

import type { FormData, Persona, ScenarioKey } from "@/lib/social-lab-types";

export type PersonaCreateResponse = {
  persona: Persona;
  opening_message: string;
  communication_rules: string[];
  evidence: {
    source: "goal" | "outcome" | "role" | "relation" | "habit" | "chatLog";
    quote: string;
    inference: string;
  }[];
  assumptions: string[];
  confidence: number;
};

export async function createPersona(
  scenario: ScenarioKey,
  form: FormData,
): Promise<PersonaCreateResponse> {
  const response = await fetch("/api/persona/create", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      scenario,
      goal: form.goal,
      outcome: form.outcome,
      role: form.role,
      relation: form.relation,
      habit: form.habit,
      chatLog: form.chatLog,
    }),
  });

  if (!response.ok) {
    throw new Error("Persona creation failed");
  }

  return response.json();
}

// G 20260624 #