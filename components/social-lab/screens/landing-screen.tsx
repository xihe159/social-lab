import { ArrowRight, Sparkles } from "lucide-react";
import type { CSSProperties } from "react";
import { scenarioKeys, scenarioPresets } from "@/lib/social-lab-data";
import type { ScenarioKey } from "@/lib/social-lab-types";

type LandingScreenProps = {
  onStart: () => void;
  onPresetSelect: (scenario: ScenarioKey) => void;
};

export function LandingScreen({
  onStart,
  onPresetSelect,
}: LandingScreenProps) {
  return (
    <section className="screen is-current">
      <div className="hero-grid">
        <div className="hero-copy">
          <div className="mini-badge">
            <Sparkles size={15} /> AI 人际沟通预演
          </div>
          <h1>
            先演练，
            <br />
            再开口。
          </h1>
          <p>
            在真实沟通前，先和 AI
            生成的关系数字分身练习一遍，预判风险，并获得更稳妥的表达方式。
          </p>
          <div className="hero-actions">
            <button className="primary-action" onClick={onStart} type="button">
              开始模拟 <ArrowRight size={18} />
            </button>
            <button
              className="secondary-action"
              onClick={() => onPresetSelect("advisor")}
              type="button"
            >
              载入导师推荐信示例
            </button>
          </div>
        </div>

        <div className="lab-preview" aria-label="产品流程预览">
          <div className="preview-topline">
            <span>本轮沟通成功率</span>
            <strong>68%</strong>
          </div>
          <div className="preview-chat">
            <p className="bubble user">老师您好，我想请您帮我写推荐信。</p>
            <p className="bubble target">
              你先把申请项目、截止时间和推荐信要求发给我，我看一下是否来得及安排。
            </p>
          </div>
          <div className="mini-chart">
            <span style={{ "--w": "68%", "--c": "#4563f4" } as CSSProperties} />
            <span style={{ "--w": "20%", "--c": "#f0b84f" } as CSSProperties} />
            <span style={{ "--w": "7%", "--c": "#de6b64" } as CSSProperties} />
            <span style={{ "--w": "5%", "--c": "#8fa0b8" } as CSSProperties} />
          </div>
        </div>
      </div>

      <div className="section-title">
        <h2>常见场景</h2>
        <p>选择后会自动带入后续表单。</p>
      </div>
      <div className="scenario-grid compact">
        {scenarioKeys.map((key) => {
          const preset = scenarioPresets[key];
          return (
            <button
              className="scenario-card"
              key={key}
              onClick={() => onPresetSelect(key)}
              type="button"
            >
              <b>{preset.label}</b>
              <span>{preset.summary}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
