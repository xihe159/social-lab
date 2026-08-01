import {RotateCcw} from "lucide-react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

import {
  AnimatedCursor,
  type CursorPoint,
} from "../components/motion/AnimatedCursor";
import {ChatComposer} from "../components/product/ChatComposer";
import {demoSession} from "../data/demo-session";
import {COLORS, MOTION, RADII, SHADOWS, TYPOGRAPHY} from "../design/tokens";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const REWRITE = demoSession.report.rewrite;
const SEGMENTS = [
  "老师您好，我正在准备研究生申请，想请问您是否方便为我提供一封推荐信。",
  "学校最晚下月 15 日提交，我已经整理好项目清单、个人陈述和推荐要求。",
  "如果您时间上不方便，也请直接告诉我，我可以尽快调整安排。",
] as const;

const CURSOR_PATH: readonly CursorPoint[] = [
  {frame: 0, x: 1660, y: 930},
  {frame: 78, x: 1280, y: 810},
  {frame: 96, x: 1100, y: 792},
  {frame: 114, x: 1100, y: 792},
  {frame: 149, x: 1100, y: 792},
];

export const RewriteRetryScene = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const cardProgress =
    frame < 0
      ? 0
      : spring({
          frame,
          fps,
          durationInFrames: 28,
          config: MOTION.cardSpring,
        });

  const pageShift = interpolate(frame, [0, 26], [0, -130], {
    ...CLAMP,
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const segment1 = interpolate(frame, [24, 40], [0, 1], CLAMP);
  const segment2 = interpolate(frame, [40, 56], [0, 1], CLAMP);
  const segment3 = interpolate(frame, [56, 72], [0, 1], CLAMP);
  const tag1 = interpolate(frame, [52, 66], [0, 1], CLAMP);
  const tag2 = interpolate(frame, [60, 74], [0, 1], CLAMP);
  const tag3 = interpolate(frame, [68, 82], [0, 1], CLAMP);
  const buttonPress = interpolate(frame, [98, 103, 109], [0, 1, 0], CLAMP);
  const matchProgress = interpolate(frame, [110, 149], [0, 1], {
    ...CLAMP,
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const cardX = interpolate(matchProgress, [0, 1], [0, 160], CLAMP);
  const cardY = interpolate(matchProgress, [0, 1], [0, 245], CLAMP);
  const cardScale = interpolate(matchProgress, [0, 1], [1, 0.74], CLAMP);
  const cardBodyOpacity = interpolate(matchProgress, [0, 0.5, 1], [1, 0.35, 0], CLAMP);
  const composerOpacity = interpolate(matchProgress, [0.48, 1], [0, 1], CLAMP);

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
          left: 0,
          right: 0,
          top: 0,
          height: 310,
          transform: `translateY(${pageShift}px)`,
          opacity: interpolate(frame, [0, 28, 110, 140], [1, 0.55, 0.4, 0.1], CLAMP),
        }}
      >
        <div
          style={{
            width: 1040,
            margin: "42px auto 0",
            padding: "26px 30px",
            borderRadius: RADII.card,
            background: `linear-gradient(135deg, ${COLORS.lavenderSurface}, ${COLORS.limeSoft})`,
            boxShadow: SHADOWS.card,
          }}
        >
          <div
            style={{
              color: COLORS.textSecondary,
              fontSize: 14,
              fontWeight: TYPOGRAPHY.weight.bold,
            }}
          >
            本轮报告 · 推荐下一步
          </div>
          <div
            style={{
              marginTop: 10,
              fontSize: 28,
              fontWeight: TYPOGRAPHY.weight.extraBold,
            }}
          >
            把分析转化成下一次可以直接练习的表达
          </div>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: "50%",
          top: 180,
          width: 930,
          transform: `translateX(-50%) translate(${cardX}px, ${cardY}px) scale(${cardScale})`,
          transformOrigin: "center",
          zIndex: 30,
        }}
      >
        <section
          style={{
            boxSizing: "border-box",
            padding: "30px 32px",
            borderRadius: RADII.hero,
            border: `1px solid ${COLORS.border}`,
            backgroundColor: COLORS.lavenderSurface,
            boxShadow: SHADOWS.floating,
            opacity: cardProgress,
          }}
        >
          <div style={{opacity: cardBodyOpacity}}>
            <div
              style={{
                color: COLORS.brand,
                fontSize: 27,
                fontWeight: TYPOGRAPHY.weight.extraBold,
              }}
            >
              推荐表达
            </div>
            <div
              style={{
                marginTop: 20,
                padding: "22px 24px",
                borderRadius: RADII.card,
                border: `1px solid ${COLORS.border}`,
                backgroundColor: COLORS.surface,
                color: COLORS.textPrimary,
                fontSize: 18,
                fontWeight: TYPOGRAPHY.weight.medium,
                lineHeight: 1.75,
              }}
            >
              <span style={{opacity: segment1}}>{SEGMENTS[0]}</span>
              <span style={{opacity: segment2}}> {SEGMENTS[1]}</span>
              <span style={{opacity: segment3}}> {SEGMENTS[2]}</span>
            </div>

            <div style={{display: "flex", gap: 10, marginTop: 18, flexWrap: "wrap"}}>
              {[
                ["明确截止时间", tag1],
                ["降低额外工作量", tag2],
                ["给对方保留拒绝空间", tag3],
              ].map(([label, progress]) => (
                <span
                  key={String(label)}
                  style={{
                    padding: "8px 12px",
                    borderRadius: RADII.pill,
                    backgroundColor: COLORS.surface,
                    color: COLORS.brand,
                    fontSize: 14,
                    fontWeight: TYPOGRAPHY.weight.extraBold,
                    opacity: Number(progress),
                    transform: `translateY(${8 * (1 - Number(progress))}px)`,
                  }}
                >
                  {String(label)}
                </span>
              ))}
            </div>

            <div style={{display: "flex", justifyContent: "flex-end", marginTop: 24}}>
              <div
                style={{
                  height: 54,
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 9,
                  padding: "0 22px",
                  borderRadius: RADII.card,
                  backgroundColor: COLORS.cta,
                  color: COLORS.surface,
                  boxShadow: SHADOWS.button,
                  fontSize: 16,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                  transform: `scale(${1 - buttonPress * 0.035})`,
                }}
              >
                <RotateCcw size={19} strokeWidth={2.4} />
                用推荐版本重新模拟
              </div>
            </div>
          </div>
        </section>
      </div>

      <div
        style={{
          position: "absolute",
          left: "50%",
          bottom: 118,
          width: 900,
          transform: "translateX(-50%)",
          opacity: composerOpacity,
          zIndex: 40,
        }}
      >
        <div
          style={{
            marginBottom: 14,
            color: COLORS.textSecondary,
            fontSize: 15,
            fontWeight: TYPOGRAPHY.weight.bold,
          }}
        >
          推荐表达已填入，可以继续调整成更像你自己的说法。
        </div>
        <ChatComposer text={REWRITE} cursorOpacity={0} height={108} />
      </div>

      <AnimatedCursor
        points={CURSOR_PATH}
        clicks={[{start: 98, end: 109}]}
        visibleFrom={72}
        visibleUntil={120}
      />
    </AbsoluteFill>
  );
};
