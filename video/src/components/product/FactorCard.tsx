import {ArrowDownRight, ArrowUpRight} from "lucide-react";

import {COLORS, RADII, SHADOWS, TYPOGRAPHY} from "../../design/tokens";

export type FactorCardProps = {
  direction: "positive" | "negative";
  title: string;
  impact: string;
  revealProgress?: number;
};

export const FactorCard = ({
  direction,
  title,
  impact,
  revealProgress = 1,
}: FactorCardProps) => {
  const reveal = Math.max(0, Math.min(1, revealProgress));
  const positive = direction === "positive";
  const Icon = positive ? ArrowUpRight : ArrowDownRight;

  return (
    <div
      style={{
        minHeight: 150,
        boxSizing: "border-box",
        padding: "22px 22px",
        borderRadius: RADII.card,
        border: `1px solid ${COLORS.border}`,
        backgroundColor: COLORS.surface,
        boxShadow: SHADOWS.card,
        opacity: reveal,
        transform: `translateY(${16 * (1 - reveal)}px)`,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 7,
          padding: "7px 10px",
          borderRadius: RADII.pill,
          backgroundColor: positive ? COLORS.limeSoft : COLORS.riskSoft,
          color: positive ? COLORS.optionSelectedText : COLORS.textSecondary,
          fontSize: 14,
          fontWeight: TYPOGRAPHY.weight.extraBold,
        }}
      >
        <Icon size={16} strokeWidth={2.4} />
        {positive ? "有利" : "阻碍"}
      </div>
      <div
        style={{
          marginTop: 19,
          color: COLORS.textPrimary,
          fontSize: 21,
          fontWeight: TYPOGRAPHY.weight.extraBold,
          lineHeight: 1.4,
        }}
      >
        {title}
      </div>
      <div
        style={{
          marginTop: 8,
          color: COLORS.textSecondary,
          fontSize: 15,
          fontWeight: TYPOGRAPHY.weight.medium,
        }}
      >
        {impact}
      </div>
    </div>
  );
};
