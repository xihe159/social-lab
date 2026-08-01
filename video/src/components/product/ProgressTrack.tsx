import {COLORS, RADII, TYPOGRAPHY} from "../../design/tokens";

export type ProgressTrackProps = {
  progress: number;
  label?: string;
  stepText?: string;
};

const clamp01 = (value: number): number => {
  return Math.max(0, Math.min(1, value));
};

export const ProgressTrack = ({
  progress,
  label = "设置沟通场景",
  stepText = "步骤 1 / 5",
}: ProgressTrackProps) => {
  const safeProgress = clamp01(progress);

  return (
    <div
      style={{
        width: "100%",
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 12,
          color: COLORS.textSecondary,
          fontSize: 16,
          fontWeight: TYPOGRAPHY.weight.medium,
        }}
      >
        <span>{label}</span>
        <span>{stepText}</span>
      </div>

      <div
        style={{
          width: "100%",
          height: 6,
          overflow: "hidden",
          borderRadius: RADII.pill,
          backgroundColor: COLORS.progressTrack,
        }}
      >
        <div
          style={{
            width: `${safeProgress * 100}%`,
            height: "100%",
            borderRadius: RADII.pill,
            backgroundColor: COLORS.cta,
          }}
        />
      </div>
    </div>
  );
};
