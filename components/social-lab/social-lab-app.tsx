"use client";

import { FileText, Home, Lock, MessageSquare, Target } from "lucide-react";
import { useMemo, useState } from "react";

import { MobileHeader } from "./mobile-header";
import {
  createPersona,
  createSimulationReport,
  sendSessionMessage,
} from "@/lib/social-lab-api";
import type {
  ChatRecordAnalysis,
  ConversationDynamics,
  PersonaModelV2,
  SimulationContextV2,
  StateTimelineItem,
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
  const [form, setForm] = useState<FormData>(() => formFromScenario("advisor"));
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

  /*
   * Persona / Simulation V2 状态。
   * 这些状态保留项目现有的 V2 会话能力。
   */
  const [simulationContext, setSimulationContext] =
    useState<SimulationContextV2 | null>(null);
  const [conversationEnded, setConversationEnded] = useState(false);
  const [personaV2, setPersonaV2] = useState<PersonaModelV2 | null>(null);
  const [chatAnalysis, setChatAnalysis] = useState<ChatRecordAnalysis | null>(
    null,
  );

  /*
   * StateAgent 动态指标。
   *
   * currentDynamics:
   *   只保存最新一轮指标，下一轮发送消息时传回后端。
   *
   * stateTimeline:
   *   保存每一轮完整指标，生成 CoachAgent 报告时提交。
   */
  const [currentDynamics, setCurrentDynamics] =
    useState<ConversationDynamics | null>(null);
  const [stateTimeline, setStateTimeline] = useState<StateTimelineItem[]>([]);

  const preset = scenarioPresets[scenario];
  const progress = useMemo(() => `${(step / 5) * 100}%`, [step]);

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 1800);
  };

  const clearDynamicsState = () => {
    setCurrentDynamics(null);
    setStateTimeline([]);
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
    setPersonaV2(null);
    setChatAnalysis(null);
    setSimulationContext(null);

    setMessages([]);
    setReport(null);
    setRetryDraft("");
    setConversationEnded(false);
    clearDynamicsState();

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

      const result = await createPersona(scenario, form);

      setPersona(result.persona);
      setPersonaV2(result.persona_v2 ?? null);
      setChatAnalysis(result.chat_analysis ?? null);

      setSimulationContext({
        personaId:
          result.persona_v2?.persona_id ?? `persona_${crypto.randomUUID()}`,
        sessionId: `session_${crypto.randomUUID()}`,
        state: null,
      });

      /*
       * 新画像代表一段全新的模拟。
       * 不允许旧会话的动态指标进入新报告。
       */
      clearDynamicsState();
      setConversationEnded(false);

      /*
       * 不让 AI 目标人物先开口。
       * 用户应先输入自己希望测试的表达。
       */
      setMessages([]);
      setReport(null);
      setRetryDraft("");

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
    if (messageLoading || !persona || conversationEnded) {
      return;
    }

    const trimmedText = text.trim();

    if (!trimmedText) {
      return;
    }

    /*
     * messages 是本轮发送前的历史记录。
     * 最新输入通过 user_message 单独提交，不能重复放入 messages。
     */
    const historyBeforeTurn = messages;

    /*
     * 即使中间某一轮没有生成 state_metrics，
     * turnIndex 也应按照真实用户轮次递增。
     */
    const turnIndex =
      historyBeforeTurn.filter((message) => message.role === "user").length + 1;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text: trimmedText,
    };

    /*
     * 先显示用户输入，提高聊天响应感。
     * 请求失败时会回滚这一条消息。
     */
    setMessages((current) => [...current, userMessage]);

    try {
      setMessageLoading(true);

      /*
       * 这里采用 options 对象传入 V2 上下文与 StateAgent 指标。
       * 对应的 lib/social-lab-api.ts 需要支持：
       *
       * {
       *   simulationContext,
       *   personaV2,
       *   currentDynamics
       * }
       */
      const result = await sendSessionMessage(
        scenario,
        form,
        persona,
        historyBeforeTurn,
        trimmedText,
        {
          simulationContext,
          personaV2,
          currentDynamics,
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
      setConversationEnded(result.conversationEnded);

      setSimulationContext((current) =>
        current
          ? {
              ...current,
              state: result.simulationState,
            }
          : current,
      );

      /*
       * 优先使用真正的目标人物回复。
       * 如果 V2 流程只返回状态消息，则将状态消息作为本轮可追踪回复。
       */
      const targetReply =
        result.targetMessage?.text?.trim() ||
        result.statusMessage?.text?.trim() ||
        "";

      if (result.stateMetrics) {
        setCurrentDynamics(result.stateMetrics);

        if (targetReply) {
          const timelineItem: StateTimelineItem = {
            turnIndex,
            metrics: result.stateMetrics,
            rhythmLabel: result.rhythmLabel,
            atmosphereLabel: result.atmosphereLabel,
            recommendedNextMove: result.recommendedNextMove,
            controlSuggestions: result.controlSuggestions,
            userMessage: trimmedText,
            targetReply,
          };

          setStateTimeline((current) => {
            /*
             * 正常情况下不会出现重复 turnIndex。
             * 开发环境中用户重试或 React 状态回放时，
             * 先移除同轮记录可以避免报告收到重复数据。
             */
            const withoutSameTurn = current.filter(
              (item) => item.turnIndex !== turnIndex,
            );

            return [...withoutSameTurn, timelineItem].sort(
              (left, right) => left.turnIndex - right.turnIndex,
            );
          });
        }
      }
    } catch (error) {
      console.error(error);

      /*
       * 请求失败时移除刚才乐观插入的用户消息，
       * 避免页面显示一条后端从未处理的内容。
       */
      setMessages((current) =>
        current.filter((message) => message.id !== userMessage.id),
      );

      showToast(
        error instanceof Error ? error.message : "AI 回复失败，请稍后重试。",
      );
    } finally {
      setMessageLoading(false);
    }
  };

  const finishSimulation = async () => {
    if (reportLoading || messageLoading || !persona) {
      return;
    }

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
        stateTimeline,
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
      await navigator.clipboard.writeText(report.rewrite);
      showToast("已复制优化表达。");
    } catch {
      showToast("复制失败，可以直接选中文本复制。");
    }
  };

  const resetChat = () => {
    setMessages([]);
    setReport(null);
    setRetryDraft("");
    setConversationEnded(false);
    clearDynamicsState();

    /*
     * 保留当前 Persona，但创建新的模拟会话。
     */
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
        <MobileHeader currentStep={step} onBack={() => goToStep(step - 1)} />

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
              setForm((current) => ({
                ...current,
                ...patch,
              }))
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
    <nav className="bottom-nav" aria-label="移动端流程导航">
      {items.map((item) => {
        const Icon = item.icon;
        const targetStep = item.step;
        const locked = targetStep > maxUnlockedStep;

        return (
          <button
            className={`bottom-nav-item${
              currentStep === targetStep ? " is-active" : ""
            }${locked ? " is-locked" : ""}`}
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
