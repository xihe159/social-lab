import { ArrowLeft, Menu } from "lucide-react";
import { stepLabels } from "@/lib/social-lab-data";

type MobileHeaderProps = {
  currentStep: number;
  onBack: () => void;
  onMenu: () => void;
};

export function MobileHeader({
  currentStep,
  onBack,
  onMenu,
}: MobileHeaderProps) {
  return (
    <header className="mobile-header">
      <button
        className="icon-button"
        onClick={onMenu}
        aria-label="打开流程"
        title="打开流程"
        type="button"
      >
        <Menu size={20} />
      </button>
      <div>
        <strong>Social Lab</strong>
        <span>
          Step {currentStep + 1} / 6 - {stepLabels[currentStep]}
        </span>
      </div>
      <button
        className="icon-button"
        onClick={onBack}
        aria-label="返回上一步"
        title="返回上一步"
        type="button"
      >
        <ArrowLeft size={20} />
      </button>
    </header>
  );
}
