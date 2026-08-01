import {COLORS, SHADOWS, TYPOGRAPHY} from "../../design/tokens";

export type MessageBubbleProps = {
  role: "user" | "target";
  text: string;
  revealProgress?: number;
  maxWidth?: number | string;
  compact?: boolean;
};

export const MessageBubble = ({
  role,
  text,
  revealProgress = 1,
  maxWidth = "82%",
  compact = false,
}: MessageBubbleProps) => {
  const reveal = Math.max(0, Math.min(1, revealProgress));
  const isUser = role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        width: "100%",
        opacity: reveal,
        transform: `translateY(${10 * (1 - reveal)}px)`,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div
        style={{
          maxWidth,
          boxSizing: "border-box",
          padding: compact ? "13px 16px" : "17px 20px",
          borderRadius: isUser ? "18px 18px 6px 18px" : "18px 18px 18px 6px",
          backgroundColor: isUser ? COLORS.lime : COLORS.lavenderSurface,
          color: isUser ? COLORS.limeText : COLORS.textPrimary,
          boxShadow: SHADOWS.card,
          fontSize: compact ? 15 : 19,
          fontWeight: TYPOGRAPHY.weight.medium,
          lineHeight: compact ? 1.55 : 1.7,
        }}
      >
        {text}
      </div>
    </div>
  );
};
