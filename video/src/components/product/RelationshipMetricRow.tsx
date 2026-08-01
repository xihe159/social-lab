import {COLORS, RADII, TYPOGRAPHY} from "../../design/tokens";

export type RelationshipMetricRowProps = {
  label: string;
  displayValue: string;
  fillPercent: number;
  progress?: number;
};

export const RelationshipMetricRow = ({
  label,
  displayValue,
  fillPercent,
  progress = 1,
}: RelationshipMetricRowProps) => {
  const safeProgress = Math.max(0, Math.min(1, progress));
  const safeFill = Math.max(0, Math.min(100, fillPercent));

  return (
    <div
      style={{
        display: "grid",
        gap: 10,
        opacity: safeProgress,
        transform: `translateY(${10 * (1 - safeProgress)}px)`,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span
          style={{
            color: COLORS.textSecondary,
            fontSize: 16,
            fontWeight: TYPOGRAPHY.weight.medium,
          }}
        >
          {label}
        </span>
        <strong
          style={{
            color: COLORS.brand,
            fontSize: 19,
            fontWeight: TYPOGRAPHY.weight.extraBold,
          }}
        >
          {displayValue}
        </strong>
      </div>
      <div
        style={{
          width: "100%",
          height: 9,
          overflow: "hidden",
          borderRadius: RADII.pill,
          backgroundColor: COLORS.border,
        }}
      >
        <div
          style={{
            width: `${safeFill * safeProgress}%`,
            height: "100%",
            borderRadius: RADII.pill,
            backgroundColor: COLORS.cta,
          }}
        />
      </div>
    </div>
  );
};
