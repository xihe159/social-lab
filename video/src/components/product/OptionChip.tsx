import {Check} from "lucide-react";
import {interpolateColors} from "remotion";

import {
  COLORS,
  RADII,
  TYPOGRAPHY,
} from "../../design/tokens";

export type OptionChipProps = {
  label: string;
  selectedProgress?: number;
  pressedProgress?: number;
  revealProgress?: number;
};

const clamp01 = (value: number): number => {
  return Math.max(0, Math.min(1, value));
};

export const OptionChip = ({
  label,
  selectedProgress = 0,
  pressedProgress = 0,
  revealProgress = 1,
}: OptionChipProps) => {
  const selected = clamp01(selectedProgress);
  const pressed = clamp01(pressedProgress);
  const reveal = clamp01(revealProgress);

  const backgroundColor = interpolateColors(
    selected,
    [0, 1],
    [COLORS.surface, COLORS.optionSelected],
  );

  const borderColor = interpolateColors(
    selected,
    [0, 1],
    [COLORS.borderStrong, COLORS.optionSelectedBorder],
  );

  const textColor = interpolateColors(
    selected,
    [0, 1],
    [COLORS.textSecondary, COLORS.optionSelectedText],
  );

  const scale =
    0.985 +
    reveal * 0.015 -
    pressed * 0.018;

  return (
    <div
      style={{
        minHeight: 42,
        boxSizing: "border-box",
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "0 18px",
        border: `1px solid ${borderColor}`,
        borderRadius: RADII.pill,
        backgroundColor,
        color: textColor,
        fontFamily: TYPOGRAPHY.fontFamily,
        fontSize: 17,
        fontWeight: TYPOGRAPHY.weight.semibold,
        whiteSpace: "nowrap",
        opacity: reveal,
        transform:
          `translateY(${8 * (1 - reveal)}px) scale(${scale})`,
        transformOrigin: "center",
        boxShadow:
          selected > 0
            ? `0 7px 18px rgba(79, 183, 126, ${0.1 * selected})`
            : "none",
        willChange: "transform, opacity",
      }}
    >
      <span>{label}</span>

      <Check
        size={17}
        strokeWidth={2.6}
        style={{
          opacity: selected,
          transform: `scale(${0.7 + selected * 0.3})`,
        }}
      />
    </div>
  );
};