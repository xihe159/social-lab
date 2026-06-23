"use client";

import { useMemo, useState } from "react";
import { MobileHeader } from "./mobile-header";
import { Sidebar } from "./sidebar";
import { ChatScreen } from "./screens/chat-screen";
import { LandingScreen } from "./screens/landing-screen";
import { PersonaScreen } from "./screens/persona-screen";
import { PersonScreen } from "./screens/person-screen";
import { ReportScreen } from "./screens/report-screen";
import { ScenarioScreen } from "./screens/scenario-screen";
import { scenarioPresets } from "@/lib/social-lab-data";
import {
  buildPersona,
  buildReply,
  buildReport,
  firstTargetMessage,
  formFromScenario,
  scoreMessage,
} from "@/lib/social-lab-logic";
import type {
  ChatMessage,
  FormData,
  Persona,
  ScenarioKey,
  SimulationReport,
} from "@/lib/social-lab-types";

export function SocialLabApp() {
  const [step, setStep] = useState(0);
  const [scenario, setScenario] = useState<ScenarioKey>("advisor");
  const [form, setForm] = useState<FormData>(() =>
    formFromScenario("advisor"),
  );
  const [persona, setPersona] = useState<Persona>(() =>
    buildPersona("advisor", formFromScenario("advisor")),
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [score, setScore] = useState(68);
  const [report, setReport] = useState<SimulationReport>(() =>
    buildReport("advisor", 68, false),
  );
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toast, setToast] = useState("");
  const [retryDraft, setRetryDraft] = useState("");

  const preset = scenarioPresets[scenario];
  const progress = useMemo(() => `${((step + 1) / 6) * 100}%`, [step]);

  const goToStep = (nextStep: number) => {
    setStep(Math.max(0, Math.min(5, nextStep)));
    setSidebarOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 1800);
  };

  const selectScenario = (nextScenario: ScenarioKey, openScenario = false) => {
    setScenario(nextScenario);
    setForm(formFromScenario(nextScenario));
    if (openScenario) goToStep(1);
  };

  const generatePersona = () => {
    if (!form.role.trim()) {
      showToast("请至少说明你想模拟谁。");
      return;
    }
    setPersona(buildPersona(scenario, form));
    goToStep(3);
  };

  const startChat = (draft = "") => {
    setMessages([
      {
        id: crypto.randomUUID(),
        role: "target",
        text: firstTargetMessage(scenario),
      },
    ]);
    setScore(68);
    setRetryDraft(draft);
    goToStep(4);
  };

  const sendMessage = (text: string) => {
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", text },
      {
        id: crypto.randomUUID(),
        role: "target",
        text: buildReply(scenario, text),
      },
    ]);
    setScore((current) => scoreMessage(current, text));
  };

  const finishSimulation = () => {
    const nextReport = buildReport(
      scenario,
      score,
      messages.some((message) => message.role === "user"),
    );
    setReport(nextReport);
    goToStep(5);
  };

  const copyRewrite = async () => {
    try {
      await navigator.clipboard.writeText(report.rewrite);
      showToast("已复制优化表达。");
    } catch {
      showToast("复制失败，可以直接选中文本复制。");
    }
  };

  return (
    <div className="app-shell">
      <Sidebar
        currentStep={step}
        isOpen={sidebarOpen}
        onStepChange={goToStep}
      />

      <main className="main-panel">
        <MobileHeader
          currentStep={step}
          onBack={() => goToStep(step - 1)}
          onMenu={() => setSidebarOpen((open) => !open)}
        />

        <div className="progress-track" aria-hidden="true">
          <span style={{ width: progress }} />
        </div>

        {step === 0 && (
          <LandingScreen
            onStart={() => goToStep(1)}
            onPresetSelect={(nextScenario) =>
              selectScenario(nextScenario, true)
            }
          />
        )}
        {step === 1 && (
          <ScenarioScreen
            scenario={scenario}
            form={form}
            onScenarioChange={(nextScenario) =>
              selectScenario(nextScenario)
            }
            onFormChange={(patch) =>
              setForm((current) => ({ ...current, ...patch }))
            }
            onContinue={() => {
              if (!form.goal.trim()) {
                showToast("请至少填写沟通目标。");
                return;
              }
              goToStep(2);
            }}
          />
        )}
        {step === 2 && (
          <PersonScreen
            form={form}
            onFormChange={(patch) =>
              setForm((current) => ({ ...current, ...patch }))
            }
            onGenerate={generatePersona}
          />
        )}
        {step === 3 && (
          <PersonaScreen
            persona={persona}
            onStart={() => startChat()}
            onTune={() => showToast("画像编辑接口将在下一阶段接入。")}
          />
        )}
        {step === 4 && (
          <ChatScreen
            title={preset.chatTitle}
            persona={persona}
            messages={messages}
            initialDraft={retryDraft}
            onSend={sendMessage}
            onReset={() => startChat()}
            onFinish={finishSimulation}
          />
        )}
        {step === 5 && (
          <ReportScreen
            report={report}
            onCopy={copyRewrite}
            onRetry={() => startChat(report.rewrite)}
          />
        )}
      </main>

      <div
        className={`toast${toast ? " is-visible" : ""}`}
        role="status"
        aria-live="polite"
      >
        {toast}
      </div>
    </div>
  );
}
