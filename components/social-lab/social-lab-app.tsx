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
import { Sidebar } from "./sidebar";
import { ChatScreen } from "./screens/chat-screen";
import { LandingScreen } from "./screens/landing-screen";
import { PersonaScreen } from "./screens/persona-screen";
import { PersonScreen } from "./screens/person-screen";
import { ReportScreen } from "./screens/report-screen";
import { ScenarioScreen } from "./screens/scenario-screen";

import {
  appendTurnTrace,
  buildDynamicsSnapshot,
  createPersona,
  createSimulationReport,
  sendSessionMessage,
} from "@/lib/social-lab-api";
import type {
  ChatRecordAnalysis,
  ConversationDynamics,
  ConversationDynamicsSnapshot,
  PersonaModelV2,
  SessionMemory,
  SimulationContextV2,
} from "@/lib/social-lab-api";
import { scenarioPresets } from "@/lib/social-lab-data";
import { formFromScenario } from "@/lib/social-lab-logic";
import type {
  ChatMessage,
  ConversationTurnTrace,
  FormData,
  Persona,
  ScenarioKey,
  SimulationReport,
} from "@/lib/social-lab-types";

const MAX_DYNAMICS_HISTORY = 10;
const MAX_TURN_TRACES = 20;

function clonePersona(value: Persona): Persona {
  return {
    ...value,
    state: {
      ...value.state,
    },
  };
}

export function SocialLabApp() {
  const [step, setStep] = useState(0);
  const [scenario, setScenario] =
    useState<ScenarioKey>("advisor");
  const [form, setForm] = useState<FormData>(() =>
    formFromScenario("advisor"),
  );

  const [persona, setPersona] =
    useState<Persona | null>(null);
  const [initialPersona, setInitialPersona] =
    useState<Persona | null>(null);
  const [personaV2, setPersonaV2] =
    useState<PersonaModelV2 | null>(null);
  const [chatAnalysis, setChatAnalysis] =
    useState<ChatRecordAnalysis | null>(null);

  const [messages, setMessages] =
    useState<ChatMessage[]>([]);
  const [report, setReport] =
    useState<SimulationReport | null>(null);

  const [currentDynamics, setCurrentDynamics] =
    useState<ConversationDynamics | null>(null);
  const [dynamicsHistory, setDynamicsHistory] =
    useState<ConversationDynamicsSnapshot[]>([]);
  const [turnTraces, setTurnTraces] =
    useState<ConversationTurnTrace[]>([]);
  const [sessionMemory, setSessionMemory] =
    useState<SessionMemory | null>(null);

  const [simulationContext, setSimulationContext] =
    useState<SimulationContextV2 | null>(null);
  const [conversationEnded, setConversationEnded] =
    useState(false);

  const [sidebarOpen, setSidebarOpen] =
    useState(false);
  const [toast, setToast] = useState("");
  const [retryDraft, setRetryDraft] =
    useState("");
  const [maxUnlockedStep, setMaxUnlockedStep] =
    useState(1);

  const [personaLoading, setPersonaLoading] =
    useState(false);
  const [messageLoading, setMessageLoading] =
    useState(false);
  const [reportLoading, setReportLoading] =
    useState(false);

  const preset = scenarioPresets[scenario];
  const progress = useMemo(
    () => `${(step / 5) * 100}%`,
    [step],
  );

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 1800);
  };

  const goToStep = (nextStep: number) => {
    const safeStep = Math.max(
      0,
      Math.min(5, nextStep),
    );

    if (safeStep > maxUnlockedStep) {
      const currentLabel =
        maxUnlockedStep < 2
          ? "场景信息"
          : maxUnlockedStep < 4
            ? "人物信息"
            : "当前步骤";

      showToast(
        `请先完成「${currentLabel}」，即可进入下一步。`,
      );
      setSidebarOpen(false);
      return;
    }

    setStep(safeStep);
    setSidebarOpen(false);
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const unlockAndGo = (nextStep: number) => {
    setMaxUnlockedStep((current) =>
      Math.max(current, nextStep),
    );
    setStep(nextStep);
    setSidebarOpen(false);
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const clearConversationData = () => {
    setMessages([]);
    setReport(null);
    setRetryDraft("");
    setConversationEnded(false);

    setCurrentDynamics(null);
    setDynamicsHistory([]);
    setTurnTraces([]);
    setSessionMemory(null);
  };

  const createFreshSimulationContext = (
    personaId: string,
  ): SimulationContextV2 => ({
    personaId,
    sessionId: `session_${crypto.randomUUID()}`,
    state: null,
  });

  const selectScenario = (
    nextScenario: ScenarioKey,
    openScenario = false,
  ) => {
    setScenario(nextScenario);
    setForm(formFromScenario(nextScenario));

    setPersona(null);
    setInitialPersona(null);
    setPersonaV2(null);
    setChatAnalysis(null);
    setSimulationContext(null);

    clearConversationData();
    setMaxUnlockedStep(1);

    if (openScenario) {
      unlockAndGo(1);
    }
  };

  const generatePersona = async () => {
    if (personaLoading) {
      return;
    }

    if (!form.role.trim()) {
      showToast("请至少说明你想模拟谁。");
      return;
    }

    try {
      setPersonaLoading(true);

      const result = await createPersona(
        scenario,
        form,
      );

      const generatedPersona =
        clonePersona(result.persona);

      setPersona(generatedPersona);
      setInitialPersona(
        clonePersona(result.persona),
      );
      setPersonaV2(
        result.persona_v2 ?? null,
      );
      setChatAnalysis(
        result.chat_analysis ?? null,
      );

      const personaId =
        result.persona_v2?.persona_id ??
        `persona_${crypto.randomUUID()}`;

      setSimulationContext(
        createFreshSimulationContext(personaId),
      );

      // 新画像必须开始一段全新的模拟，
      // 避免旧 Dynamics、Memory 和轨迹污染。
      clearConversationData();

      // 不让 AI 目标人物先开口；
      // 用户应该先输入自己想说的话。
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
    if (
      messageLoading ||
      conversationEnded ||
      !persona
    ) {
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text,
    };

    // 先把用户消息显示在界面上。
    setMessages((current) => [
      ...current,
      userMessage,
    ]);

    try {
      setMessageLoading(true);

      const result =
        await sendSessionMessage(
          scenario,
          form,
          persona,
          messages,
          text,
          simulationContext,
          personaV2,
          {
            currentDynamics,
            history: dynamicsHistory,
            turnTraces,
            memory: sessionMemory,
          },
        );

      setMessages((current) => {
        const next = [...current];

        if (result.targetMessage) {
          next.push(result.targetMessage);
        }

        if (result.statusMessage) {
          next.push(result.statusMessage);
        }

        return next;
      });

      setPersona(result.updatedPersona);
      setConversationEnded(
        result.conversationEnded,
      );
      setSessionMemory(result.updatedMemory);
      setCurrentDynamics(
        result.currentDynamics,
      );

      if (
        result.currentDynamics &&
        result.turnTrace
      ) {
        const snapshot =
          buildDynamicsSnapshot(
            result.currentDynamics,
            result.turnTrace.turnIndex,
          );

        setDynamicsHistory((current) => [
          ...current,
          snapshot,
        ].slice(-MAX_DYNAMICS_HISTORY));
      }

      if (result.turnTrace) {
        setTurnTraces((current) =>
          appendTurnTrace(
            current,
            result.turnTrace,
            MAX_TURN_TRACES,
          ),
        );
      }

      setSimulationContext((current) =>
        current
          ? {
              ...current,
              state: result.simulationState,
            }
          : current,
      );
    } catch (error) {
      console.error(error);

      // 请求失败时撤销刚才的乐观消息，
      // 防止没有目标人物回复的消息进入下一轮上下文。
      setMessages((current) =>
        current.filter(
          (message) =>
            message.id !== userMessage.id,
        ),
      );

      showToast(
        error instanceof Error
          ? error.message
          : "AI 回复失败，请稍后重试。",
      );
    } finally {
      setMessageLoading(false);
    }
  };

  const finishSimulation = async () => {
    if (
      reportLoading ||
      messageLoading ||
      !persona
    ) {
      return;
    }

    if (
      !messages.some(
        (message) => message.role === "user",
      )
    ) {
      showToast(
        "请至少发送一句话后再生成报告。",
      );
      return;
    }

    try {
      setReportLoading(true);

      const nextReport =
        await createSimulationReport(
          scenario,
          form,
          persona,
          messages,
          {
            currentDynamics,
            history: dynamicsHistory,
            turnTraces,
            memory: sessionMemory,
          },
        );

      setReport(nextReport);
      unlockAndGo(5);
    } catch (error) {
      console.error(error);
      showToast(
        error instanceof Error
          ? error.message
          : "AI 报告生成失败，请稍后重试。",
      );
    } finally {
      setReportLoading(false);
    }
  };

  const copyRewrite = async () => {
    if (!report) {
      return;
    }

    try {
      await navigator.clipboard.writeText(
        report.rewrite,
      );
      showToast("已复制优化表达。");
    } catch {
      showToast(
        "复制失败，可以直接选中文本复制。",
      );
    }
  };

  const resetChat = () => {
    clearConversationData();

    if (initialPersona) {
      setPersona(clonePersona(initialPersona));
    }

    setSimulationContext((current) =>
      current
        ? createFreshSimulationContext(
            current.personaId,
          )
        : current,
    );
  };

  const retryWithRewrite = () => {
    if (!report) {
      return;
    }

    const draft = report.rewrite;

    clearConversationData();

    if (initialPersona) {
      setPersona(clonePersona(initialPersona));
    }

    setSimulationContext((current) =>
      current
        ? createFreshSimulationContext(
            current.personaId,
          )
        : current,
    );

    setRetryDraft(draft);
    unlockAndGo(4);
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
          <div
            className="progress-track"
            aria-hidden="true"
          >
            <span style={{ width: progress }} />
          </div>
        )}

        {step === 0 && (
          <LandingScreen
            onPresetSelect={(nextScenario) =>
              selectScenario(
                nextScenario,
                true,
              )
            }
          />
        )}

        {step === 1 && (
          <ScenarioScreen
            scenario={scenario}
            form={form}
            onFormChange={(patch) =>
              setForm((current) => ({
                ...current,
                ...patch,
              }))
            }
            onContinue={(patch) => {
              const nextForm = {
                ...form,
                ...patch,
              };

              if (!nextForm.goal.trim()) {
                showToast(
                  "请至少填写沟通目标。",
                );
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
              setForm((current) => ({
                ...current,
                ...patch,
              }))
            }
            onGenerate={generatePersona}
            isGenerating={personaLoading}
            canGenerate={Boolean(
              form.role.trim(),
            )}
          />
        )}

        {step === 3 && persona && (
          <PersonaScreen
            persona={persona}
            chatAnalysis={chatAnalysis}
            onStart={() => startChat()}
            onTune={() =>
              showToast(
                "画像编辑接口将在下一阶段接入。",
              )
            }
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
            isFinishing={
              reportLoading || messageLoading
            }
            conversationEnded={
              conversationEnded
            }
          />
        )}

        {step === 5 && report && (
          <ReportScreen
            report={report}
            onCopy={copyRewrite}
            onRetry={retryWithRewrite}
          />
        )}
      </main>

      <MobileBottomNav
        currentStep={step}
        maxUnlockedStep={maxUnlockedStep}
        onStepChange={goToStep}
      />

      <div
        className={`toast${
          toast ? " is-visible" : ""
        }`}
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
    {
      label: "首页",
      icon: Home,
      step: 0,
    },
    {
      label: "场景",
      icon: Target,
      step: 1,
    },
    {
      label: "模拟",
      icon: MessageSquare,
      step: 4,
    },
    {
      label: "报告",
      icon: FileText,
      step: 5,
    },
  ];

  return (
    <nav
      className="bottom-nav"
      aria-label="移动端流程导航"
    >
      {items.map((item) => {
        const Icon = item.icon;
        const targetStep = item.step;
        const locked =
          targetStep > maxUnlockedStep;

        return (
          <button
            className={`bottom-nav-item${
              currentStep === targetStep
                ? " is-active"
                : ""
            }${
              locked
                ? " is-locked"
                : ""
            }`}
            key={item.label}
            onClick={() =>
              onStepChange(targetStep)
            }
            type="button"
          >
            {locked ? (
              <Lock size={18} />
            ) : (
              <Icon size={20} />
            )}
            <span>{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
