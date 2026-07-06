import {
  ArrowRight,
  BriefcaseBusiness,
  GraduationCap,
  HandHeart,
  Sparkles,
  X,
} from "lucide-react";
import { useState } from "react";
import type { CSSProperties } from "react";
import { scenarioKeys, scenarioPresets } from "@/lib/social-lab-data";
import type { ScenarioKey } from "@/lib/social-lab-types";

type LandingScreenProps = {
  onPresetSelect: (scenario: ScenarioKey) => void;
};

const compactScenarioCopy: Record<ScenarioKey, { label: string; summary: string }> = {
  advisor: {
    label: "导师",
    summary: "推荐信 / 催回复",
  },
  work: {
    label: "职场",
    summary: "加薪 / 汇报",
  },
  social: {
    label: "社交",
    summary: "道歉 / 拒绝",
  },
};

export function LandingScreen({
  onPresetSelect,
}: LandingScreenProps) {
  const [pickerOpen, setPickerOpen] = useState(false);

  const selectFromPicker = (nextScenario: ScenarioKey) => {
    setPickerOpen(false);
    onPresetSelect(nextScenario);
  };

  return (
    <section className="screen landing-screen is-current">
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
            <button
              className="primary-action"
              onClick={() => setPickerOpen(true)}
              type="button"
            >
              开始模拟 <ArrowRight size={18} />
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
          const preset = compactScenarioCopy[key];
          return (
            <button
              className="scenario-card"
              key={key}
              onClick={() => onPresetSelect(key)}
              type="button"
            >
              <ScenarioIcon scenario={key} />
              <b>{preset.label}</b>
              <span>{preset.summary}</span>
            </button>
          );
        })}
      </div>
      {pickerOpen && (
        <div className="scenario-modal" role="dialog" aria-modal="true">
          <div
            className="scenario-modal-backdrop"
            onClick={() => setPickerOpen(false)}
          />
          <div className="scenario-modal-card">
            <div className="scenario-modal-title">选择你的沟通场景</div>
            <div className="scenario-modal-grid">
              {scenarioKeys.map((key) => {
                const preset = scenarioPresets[key];
                const compactPreset = compactScenarioCopy[key];
                return (
                  <button
                    className="scenario-modal-option"
                    key={key}
                    onClick={() => selectFromPicker(key)}
                    type="button"
                  >
                    <ScenarioIcon scenario={key} />
                    <b>{compactPreset.label}</b>
                    <span>{preset.summary}</span>
                  </button>
                );
              })}
            </div>
            <p>后续问题会根据你的选择自动调整</p>
          </div>
          <button
            className="scenario-modal-close"
            onClick={() => setPickerOpen(false)}
            aria-label="关闭场景选择"
            type="button"
          >
            <X size={24} />
          </button>
        </div>
      )}
    </section>
  );
}

function ScenarioIcon({ scenario }: { scenario: ScenarioKey }) {
  const icon =
    scenario === "advisor" ? (
      <GraduationCap size={24} />
    ) : scenario === "work" ? (
      <BriefcaseBusiness size={24} />
    ) : (
      <HandHeart size={24} />
    );

  return <span className={`scenario-icon is-${scenario}`}>{icon}</span>;
}
