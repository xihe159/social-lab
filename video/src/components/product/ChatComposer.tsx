import {Send} from "lucide-react";

import {COLORS, RADII, SHADOWS, TYPOGRAPHY} from "../../design/tokens";

export type ChatComposerProps = {
  text: string;
  cursorOpacity?: number;
  revealProgress?: number;
  sendPressedProgress?: number;
  height?: number;
};

export const ChatComposer = ({
  text,
  cursorOpacity = 0,
  revealProgress = 1,
  sendPressedProgress = 0,
  height = 82,
}: ChatComposerProps) => {
  const reveal = Math.max(0, Math.min(1, revealProgress));
  const pressed = Math.max(0, Math.min(1, sendPressedProgress));

  return (
    <div
      style={{
        height,
        boxSizing: "border-box",
        display: "flex",
        alignItems: "center",
        gap: 14,
        padding: "13px 13px 13px 20px",
        borderRadius: RADII.card,
        border: `1px solid ${COLORS.border}`,
        backgroundColor: COLORS.surface,
        boxShadow: SHADOWS.card,
        opacity: reveal,
        transform: `translateY(${12 * (1 - reveal)}px)`,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div
        style={{
          flex: 1,
          minWidth: 0,
          color: text ? COLORS.textPrimary : COLORS.textMuted,
          fontSize: 17,
          fontWeight: TYPOGRAPHY.weight.medium,
          lineHeight: 1.5,
          overflow: "hidden",
        }}
      >
        <span>{text || "输入你想说的话……"}</span>
        <span
          style={{
            display: "inline-block",
            width: 2,
            height: 22,
            marginLeft: 4,
            verticalAlign: "middle",
            borderRadius: RADII.pill,
            backgroundColor: COLORS.brand,
            opacity: cursorOpacity,
          }}
        />
      </div>
      <div
        style={{
          width: 52,
          height: 52,
          flex: "0 0 auto",
          display: "grid",
          placeItems: "center",
          borderRadius: RADII.input,
          backgroundColor: COLORS.brand,
          color: COLORS.surface,
          transform: `scale(${1 - pressed * 0.06})`,
          boxShadow: "0 8px 18px rgba(47, 47, 99, 0.20)",
        }}
      >
        <Send size={23} strokeWidth={2.2} />
      </div>
    </div>
  );
};
