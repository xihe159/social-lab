import type {ReactNode} from "react";

import {COLORS, RADII, SHADOWS, TYPOGRAPHY} from "../../design/tokens";

export type FormFieldMockProps = {
  label: string;
  value: ReactNode;
  placeholder?: string;
  helper?: string;
  multiline?: boolean;
  revealProgress?: number;
  focusProgress?: number;
};

export const FormFieldMock = ({
  label,
  value,
  placeholder,
  helper,
  multiline = false,
  revealProgress = 1,
  focusProgress = 0,
}: FormFieldMockProps) => {
  const reveal = Math.max(0, Math.min(1, revealProgress));
  const focus = Math.max(0, Math.min(1, focusProgress));

  return (
    <div
      style={{
        opacity: reveal,
        transform: `translateY(${14 * (1 - reveal)}px)`,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div
        style={{
          marginBottom: 9,
          color: COLORS.textPrimary,
          fontSize: 17,
          fontWeight: TYPOGRAPHY.weight.bold,
        }}
      >
        {label}
      </div>
      <div
        style={{
          minHeight: multiline ? 106 : 58,
          boxSizing: "border-box",
          padding: multiline ? "16px 18px" : "0 18px",
          display: "flex",
          alignItems: multiline ? "flex-start" : "center",
          borderRadius: RADII.input,
          border: `1px solid ${focus > 0.5 ? COLORS.brand : COLORS.border}`,
          backgroundColor: COLORS.surface,
          boxShadow: focus > 0 ? SHADOWS.focus : "none",
          color: value ? COLORS.textPrimary : COLORS.textMuted,
          fontSize: 18,
          fontWeight: TYPOGRAPHY.weight.medium,
          lineHeight: multiline ? 1.7 : 1.2,
          whiteSpace: "pre-line",
        }}
      >
        {value || placeholder}
      </div>
      {helper ? (
        <div
          style={{
            marginTop: 8,
            color: COLORS.textMuted,
            fontSize: 13,
            lineHeight: 1.5,
          }}
        >
          {helper}
        </div>
      ) : null}
    </div>
  );
};
