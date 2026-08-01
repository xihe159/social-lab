import {AbsoluteFill, interpolate, useCurrentFrame} from "remotion";

import {BrandLockup} from "../components/product/BrandLockup";
import {COLORS, RADII, TYPOGRAPHY} from "../design/tokens";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

export const OutroScene = () => {
  const frame = useCurrentFrame();

  const textureScale = interpolate(frame, [0, 24], [1, 0.92], CLAMP);
  const textureOpacity = interpolate(frame, [0, 24], [0.34, 0.1], CLAMP);
  const brandProgress = interpolate(frame, [18, 50], [0, 1], CLAMP);
  const disclaimerProgress = interpolate(frame, [45, 68], [0, 1], CLAMP);

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        backgroundColor: COLORS.page,
        color: COLORS.textPrimary,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 80,
          display: "grid",
          gridTemplateColumns: "1fr 0.8fr",
          gap: 22,
          opacity: textureOpacity,
          transform: `scale(${textureScale})`,
          filter: "blur(1.5px)",
        }}
      >
        <div
          style={{
            borderRadius: RADII.hero,
            border: `1px solid ${COLORS.border}`,
            backgroundColor: COLORS.surface,
          }}
        />
        <div style={{display: "grid", gap: 18}}>
          <div
            style={{
              borderRadius: RADII.hero,
              border: `1px solid ${COLORS.border}`,
              backgroundColor: COLORS.lavenderSurface,
            }}
          />
          <div
            style={{
              borderRadius: RADII.hero,
              border: `1px solid ${COLORS.border}`,
              backgroundColor: COLORS.limeSoft,
            }}
          />
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%)",
        }}
      >
        <BrandLockup progress={brandProgress} />
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 58,
          textAlign: "center",
          color: COLORS.textSecondary,
          fontSize: 14,
          fontWeight: TYPOGRAPHY.weight.medium,
          opacity: disclaimerProgress,
          transform: `translateY(${8 * (1 - disclaimerProgress)}px)`,
        }}
      >
        沟通预演与决策支持工具 · 结果仅供练习参考
      </div>
    </AbsoluteFill>
  );
};
