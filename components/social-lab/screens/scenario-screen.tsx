import { ArrowRight } from "lucide-react";
import { scenarioKeys, scenarioPresets } from "@/lib/social-lab-data";
import type { FormData, ScenarioKey } from "@/lib/social-lab-types";

type ScenarioScreenProps = {
  scenario: ScenarioKey;
  form: FormData;
  onScenarioChange: (scenario: ScenarioKey) => void;
  onFormChange: (patch: Partial<FormData>) => void;
  onContinue: () => void;
};

export function ScenarioScreen({
  scenario,
  form,
  onScenarioChange,
  onFormChange,
  onContinue,
}: ScenarioScreenProps) {
  return (
    <section className="screen scenario-screen is-current">
      <div className="screen-heading">
        <span>Step 1 / 5 - 场景</span>
        <h2>这次你想预演什么沟通？</h2>
      </div>

      <div className="scenario-grid">
        {scenarioKeys.map((key) => {
          const preset = scenarioPresets[key];
          return (
            <label className="choice-card" key={key}>
              <input
                type="radio"
                name="scenario"
                checked={scenario === key}
                onChange={() => onScenarioChange(key)}
              />
              <span>
                <b>{preset.label}</b>
                <small>{preset.summary}</small>
              </span>
            </label>
          );
        })}
      </div>

      <div className="form-stack">
        <label>
          <span>你的沟通目标是什么？</span>
          <input
            value={form.goal}
            onChange={(event) => onFormChange({ goal: event.target.value })}
          />
        </label>
        <label>
          <span>期望结果，可选</span>
          <input
            value={form.outcome}
            onChange={(event) => onFormChange({ outcome: event.target.value })}
          />
        </label>
      </div>

      <p className="helper-text">
        目标太短也可以继续，但补充更多背景会让模拟更准确。
      </p>
      <div className="footer-actions">
        <button className="primary-action" onClick={onContinue} type="button">
          继续创建人物 <ArrowRight size={18} />
        </button>
      </div>
    </section>
  );
}
