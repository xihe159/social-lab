import {COLORS, RADII, TYPOGRAPHY} from "../../design/tokens";

export type PersonaTraitTileProps = {
  label: string;
  value: string;
  revealProgress?: number;
  tone?: "lavender" | "risk";
  span?: number;
};

export const PersonaTraitTile = ({
  label,
  value,
  revealProgress = 1,
  tone = "lavender",
  span = 1,
}: PersonaTraitTileProps) => {
  const reveal = Math.max(0, Math.min(1, revealProgress));
  const backgroundColor =
    tone === "risk" ? COLORS.riskSoft : COLORS.lavenderSurface;

  return (
    <div
      style={{
        gridColumn: `span ${span}`,
        minHeight: 118,
        boxSizing: "border-box",
        padding: "20px 20px",
        borderRadius: RADII.card,
        border: `1px solid ${COLORS.border}`,
        backgroundColor,
        opacity: reveal,
        transform: `translateY(${14 * (1 - reveal)}px) scale(${0.99 + reveal * 0.01})`,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div
        style={{
          color: COLORS.textSecondary,
          fontSize: 14,
          fontWeight: TYPOGRAPHY.weight.bold,
          letterSpacing: "0.04em",
        }}
      >
        {label}
      </div>
      <div
        style={{
          marginTop: 12,
          color: COLORS.textPrimary,
          fontSize: 20,
          fontWeight: TYPOGRAPHY.weight.extraBold,
          lineHeight: 1.55,
        }}
      >
        {value}
      </div>
    </div>
  );
};
