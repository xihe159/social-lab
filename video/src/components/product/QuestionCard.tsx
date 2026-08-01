import type {ReactNode} from "react";
import {Check} from "lucide-react";
import {interpolateColors} from "remotion";

import {
  COLORS,
  RADII,
  SHADOWS,
  TYPOGRAPHY,
} from "../../design/tokens";

export type QuestionCardProps = {
  number: number;
  title: string;
  description?: string;
  children: ReactNode;

  revealProgress?: number;
  completionProgress?: number;
};

const clamp01 = (value: number): number => {
  return Math.max(0, Math.min(1, value));
};

export const QuestionCard = ({
  number,
  title,
  description,
  children,
  revealProgress = 1,
  completionProgress = 0,
}: QuestionCardProps) => {
  const reveal = clamp01(revealProgress);
  const complete = clamp01(completionProgress);

  const numberBackground = interpolateColors(
    complete,
    [0, 1],
    [COLORS.lavender, COLORS.optionSelectedBorder],
  );

  const numberColor = interpolateColors(
    complete,
    [0, 1],
    [COLORS.brand, COLORS.surface],
  );

  return (
    <section
      style={{
        position: "relative",
        boxSizing: "border-box",
        padding: "26px 28px",
        border: `1px solid ${COLORS.formWarmBorder}`,
        borderRadius: RADII.card,
        backgroundColor: "rgba(255, 255, 253, 0.92)",
        boxShadow: SHADOWS.card,
        opacity: reveal,
        transform:
          `translateY(${18 * (1 - reveal)}px) ` +
          `scale(${0.992 + reveal * 0.008})`,
        transformOrigin: "center",
        willChange: "transform, opacity",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: 18,
        }}
      >
        <div
          style={{
            position: "relative",
            width: 42,
            height: 42,
            flex: "0 0 auto",
            display: "grid",
            placeItems: "center",
            borderRadius: "50%",
            backgroundColor: numberBackground,
            color: numberColor,
            fontFamily: TYPOGRAPHY.fontFamily,
            fontSize: 17,
            fontWeight: TYPOGRAPHY.weight.extraBold,
          }}
        >
          <span
            style={{
              opacity: 1 - complete,
            }}
          >
            {number}
          </span>

          <Check
            size={21}
            strokeWidth={2.8}
            style={{
              position: "absolute",
              opacity: complete,
              transform: `scale(${0.65 + complete * 0.35})`,
            }}
          />
        </div>

        <div
          style={{
            flex: 1,
            minWidth: 0,
          }}
        >
          <h3
            style={{
              margin: 0,
              color: COLORS.textPrimary,
              fontFamily: TYPOGRAPHY.fontFamily,
              fontSize: 24,
              fontWeight: TYPOGRAPHY.weight.extraBold,
              lineHeight: 1.3,
              letterSpacing: "-0.015em",
            }}
          >
            {title}
          </h3>

          {description ? (
            <p
              style={{
                margin: "8px 0 0",
                color: COLORS.textSecondary,
                fontFamily: TYPOGRAPHY.fontFamily,
                fontSize: 16,
                fontWeight: TYPOGRAPHY.weight.regular,
                lineHeight: 1.6,
              }}
            >
              {description}
            </p>
          ) : null}

          <div
            style={{
              marginTop: 22,
            }}
          >
            {children}
          </div>
        </div>
      </div>
    </section>
  );
};
