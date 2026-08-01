import type {ReactNode} from "react";

import {COLORS, RADII, SHADOWS, TYPOGRAPHY} from "../../design/tokens";

export type ReportHeroProps = {
  score: ReactNode;
  resultLabel: string;
  confidence: string;
  rangeText: string;
  summary: string;
  likelyOutcome: string;
  revealProgress?: number;
};

export const ReportHero = ({
  score,
  resultLabel,
  confidence,
  rangeText,
  summary,
  likelyOutcome,
  revealProgress = 1,
}: ReportHeroProps) => {
  const reveal = Math.max(0, Math.min(1, revealProgress));

  return (
    <section
      style={{
        display: "grid",
        gridTemplateColumns: "0.8fr 1.2fr",
        gap: 34,
        boxSizing: "border-box",
        padding: "34px 38px",
        borderRadius: RADII.card,
        border: `1px solid ${COLORS.border}`,
        background: `linear-gradient(135deg, ${COLORS.lavenderSurface}, ${COLORS.limeSoft})`,
        boxShadow: SHADOWS.floating,
        opacity: reveal,
        transform: `translateY(${18 * (1 - reveal)}px) scale(${0.99 + reveal * 0.01})`,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div>
        <div
          style={{
            color: COLORS.textSecondary,
            fontSize: 16,
            fontWeight: TYPOGRAPHY.weight.bold,
          }}
        >
          本轮结果
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 10,
            marginTop: 14,
          }}
        >
          <strong
            style={{
              color: COLORS.brand,
              fontSize: 108,
              fontWeight: TYPOGRAPHY.weight.extraBold,
              lineHeight: 0.95,
              letterSpacing: "-0.05em",
            }}
          >
            {score}
          </strong>
          <span
            style={{
              color: COLORS.textSecondary,
              fontSize: 23,
              fontWeight: TYPOGRAPHY.weight.bold,
            }}
          >
            /100
          </span>
        </div>
        <div
          style={{
            display: "inline-flex",
            marginTop: 22,
            padding: "8px 14px",
            borderRadius: RADII.pill,
            backgroundColor: COLORS.surface,
            color: COLORS.brand,
            fontSize: 16,
            fontWeight: TYPOGRAPHY.weight.extraBold,
          }}
        >
          {resultLabel}
        </div>
      </div>

      <div style={{display: "grid", alignContent: "center", gap: 18}}>
        <div style={{display: "flex", gap: 10, flexWrap: "wrap"}}>
          <span
            style={{
              padding: "8px 12px",
              borderRadius: RADII.pill,
              backgroundColor: COLORS.surface,
              color: COLORS.textSecondary,
              fontSize: 14,
              fontWeight: TYPOGRAPHY.weight.bold,
            }}
          >
            置信度：{confidence}
          </span>
          <span
            style={{
              padding: "8px 12px",
              borderRadius: RADII.pill,
              backgroundColor: COLORS.surface,
              color: COLORS.textSecondary,
              fontSize: 14,
              fontWeight: TYPOGRAPHY.weight.bold,
            }}
          >
            预测波动范围：{rangeText}
          </span>
        </div>
        <p
          style={{
            margin: 0,
            color: COLORS.textPrimary,
            fontSize: 21,
            fontWeight: TYPOGRAPHY.weight.semibold,
            lineHeight: 1.65,
          }}
        >
          {summary}
        </p>
        <div
          style={{
            paddingTop: 16,
            borderTop: `1px solid rgba(47,47,99,0.12)`,
          }}
        >
          <div
            style={{
              color: COLORS.textSecondary,
              fontSize: 14,
              fontWeight: TYPOGRAPHY.weight.bold,
            }}
          >
            最可能结果
          </div>
          <div
            style={{
              marginTop: 7,
              color: COLORS.textPrimary,
              fontSize: 18,
              fontWeight: TYPOGRAPHY.weight.bold,
              lineHeight: 1.55,
            }}
          >
            {likelyOutcome}
          </div>
        </div>
      </div>
    </section>
  );
};
