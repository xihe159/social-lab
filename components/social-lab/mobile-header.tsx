import { ArrowLeft, BrainCircuit } from "lucide-react";
import { stepLabels } from "@/lib/social-lab-data";

type MobileHeaderProps = {
  currentStep: number;
  onBack: () => void;
};

export function MobileHeader({
  currentStep,
  onBack,
}: MobileHeaderProps) {
  const stepText =
    currentStep === 0
      ? "先演练，再开口"
      : `Step ${currentStep} / 5 · ${stepLabels[currentStep]}`;

  return (
    <header className="mobile-header">
      <button
        className="icon-button"
        onClick={onBack}
        aria-label="返回上一步"
        title="返回上一步"
        type="button"
      >
        <ArrowLeft size={20} />
      </button>
      <div>
        <strong>Social Lab</strong>
        <span>{stepText}</span>
      </div>
      <button
        className="icon-button"
        aria-label="AI 模拟"
        title="AI 模拟"
        type="button"
      >
        <BrainCircuit size={20} />
      </button>
    </header>
  );
}
