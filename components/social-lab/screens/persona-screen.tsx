import { MessageCircle, SlidersHorizontal } from "lucide-react";
import type { CSSProperties } from "react";
import { stateLabels } from "@/lib/social-lab-data";
import type { ChatRecordAnalysis } from "@/lib/social-lab-api";
import type { Persona, RelationshipState } from "@/lib/social-lab-types";

type PersonaScreenProps = {
  persona: Persona;
  chatAnalysis?: ChatRecordAnalysis | null;
  onStart: () => void;
  onTune: () => void;
};

export function PersonaScreen({
  persona,
  chatAnalysis,
  onStart,
  onTune,
}: PersonaScreenProps) {
  return (
    <section className="screen persona-screen is-current">
      <div className="screen-heading">
        <h2>{persona.title}</h2>
        <p>AI 将根据这个画像扮演对方。你在下一步中扮演自己，主动输入你想说的话。</p>
      </div>

      <div className="dashboard-grid">
        <article className="card-block persona-card">
          <div className="card-header">
            <span>Persona Card</span>
            <button className="text-button" onClick={onTune} type="button">
              <SlidersHorizontal size={15} /> 微调画像
            </button>
          </div>
          <div className="trait-grid">
            <div>
              <small>沟通风格</small>
              <b>{persona.style}</b>
            </div>
            <div>
              <small>回复速度</small>
              <b>{persona.speed}</b>
            </div>
            <div>
              <small>关注重点</small>
              <b>{persona.focus}</b>
            </div>
            <div className="risk-tile">
              <small>风险点</small>
              <b>{persona.risk}</b>
            </div>
          </div>
        </article>

        <article className="card-block">
          <div className="card-header">
            <span>Relationship State</span>
            <small>模拟参数</small>
          </div>
          <div className="state-list">
            {stateLabels.map(([key, label, description]) => (
              <StateRow
                key={key}
                stateKey={key}
                label={label}
                description={description}
                value={persona.state[key]}
              />
            ))}
          </div>
        </article>
      </div>

      <div className="strategy-box">
        <b>推荐策略</b>
        <p>{persona.strategy}</p>
      </div>

      {chatAnalysis && (
        <article className="card-block chat-analysis-card">
          <div className="card-header">
            <span>真实聊天记录分析</span>
            <small>置信度 {Math.round(chatAnalysis.confidence * 100)}%</small>
          </div>
          <div className="chat-analysis-grid">
            <div>
              <small>沟通风格</small>
              <b>
                {replyLengthLabel(chatAnalysis.communication_style.average_reply_length)} ·
                {chatAnalysis.communication_style.formality >= 0.65 ? "偏正式" : "偏自然"} ·
                {chatAnalysis.communication_style.question_frequency >= 0.5 ? "常用提问" : "较少提问"}
              </b>
            </div>
            <div>
              <small>关系特征</small>
              <ul>
                {chatAnalysis.relationship_characteristics.summary.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
          <div className="behavior-patterns">
            <small>识别到的行为模式</small>
            <div>
              {chatAnalysis.behavior_patterns.map((pattern) => (
                <span key={pattern.pattern_id}>
                  {patternLabel(pattern.inferred_tendency)} · {Math.round(pattern.confidence * 100)}%
                </span>
              ))}
            </div>
          </div>
          {chatAnalysis.uncertainty_notes.length > 0 && (
            <p className="analysis-note">{chatAnalysis.uncertainty_notes[0]}</p>
          )}
        </article>
      )}

      <div className="footer-actions">
        <button className="primary-action" onClick={onStart} type="button">
          开始模拟 <MessageCircle size={18} />
        </button>
      </div>
    </section>
  );
}

function replyLengthLabel(value: "short" | "medium" | "long") {
  return { short: "回复简短", medium: "回复适中", long: "回复较详细" }[value];
}

function patternLabel(value: string) {
  const labels: Record<string, string> = {
    responds_briefly: "倾向简短回应",
    responds_with_detail: "倾向详细回应",
    uses_questions: "习惯通过提问确认",
    rarely_asks_questions: "较少主动追问",
    sends_multiple_messages: "习惯连续发送",
    sends_single_message: "习惯单条回复",
  };
  if (labels[value]) return labels[value];
  return value
    .replace(/^when_/, "当 ")
    .replace(/_tends_to_/, " 时倾向 ")
    .replaceAll("_", " ");
}

function StateRow({
  stateKey,
  label,
  description,
  value,
}: {
  stateKey: keyof RelationshipState;
  label: string;
  description: string;
  value: number;
}) {
  const normalized =
    stateKey === "emotional" ? Math.max(0, value + 50) : value;
  const readable =
    stateKey === "emotional" && value >= 0 ? `+${value}` : value;

  return (
    <div className="state-row">
      <div className="state-row-header">
        <span>{label}</span>
        <span>{readable}</span>
      </div>
      <small>{description}</small>
      <div className="meter">
        <span
          style={{ "--value": `${normalized}%` } as CSSProperties}
        />
      </div>
    </div>
  );
}
