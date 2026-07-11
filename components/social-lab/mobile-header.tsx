import { ArrowLeft, UserRound } from "lucide-react";
import { stepLabels } from "@/lib/social-lab-data";

type MobileHeaderProps = {
  currentStep: number;
  onBack: () => void;
  onAccountClick: () => void;
  accountLabel: string;
  isSignedIn: boolean;
};

export function MobileHeader({
  currentStep,
  onBack,
  onAccountClick,
  accountLabel,
  isSignedIn,
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
        className="icon-button account-button"
        onClick={onAccountClick}
        aria-label="查看本机记录"
        title="查看本机记录"
        type="button"
      >
        {isSignedIn ? (
          <span className="account-initial">{accountLabel}</span>
        ) : (
          <UserRound size={20} />
        )}
      </button>
    </header>
  );
}
