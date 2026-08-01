import {Send} from "lucide-react";

import {BrowserWindow} from "../BrowserWindow";
import {
  COLORS,
  LAYOUT,
  RADII,
  SHADOWS,
  SPACING,
  TYPOGRAPHY,
} from "../../design/tokens";

export type ComposerMockProps = {
  text: string;
  cursorOpacity?: number;
  width?: number;
  showLabel?: boolean;
  label?: string;
};

export const ComposerMock = ({
  text,
  cursorOpacity = 0,
  width = LAYOUT.formWidth,
  showLabel = true,
  label = "一段尚未开始的沟通",
}: ComposerMockProps) => {
  return (
    <BrowserWindow
      showChrome={false}
      width={width}
      contentStyle={{
        padding: "30px 32px 28px",
      }}
    >
      {showLabel ? (
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            minHeight: 34,
            padding: "7px 14px",
            marginBottom: SPACING.lg,
            borderRadius: RADII.pill,
            backgroundColor: COLORS.lavender,
            color: COLORS.brand,
            fontFamily: TYPOGRAPHY.fontFamily,
            fontSize: TYPOGRAPHY.size.label,
            fontWeight: TYPOGRAPHY.weight.bold,
            letterSpacing: "0.01em",
            whiteSpace: "nowrap",
          }}
        >
          {label}
        </div>
      ) : null}

      <div
        style={{
          minHeight: 80,
          boxSizing: "border-box",
          display: "flex",
          alignItems: "center",
          gap: SPACING.md,
          padding: "14px 14px 14px 22px",
          borderRadius: RADII.input,
          border: `1px solid ${COLORS.border}`,
          backgroundColor: COLORS.surface,
          boxShadow: SHADOWS.focus,
        }}
      >
        <div
          style={{
            flex: 1,
            minWidth: 0,
            height: 50,
            display: "flex",
            alignItems: "center",
            overflow: "hidden",
            color: COLORS.textPrimary,
            fontFamily: TYPOGRAPHY.fontFamily,
            fontSize: TYPOGRAPHY.size.bodyLarge,
            fontWeight: TYPOGRAPHY.weight.medium,
            lineHeight: 1,
            whiteSpace: "nowrap",
          }}
        >
          <span>{text}</span>

          <span
            aria-hidden
            style={{
              display: "inline-block",
              width: 2,
              height: 30,
              marginLeft: 5,
              borderRadius: RADII.pill,
              backgroundColor: COLORS.brand,
              opacity: cursorOpacity,
            }}
          />
        </div>

        <div
          aria-label="发送按钮"
          role="img"
          style={{
            flex: "0 0 auto",
            width: 50,
            height: 50,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            borderRadius: RADII.input,
            backgroundColor: COLORS.brand,
            boxShadow: "0 8px 18px rgba(47, 47, 99, 0.20)",
          }}
        >
          <Send
            size={23}
            strokeWidth={2.2}
            color={COLORS.surface}
          />
        </div>
      </div>
    </BrowserWindow>
  );
};

