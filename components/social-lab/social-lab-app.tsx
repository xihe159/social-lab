"use client";

import {
  FileText,
  Home,
  Lock,
  MessageSquare,
  Target,
} from "lucide-react";
import { useMemo, useState } from "react";
import { MobileHeader } from "./mobile-header";
import {
  createPersona,
  createSimulationReport,
  sendSessionMessage,
} from "@/lib/social-lab-api";
import type {
  ChatRecordAnalysis,
  PersonaModelV2,
  SimulationContextV2,
} from "@/lib/social-lab-api";
import { Sidebar } from "./sidebar";
import { ChatScreen } from "./screens/chat-screen";
import { LandingScreen } from "./screens/landing-screen";
import { PersonaScreen } from "./screens/persona-screen";
import { PersonScreen } from "./screens/person-screen";
import { ReportScreen } from "./screens/report-screen";
import { ScenarioScreen } from "./screens/scenario-screen";
import { scenarioPresets } from "@/lib/social-lab-data";
import { formFromScenario } from "@/lib/social-lab-logic";
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
  const [persona, setPersona] = useState<Persona | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [report, setReport] = useState<SimulationReport | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toast, setToast] = useState("");
  const [retryDraft, setRetryDraft] = useState("");
  const [maxUnlockedStep, setMaxUnlockedStep] = useState(1);
  const [personaLoading, setPersonaLoading] = useState(false);
  const [messageLoading, setMessageLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [simulationContext, setSimulationContext] =
    useState<SimulationContextV2 | null>(null);
  const [conversationEnded, setConversationEnded] = useState(false);
  const [personaV2, setPersonaV2] = useState<PersonaModelV2 | null>(null);
  const [chatAnalysis, setChatAnalysis] = useState<ChatRecordAnalysis | null>(null);

  const preset = scenarioPresets[scenario];
  const progress = useMemo(() => `${(step / 5) * 100}%`, [step]);

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 1800);
  };

  const goToStep = (nextStep: number) => {
    const safeStep = Math.max(0, Math.min(5, nextStep));
    if (safeStep > maxUnlockedStep) {
      const currentLabel =
        maxUnlockedStep < 2
          ? "场景信息"
          : maxUnlockedStep < 4
            ? "人物信息"
            : "当前步骤";
      showToast(`请先完成「${currentLabel}」，即可进入下一步。`);
      setSidebarOpen(false);
      return;
    }
    setStep(safeStep);
    setSidebarOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const unlockAndGo = (nextStep: number) => {
    setMaxUnlockedStep((current) => Math.max(current, nextStep));
    setStep(nextStep);
    setSidebarOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const selectScenario = (nextScenario: ScenarioKey, openScenario = false) => {
    setScenario(nextScenario);
    setForm(formFromScenario(nextScenario));
    setPersona(null);
    setMessages([]);
    setReport(null);
    setRetryDraft("");
    setSimulationContext(null);
    setConversationEnded(false);
    setPersonaV2(null);
    setChatAnalysis(null);
    setMaxUnlockedStep(1);
    if (openScenario) unlockAndGo(1);
  };

  const generatePersona = async () => {
    if (personaLoading) return;
    if (!form.role.trim()) {
      showToast("请至少说明你想模拟谁。");
      return;
    }
    try {
      setPersonaLoading(true);
      const result = await createPersona(scenario, form);
      setPersona(result.persona);
      setPersonaV2(result.persona_v2 ?? null);
      setChatAnalysis(result.chat_analysis ?? null);
      setSimulationContext({
        personaId: result.persona_v2?.persona_id ?? `persona_${crypto.randomUUID()}`,
        sessionId: `session_${crypto.randomUUID()}`,
        state: null,
      });
      setConversationEnded(false);
      // 不让 AI 目标人物先开口
      // 用户应该先输入自己想说的话
      setMessages([]);
      setReport(null);
      unlockAndGo(3);
    } catch (error) {
      console.error(error);
      showToast(
        error instanceof Error
          ? error.message
          : "AI 画像生成失败，请稍后重试。",
      );
    } finally {
      setPersonaLoading(false);
    }
  };

  const startChat = (draft = "") => {
    if (!persona) {
      showToast("请先生成画像。");
      return;
    }
    setRetryDraft(draft);
    unlockAndGo(4);
  };

  const sendMessage = async (text: string) => {
    if (messageLoading || !persona) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text,
    };

    setMessages((current) => [...current, userMessage]);

    try {
      setMessageLoading(true);
      const result = await sendSessionMessage(
        scenario,
        form,
        persona,
        messages,
        text,
        simulationContext,
        personaV2,
      );
      setMessages((current) => {
        const next = [...current];
        if (result.targetMessage) next.push(result.targetMessage);
        if (result.statusMessage) next.push(result.statusMessage);
        return next;
      });
      setPersona(result.updatedPersona);
      setConversationEnded(result.conversationEnded);
      setSimulationContext((current) =>
        current
          ? { ...current, state: result.simulationState }
          : current,
      );
    } catch (error) {
      console.error(error);
      showToast(
        error instanceof Error ? error.message : "AI 回复失败，请稍后重试。",
      );
    } finally {
      setMessageLoading(false);
    }
  };

  const finishSimulation = async () => {
    if (reportLoading || messageLoading || !persona) return;
    if (!messages.some((message) => message.role === "user")) {
      showToast("请至少发送一句话后再生成报告。");
      return;
    }

    try {
      setReportLoading(true);
      const nextReport = await createSimulationReport(
        scenario,
        form,
        persona,
        messages,
      );
      setReport(nextReport);
      unlockAndGo(5);
    } catch (error) {
      console.error(error);
      showToast(
        error instanceof Error ? error.message : "AI 报告生成失败，请稍后重试。",
      );
    } finally {
      setReportLoading(false);
    }
  };

  const copyRewrite = async () => {
    if (!report) return;
    try {
      await navigator.clipboard.writeText(report.rewrite);
      showToast("已复制优化表达。");
    } catch {
      showToast("复制失败，可以直接选中文本复制。");
    }
  };

  const resetChat = () => {
    setMessages([]);
    setRetryDraft("");
    setConversationEnded(false);
    setSimulationContext((current) =>
      current
        ? {
            ...current,
            sessionId: `session_${crypto.randomUUID()}`,
            state: null,
          }
        : current,
    );
  };

  return (
    <div className="app-shell">
      <Sidebar
        currentStep={step}
        isOpen={sidebarOpen}
        maxUnlockedStep={maxUnlockedStep}
        onStepChange={goToStep}
      />

      <main className="main-panel">
        <MobileHeader
          currentStep={step}
          onBack={() => goToStep(step - 1)}
        />

        {step > 0 && (
          <div className="progress-track" aria-hidden="true">
            <span style={{ width: progress }} />
          </div>
        )}

        {step === 0 && (
          <LandingScreen
            onPresetSelect={(nextScenario) =>
              selectScenario(nextScenario, true)
            }
          />
        )}
        {step === 1 && (
          <ScenarioScreen
            scenario={scenario}
            form={form}
            onFormChange={(patch) =>
              setForm((current) => ({ ...current, ...patch }))
            }
            onContinue={(patch) => {
              const nextForm = { ...form, ...patch };
              if (!nextForm.goal.trim()) {
                showToast("请至少填写沟通目标。");
                return;
              }
              setForm(nextForm);
              unlockAndGo(2);
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
            isGenerating={personaLoading}
            canGenerate={Boolean(form.role.trim())}
          />
        )}
        {step === 3 && persona && (
          <PersonaScreen
            persona={persona}
            chatAnalysis={chatAnalysis}
            onStart={() => startChat()}
            onTune={() => showToast("画像编辑接口将在下一阶段接入。")}
          />
        )}
        {step === 4 && persona && (
          <ChatScreen
            title={preset.chatTitle}
            persona={persona}
            messages={messages}
            initialDraft={retryDraft}
            onSend={sendMessage}
            onReset={resetChat}
            onFinish={finishSimulation}
            isSending={messageLoading}
            isFinishing={reportLoading || messageLoading}
            conversationEnded={conversationEnded}
          />
        )}
        {step === 5 && report && (
          <ReportScreen
            report={report}
            onCopy={copyRewrite}
            onRetry={() => startChat(report.rewrite)}
          />
        )}
      </main>

      <MobileBottomNav
        currentStep={step}
        maxUnlockedStep={maxUnlockedStep}
        onStepChange={goToStep}
      />

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

function MobileBottomNav({
  currentStep,
  maxUnlockedStep,
  onStepChange,
}: {
  currentStep: number;
  maxUnlockedStep: number;
  onStepChange: (step: number) => void;
}) {
  const items = [
    { label: "首页", icon: Home, step: 0 },
    { label: "场景", icon: Target, step: 1 },
    { label: "模拟", icon: MessageSquare, step: 4 },
    { label: "报告", icon: FileText, step: 5 },
  ];

  return (
    <nav className="bottom-nav" aria-label="移动端流程导航">
      {items.map((item, index) => {
        const Icon = item.icon;
        const targetStep = item.step;
        const locked = targetStep > maxUnlockedStep;
        return (
          <button
            className={`bottom-nav-item${currentStep === targetStep ? " is-active" : ""}${locked ? " is-locked" : ""}`}
            key={item.label}
            onClick={() => onStepChange(targetStep)}
            type="button"
          >
            {locked ? <Lock size={18} /> : <Icon size={20} />}
            <span>{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
