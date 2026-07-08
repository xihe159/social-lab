import { MessageCircle, SlidersHorizontal } from "lucide-react";
import type { CSSProperties } from "react";
import { stateLabels } from "@/lib/social-lab-data";
import type { Persona, RelationshipState } from "@/lib/social-lab-types";

type PersonaScreenProps = {
  persona: Persona;
  onStart: () => void;
  onTune: () => void;
};

export function PersonaScreen({
  persona,
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

      <div className="footer-actions">
        <button className="primary-action" onClick={onStart} type="button">
          开始模拟 <MessageCircle size={18} />
        </button>
      </div>
    </section>
  );
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
