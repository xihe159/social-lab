import type {ReactNode} from "react";

import {COLORS, RADII, TYPOGRAPHY} from "../../design/tokens";

export type AgentNodeProps = {
  title: string;
  subtitle: string;
  progress: number;
  children?: ReactNode;
  tone?: "neutral" | "lavender" | "lime";
};

export const AgentNode = ({
  title,
  subtitle,
  progress,
  children,
  tone = "neutral",
}: AgentNodeProps) => {
  const safe = Math.max(0, Math.min(1, progress));
  const backgroundColor =
    tone === "lime"
      ? COLORS.limeSoft
      : tone === "lavender"
        ? COLORS.lavenderSurface
        : COLORS.surface;

  return (
    <div
      style={{
        position: "relative",
        minHeight: 82,
        boxSizing: "border-box",
        padding: "17px 18px",
        borderRadius: RADII.input,
        border: `1.5px solid ${safe > 0.2 ? COLORS.brand : COLORS.border}`,
        backgroundColor,
        boxShadow:
          safe > 0.2
            ? `0 12px 28px rgba(47, 47, 99, ${0.05 + safe * 0.08})`
            : "none",
        transform: `scale(${1 + safe * 0.01})`,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div
        style={{
          color: COLORS.textPrimary,
          fontSize: 18,
          fontWeight: TYPOGRAPHY.weight.extraBold,
        }}
      >
        {title}
      </div>
      <div
        style={{
          marginTop: 5,
          color: COLORS.textSecondary,
          fontSize: 13,
          fontWeight: TYPOGRAPHY.weight.bold,
        }}
      >
        {subtitle}
      </div>
      {children ? <div style={{marginTop: 11}}>{children}</div> : null}
    </div>
  );
};
