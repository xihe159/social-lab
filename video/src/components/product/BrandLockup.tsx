import {COLORS, RADII, TYPOGRAPHY} from "../../design/tokens";

export type BrandLockupProps = {
  progress?: number;
  scale?: number;
};

export const BrandLockup = ({progress = 1, scale = 1}: BrandLockupProps) => {
  const safe = Math.max(0, Math.min(1, progress));

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 28,
        opacity: safe,
        transform: `translateY(${12 * (1 - safe)}px) scale(${scale})`,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div
        style={{
          width: 112,
          height: 112,
          display: "grid",
          placeItems: "center",
          borderRadius: 30,
          backgroundColor: COLORS.brand,
          color: COLORS.surface,
          fontSize: 42,
          fontWeight: TYPOGRAPHY.weight.extraBold,
          boxShadow: "0 24px 54px rgba(47,47,99,0.18)",
        }}
      >
        SL
      </div>
      <div>
        <div
          style={{
            color: COLORS.textPrimary,
            fontSize: 62,
            fontWeight: TYPOGRAPHY.weight.extraBold,
            lineHeight: 1,
            letterSpacing: "-0.04em",
          }}
        >
          Social Lab
        </div>
        <div
          style={{
            marginTop: 15,
            display: "inline-flex",
            padding: "8px 14px",
            borderRadius: RADII.pill,
            backgroundColor: COLORS.lavender,
            color: COLORS.brand,
            fontSize: 22,
            fontWeight: TYPOGRAPHY.weight.extraBold,
          }}
        >
          先演练，再开口。
        </div>
      </div>
    </div>
  );
};
