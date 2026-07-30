import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export const SocialLabIntro = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleProgress = spring({
    frame,
    fps,
    config: {
      damping: 18,
      stiffness: 90,
      mass: 0.8,
    },
  });

  const titleOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const lineWidth = interpolate(frame, [20, 55], [0, 420], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const subtitleOpacity = interpolate(frame, [45, 75], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const subtitleY = interpolate(frame, [45, 75], [18, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 50% 45%, #172554 0%, #0f172a 48%, #020617 100%)",
        justifyContent: "center",
        alignItems: "center",
        color: "white",
        fontFamily:
          'Inter, "Microsoft YaHei", "PingFang SC", Arial, sans-serif',
      }}
      from={-18}
    >
      <div
        style={{
          textAlign: "center",
          opacity: titleOpacity,
          transform: `
            translateY(${40 * (1 - titleProgress)}px)
            scale(${0.92 + 0.08 * titleProgress})
          `,
        }}
      >
        <div
          style={{
            fontSize: 110,
            fontWeight: 700,
            letterSpacing: "-4px",
          }}
        >
          Social Lab
        </div>

        <div
          style={{
            width: lineWidth,
            height: 3,
            margin: "30px auto",
            borderRadius: 999,
            background: "rgba(255,255,255,0.72)",
          }}
        />

        <div
          style={{
            opacity: subtitleOpacity,
            transform: `translateY(${subtitleY}px)`,
            fontSize: 34,
            fontWeight: 400,
            letterSpacing: "2px",
            color: "rgba(255,255,255,0.72)",
          }}
        >
          在真正开口之前，先模拟一次
        </div>
      </div>
    </AbsoluteFill>
  );
};
