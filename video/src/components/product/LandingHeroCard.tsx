import {ArrowRight, Sparkles} from "lucide-react";

import {
  COLORS,
  RADII,
  SHADOWS,
  SPACING,
  TYPOGRAPHY,
} from "../../design/tokens";

export type LandingHeroCardProps = {
  cardProgress?: number;
  badgeProgress?: number;
  titleProgress?: number;
  copyProgress?: number;
  buttonProgress?: number;
  buttonBreath?: number;
};

const entranceStyle = (
  progress: number,
  distance = 16,
) => {
  return {
    opacity: progress,
    transform: `translateY(${distance * (1 - progress)}px)`,
  };
};

export const LandingHeroCard = ({
  cardProgress = 1,
  badgeProgress = 1,
  titleProgress = 1,
  copyProgress = 1,
  buttonProgress = 1,
  buttonBreath = 0,
}: LandingHeroCardProps) => {
  const buttonScale = 1 + buttonBreath * 0.008;
  const buttonShadowAlpha = 0.24 + buttonBreath * 0.1;

  return (
    <section
      style={{
        height: "100%",
        boxSizing: "border-box",
        padding: "52px 54px",
        border: `1px solid ${COLORS.border}`,
        borderRadius: 26,
        backgroundColor: COLORS.surface,
        boxShadow: SHADOWS.card,
        opacity: cardProgress,
        transform:
          `translateY(${18 * (1 - cardProgress)}px) ` +
          `scale(${0.99 + cardProgress * 0.01})`,
        willChange: "transform, opacity",
      }}
    >
      <div
        style={{
          ...entranceStyle(badgeProgress, 12),
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          minHeight: 36,
          padding: "8px 12px",
          borderRadius: 16,
          backgroundColor: COLORS.lavenderSurface,
          color: COLORS.brand,
          fontFamily: TYPOGRAPHY.fontFamily,
          fontSize: 16,
          fontWeight: TYPOGRAPHY.weight.extraBold,
          whiteSpace: "nowrap",
          willChange: "transform, opacity",
        }}
      >
        <Sparkles size={18} strokeWidth={2.2} />
        AI 人际沟通预演
      </div>

      <h1
        style={{
          ...entranceStyle(titleProgress, 18),
          margin: "30px 0 20px",
          color: COLORS.textPrimary,
          fontFamily: TYPOGRAPHY.fontFamily,
          fontSize: 70,
          fontWeight: TYPOGRAPHY.weight.extraBold,
          lineHeight: 1.06,
          letterSpacing: "-0.035em",
          willChange: "transform, opacity",
        }}
      >
        先演练，
        <br />
        再开口。
      </h1>

      <p
        style={{
          ...entranceStyle(copyProgress, 16),
          maxWidth: 550,
          margin: 0,
          color: COLORS.textSecondary,
          fontFamily: TYPOGRAPHY.fontFamily,
          fontSize: 22,
          fontWeight: TYPOGRAPHY.weight.regular,
          lineHeight: 1.75,
          willChange: "transform, opacity",
        }}
      >
        在真实沟通前，先和 AI
        生成的关系数字分身练习一遍，预判风险，并获得更稳妥的表达方式。
      </p>

      <div
        style={{
          ...entranceStyle(buttonProgress, 14),
          marginTop: SPACING.xl,
          willChange: "transform, opacity",
        }}
      >
        <div
          style={{
            width: "fit-content",
            minHeight: 56,
            boxSizing: "border-box",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 10,
            padding: "0 27px",
            borderRadius: 16,
            backgroundColor: COLORS.cta,
            color: COLORS.surface,
            boxShadow:
              `0 12px 28px rgba(79, 157, 122, ` +
              `${buttonShadowAlpha})`,
            fontFamily: TYPOGRAPHY.fontFamily,
            fontSize: 19,
            fontWeight: TYPOGRAPHY.weight.extraBold,
            transform: `scale(${buttonScale})`,
            transformOrigin: "center center",
          }}
        >
          开始模拟
          <ArrowRight size={20} strokeWidth={2.4} />
        </div>
      </div>
    </section>
  );
};
