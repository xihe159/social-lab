import {COLORS, RADII, SHADOWS, TYPOGRAPHY} from "../../design/tokens";

export type MetricDeltaCardProps = {
  label: string;
  value: number;
  delta: number;
  barPercent: number;
  revealProgress?: number;
};

export const MetricDeltaCard = ({
  label,
  value,
  delta,
  barPercent,
  revealProgress = 1,
}: MetricDeltaCardProps) => {
  const reveal = Math.max(0, Math.min(1, revealProgress));
  const safeBar = Math.max(0, Math.min(100, barPercent));
  const deltaText = delta > 0 ? `+${delta}` : `${delta}`;

  return (
    <div
      style={{
        boxSizing: "border-box",
        padding: "18px 20px",
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
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
          gap: 12,
        }}
      >
        <span
          style={{
            color: COLORS.textSecondary,
            fontSize: 15,
            fontWeight: TYPOGRAPHY.weight.bold,
          }}
        >
          {label}
        </span>
        <div style={{display: "flex", alignItems: "baseline", gap: 8}}>
          <strong
            style={{
              color: COLORS.brand,
              fontSize: 32,
              fontWeight: TYPOGRAPHY.weight.extraBold,
            }}
          >
            {value}
          </strong>
          <span
            style={{
              color: COLORS.cta,
              fontSize: 15,
              fontWeight: TYPOGRAPHY.weight.extraBold,
            }}
          >
            {deltaText}
          </span>
        </div>
      </div>
      <div
        style={{
          width: "100%",
          height: 8,
          marginTop: 14,
          overflow: "hidden",
          borderRadius: RADII.pill,
          backgroundColor: COLORS.border,
        }}
      >
        <div
          style={{
            width: `${safeBar}%`,
            height: "100%",
            borderRadius: RADII.pill,
            backgroundColor: COLORS.cta,
          }}
        />
      </div>
    </div>
  );
};
