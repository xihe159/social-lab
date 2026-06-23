import { stepDescriptions, stepLabels } from "@/lib/social-lab-data";

type SidebarProps = {
  currentStep: number;
  isOpen: boolean;
  onStepChange: (step: number) => void;
};

export function Sidebar({
  currentStep,
  isOpen,
  onStepChange,
}: SidebarProps) {
  return (
    <aside
      className={`sidebar${isOpen ? " is-open" : ""}`}
      aria-label="Social Lab workspace"
    >
      <div className="brand-block">
        <div className="brand-mark" aria-hidden="true">
          SL
        </div>
        <div>
          <strong>Social Lab</strong>
          <span>先演练，再开口</span>
        </div>
      </div>

      <nav className="step-list" aria-label="流程进度">
        {stepLabels.map((label, index) => (
          <button
            className={`step-item${currentStep === index ? " is-active" : ""}`}
            key={label}
            onClick={() => onStepChange(index)}
            type="button"
          >
            <span>{index + 1}</span>
            <b>{label}</b>
            <small>{stepDescriptions[index]}</small>
          </button>
        ))}
      </nav>

      <div className="side-note">
        <b>隐私提醒</b>
        <p>
          请勿上传身份证号、手机号、住址、银行卡号等敏感信息。模拟结果仅供沟通演练参考。
        </p>
      </div>
    </aside>
  );
}
