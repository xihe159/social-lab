import { ArrowRight } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { FormData, ScenarioKey } from "@/lib/social-lab-types";

type ScenarioScreenProps = {
  scenario: ScenarioKey;
  form: FormData;
  onFormChange: (patch: Partial<FormData>) => void;
  onContinue: (patch: Partial<FormData>) => void;
};

type ScenarioDraft = {
  task: string;
  urgency: string;
  outcome: string;
  concerns: string[];
  concernNote: string;
};

type ScenarioCopy = {
  title: string;
  subtitle: string;
  taskQuestion: string;
  taskOptions: string[];
  taskPlaceholder: string;
  urgencyQuestion: string;
  urgencyHint: string;
  urgencyOptions: string[];
  outcomeQuestion: string;
  outcomePlaceholder: string;
  concernQuestion: string;
  concernOptions: string[];
  concernPlaceholder: string;
  cta: string;
};

const scenarioCopy: Record<ScenarioKey, ScenarioCopy> = {
  advisor: {
    title: "这次你想解决什么沟通问题？",
    subtitle: "先描述这次沟通任务，下一步再补充对方是谁。",
    taskQuestion: "这次你想沟通什么？",
    taskOptions: [
      "申请推荐信",
      "催回复",
      "申请延期",
      "预约沟通",
      "询问项目机会",
      "请求修改材料",
      "其他",
    ],
    taskPlaceholder: "例如：我想请导师帮我写推荐信",
    urgencyQuestion: "这件事有多紧急？",
    urgencyHint: "单选 · 可跳过",
    urgencyOptions: [
      "不着急，只是提前沟通",
      "一周内需要回复",
      "三天内需要回复",
      "今天或明天就需要回复",
      "不确定",
    ],
    outcomeQuestion: "你希望这次沟通达到什么结果？",
    outcomePlaceholder: "例如：希望导师愿意帮我写推荐信，并且不要觉得我太唐突。",
    concernQuestion: "你最担心哪里出问题？",
    concernOptions: [
      "担心对方觉得我在抱怨",
      "担心显得不够配合",
      "担心请求被拒绝",
      "担心被施加更多压力",
      "担心影响之后评价",
      "担心对方不认真听",
    ],
    concernPlaceholder: "例如：我怕自己表达太直接，让对方觉得有压力",
    cta: "继续补充对方信息",
  },
  work: {
    title: "这次你想解决什么沟通问题？",
    subtitle: "先描述这次沟通任务，下一步再补充对方是谁。",
    taskQuestion: "这次你想沟通什么？",
    taskOptions: [
      "谈加薪",
      "拒绝额外工作",
      "向领导汇报",
      "沟通绩效反馈",
      "协调工作边界",
      "提出资源或支持需求",
      "其他",
    ],
    taskPlaceholder: "例如：我想和领导沟通加薪和工作边界",
    urgencyQuestion: "这件事有多紧急？",
    urgencyHint: "单选 · 可跳过",
    urgencyOptions: [
      "不着急，只是提前沟通",
      "一周内需要回复",
      "三天内需要回复",
      "今天或明天就需要回复",
      "不确定",
    ],
    outcomeQuestion: "你希望这次沟通达到什么结果？",
    outcomePlaceholder: "例如：希望领导认可我的贡献，并给出明确下一步。",
    concernQuestion: "你最担心哪里出问题？",
    concernOptions: [
      "担心对方觉得我在抱怨",
      "担心显得不够配合",
      "担心请求被拒绝",
      "担心被施加更多压力",
      "担心影响之后评价",
      "担心对方不认真听",
    ],
    concernPlaceholder: "例如：我怕自己表达太直接，让对方觉得有压力",
    cta: "继续补充对方信息",
  },
  social: {
    title: "这次你想解决什么沟通问题？",
    subtitle: "先描述这次沟通任务，下一步再补充对方是谁。",
    taskQuestion: "这次你想沟通什么？",
    taskOptions: [
      "道歉",
      "拒绝请求",
      "解释误会",
      "表达边界",
      "处理冲突",
      "修复关系",
      "其他",
    ],
    taskPlaceholder: "例如：我想拒绝朋友的请求，但不想让关系变僵",
    urgencyQuestion: "这件事现在有多敏感？",
    urgencyHint: "单选 · 可跳过",
    urgencyOptions: [
      "不太敏感",
      "有点尴尬",
      "对方可能受伤",
      "已经出现冲突",
      "不确定",
    ],
    outcomeQuestion: "你希望这次沟通达到什么结果？",
    outcomePlaceholder: "例如：希望清楚表达边界，同时让对方感到被尊重。",
    concernQuestion: "你最担心哪里出问题？",
    concernOptions: [
      "担心对方误解我的意思",
      "担心显得太冷淡",
      "担心引发争吵",
      "担心关系变尴尬",
      "担心自己心软答应",
      "担心说不清楚边界",
    ],
    concernPlaceholder: "例如：我怕拒绝后对方觉得我不重视这段关系",
    cta: "继续补充对方信息",
  },
};

export function ScenarioScreen({
  scenario,
  form,
  onFormChange,
  onContinue,
}: ScenarioScreenProps) {
  const copy = scenarioCopy[scenario];
  const [draft, setDraft] = useState<ScenarioDraft>({
    task: form.goal,
    urgency: "",
    outcome: form.outcome,
    concerns: [],
    concernNote: "",
  });

  useEffect(() => {
    setDraft({
      task: "",
      urgency: "",
      outcome: "",
      concerns: [],
      concernNote: "",
    });
  }, [scenario]);

  const composedPatch = useMemo<Partial<FormData>>(() => {
    const concernText = [...draft.concerns, draft.concernNote]
      .filter(Boolean)
      .join("；");
    const outcomeParts = [
      draft.urgency && `紧急/敏感程度：${draft.urgency}`,
      draft.outcome && `期望结果：${draft.outcome}`,
      concernText && `担心点：${concernText}`,
    ].filter(Boolean);

    return {
      goal: draft.task.trim(),
      outcome: outcomeParts.join("\n"),
    };
  }, [draft]);

  const chooseSingle = (key: "task" | "urgency", value: string) => {
    setDraft((current) => ({ ...current, [key]: value }));
  };

  const toggleConcern = (value: string) => {
    setDraft((current) => {
      const exists = current.concerns.includes(value);
      return {
        ...current,
        concerns: exists
          ? current.concerns.filter((item) => item !== value)
          : [...current.concerns, value],
      };
    });
  };

  return (
    <section className="screen scenario-screen is-current">
      <div className="screen-heading">
        <h2>{copy.title}</h2>
        <p>{copy.subtitle}</p>
      </div>

      <div className="question-stack">
        <QuestionCard
          number={1}
          title={copy.taskQuestion}
          hint="单选 + 自定义 · 可跳过"
          isComplete={Boolean(draft.task.trim())}
        >
          <ChipGroup
            options={copy.taskOptions}
            selected={[draft.task]}
            onSelect={(value) => chooseSingle("task", value)}
          />
          <input
            value={draft.task}
            onChange={(event) => {
              const value = event.target.value;
              setDraft((current) => ({ ...current, task: value }));
              onFormChange({ goal: value });
            }}
            placeholder={copy.taskPlaceholder}
          />
        </QuestionCard>

        <QuestionCard
          number={2}
          title={copy.urgencyQuestion}
          hint={copy.urgencyHint}
          isComplete={Boolean(draft.urgency)}
        >
          <ChipGroup
            options={copy.urgencyOptions}
            selected={[draft.urgency]}
            onSelect={(value) => chooseSingle("urgency", value)}
          />
        </QuestionCard>

        <QuestionCard
          number={3}
          title={copy.outcomeQuestion}
          hint="文本输入，可选 · 可跳过"
          isComplete={Boolean(draft.outcome.trim())}
        >
          <textarea
            value={draft.outcome}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                outcome: event.target.value,
              }))
            }
            placeholder={copy.outcomePlaceholder}
          />
        </QuestionCard>

        <QuestionCard
          number={4}
          title={copy.concernQuestion}
          hint="多选 + 可自定义 · 可跳过"
          isComplete={draft.concerns.length > 0 || Boolean(draft.concernNote.trim())}
        >
          <ChipGroup
            options={copy.concernOptions}
            selected={draft.concerns}
            onSelect={toggleConcern}
          />
          <input
            value={draft.concernNote}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                concernNote: event.target.value,
              }))
            }
            placeholder={copy.concernPlaceholder}
          />
        </QuestionCard>
      </div>

      <div className="footer-actions">
        <button
          className="primary-action"
          onClick={() => onContinue(composedPatch)}
          type="button"
        >
          {copy.cta} <ArrowRight size={18} />
        </button>
      </div>
    </section>
  );
}

function QuestionCard({
  number,
  title,
  hint,
  isComplete,
  children,
}: {
  number: number;
  title: string;
  hint: string;
  isComplete: boolean;
  children: ReactNode;
}) {
  return (
    <article className={`question-card${isComplete ? " is-complete" : ""}`}>
      <div className="question-card-title">
        <span>{number}</span>
        <div>
          <h3>{title}</h3>
          <p>{hint}</p>
        </div>
      </div>
      {children}
    </article>
  );
}

function ChipGroup({
  options,
  selected,
  onSelect,
}: {
  options: string[];
  selected: string[];
  onSelect: (value: string) => void;
}) {
  return (
    <div className="chip-group">
      {options.map((option) => (
        <button
          className={`option-chip${selected.includes(option) ? " is-selected" : ""}`}
          key={option}
          onClick={() => onSelect(option)}
          type="button"
        >
          {option}
        </button>
      ))}
    </div>
  );
}
