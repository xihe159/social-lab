import {ArrowRight, LoaderCircle} from "lucide-react";
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
import {FormFieldMock} from "../components/product/FormFieldMock";
import {ProgressTrack} from "../components/product/ProgressTrack";
import {WorkflowSidebar} from "../components/product/WorkflowSidebar";
import {demoSession} from "../data/demo-session";
import {
  COLORS,
  LAYOUT,
  MOTION,
  RADII,
  SHADOWS,
  TYPOGRAPHY,
  VIDEO,
} from "../design/tokens";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const GOLDEN_RATIO = 1.61803398875;
const GOLDEN_CONTENT_WIDTH = Math.round(
  (VIDEO.width - LAYOUT.sidebarWidth) / GOLDEN_RATIO,
);

const CURSOR_PATH: readonly CursorPoint[] = [
  {frame: 0, x: 1700, y: 930},
  {frame: 100, x: 1640, y: 860},
  {frame: 116, x: 1510, y: 735},
  {frame: 122, x: 1480, y: 704},
  {frame: 134, x: 1480, y: 704},
  {frame: 152, x: 1510, y: 735},
  {frame: 179, x: 1510, y: 735},
];

const revealText = (
  text: string,
  frame: number,
  from: number,
  to: number,
): string => {
  const characters = Array.from(text);
  const count = Math.floor(
    interpolate(frame, [from, to], [0, characters.length], CLAMP),
  );
  return characters.slice(0, count).join("");
};

export const PersonSetupScene = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const createSpring = (startFrame: number, durationInFrames = 22) => {
    if (frame < startFrame) {
      return 0;
    }

    return spring({
      frame: frame - startFrame,
      fps,
      durationInFrames,
      config: {
        ...MOTION.gentleSpring,
        overshootClamping: true,
      },
    });
  };

  const pageProgress = createSpring(0, 25);
  const sidebarProgress = createSpring(2, 22);
  const roleProgress = createSpring(14, 18);
  const relationProgress = createSpring(24, 18);
  const habitProgress = createSpring(38, 18);
  const chatProgress = createSpring(52, 20);
  const privacyProgress = interpolate(frame, [82, 104], [0, 1], CLAMP);
  const buttonProgress = createSpring(92, 20);
  const loadingProgress = interpolate(frame, [136, 146], [0, 1], CLAMP);
  const buttonPress = interpolate(frame, [122, 126, 130], [0, 1, 0], CLAMP);
  const completionPulse = interpolate(
    frame,
    [146, 153, 161],
    [0, 1, 0],
    CLAMP,
  );

  const roleText = revealText(demoSession.person.role, frame, 18, 28);
  const relationText = revealText(demoSession.person.relation, frame, 30, 42);
  const habitText = revealText(demoSession.person.habit, frame, 46, 60);
  const chatText =
    frame < 70
      ? ""
      : demoSession.person.chatLog
          .slice(0, frame >= 84 ? 2 : 1)
          .join("\n");

  const mainScale = interpolate(pageProgress, [0, 1], [0.985, 1], CLAMP);
  const mainTranslateY = interpolate(pageProgress, [0, 1], [20, 0], CLAMP);
  const fadeToNext = interpolate(frame, [162, 179], [0, 0.72], {
    ...CLAMP,
    easing: Easing.inOut(Easing.ease),
  });

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        backgroundColor: COLORS.page,
        color: COLORS.textPrimary,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <WorkflowSidebar activeStep={2} progress={sidebarProgress} />

      <main
        style={{
          position: "absolute",
          inset: `0 0 0 ${LAYOUT.sidebarWidth}px`,
          opacity: pageProgress,
          transform: `translateY(${mainTranslateY}px) scale(${mainScale})`,
          transformOrigin: "50% 48%",
          willChange: "transform, opacity",
        }}
      >
        <div style={{position: "absolute", left: 70, right: 70, top: 30}}>
          <ProgressTrack
            progress={0.4}
            label="补充对方信息"
            stepText="步骤 2 / 5"
          />
        </div>

        <div
          style={{
            width: GOLDEN_CONTENT_WIDTH,
            margin: "90px auto 0",
          }}
        >
          <header>
            <div
              style={{
                display: "inline-flex",
                padding: "7px 14px",
                borderRadius: RADII.pill,
                backgroundColor: COLORS.lavender,
                color: COLORS.brand,
                fontSize: 16,
                fontWeight: TYPOGRAPHY.weight.extraBold,
              }}
            >
              导师沟通 · 对方设置
            </div>
            <h1
              style={{
                margin: "14px 0 8px",
                fontSize: 44,
                fontWeight: TYPOGRAPHY.weight.extraBold,
                lineHeight: 1.1,
                letterSpacing: "-0.035em",
              }}
            >
              你希望 AI 扮演谁？
            </h1>
            <p
              style={{
                margin: 0,
                color: COLORS.textSecondary,
                fontSize: 18,
                lineHeight: 1.55,
              }}
            >
              补充身份、关系和沟通习惯，让模拟不再是泛化回答。
            </p>
          </header>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
              gap: 14,
              marginTop: 20,
            }}
          >
            <FormFieldMock
              label="对方身份"
              value={roleText}
              placeholder="例如：研究生导师"
              revealProgress={roleProgress}
              focusProgress={interpolate(
                frame,
                [16, 20, 29, 33],
                [0, 1, 1, 0],
                CLAMP,
              )}
            />
            <FormFieldMock
              label="当前关系"
              value={relationText}
              placeholder="描述你们目前的关系"
              revealProgress={relationProgress}
              focusProgress={interpolate(
                frame,
                [27, 31, 43, 47],
                [0, 1, 1, 0],
                CLAMP,
              )}
            />
            <div style={{gridColumn: "1 / -1"}}>
              <FormFieldMock
                label="沟通习惯"
                value={habitText}
                placeholder="例如：回复较慢、比较严谨"
                revealProgress={habitProgress}
                focusProgress={interpolate(
                  frame,
                  [43, 47, 61, 65],
                  [0, 1, 1, 0],
                  CLAMP,
                )}
              />
            </div>
            <div style={{gridColumn: "1 / -1"}}>
              <FormFieldMock
                label="可选聊天记录"
                value={chatText}
                placeholder="粘贴匿名化后的聊天记录"
                helper="仅用于演示画像生成逻辑，请勿放入真实敏感信息。"
                multiline
                revealProgress={chatProgress}
                focusProgress={interpolate(
                  frame,
                  [57, 63, 87, 91],
                  [0, 1, 1, 0],
                  CLAMP,
                )}
              />
            </div>
          </div>

          <div
            style={{
              marginTop: 12,
              color: "#8B8D98",
              fontSize: 13,
              lineHeight: 1.5,
              opacity: privacyProgress,
            }}
          >
            视频示例已做匿名处理；产品使用时请避免提交不必要的个人敏感信息。
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              marginTop: 16,
              opacity: buttonProgress,
              transform: `translateY(${10 * (1 - buttonProgress)}px)`,
            }}
          >
            <div
              style={{
                minWidth: 268,
                height: 58,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 10,
                padding: "0 26px",
                borderRadius: RADII.card,
                backgroundColor: COLORS.cta,
                color: COLORS.surface,
                boxShadow: SHADOWS.button,
                fontSize: 18,
                fontWeight: TYPOGRAPHY.weight.extraBold,
                transform: `scale(${1 - buttonPress * 0.025 + completionPulse * 0.008})`,
                willChange: "transform",
              }}
            >
              {loadingProgress > 0 ? (
                <>
                  <LoaderCircle
                    size={21}
                    strokeWidth={2.3}
                    style={{transform: `rotate(${frame * 16}deg)`}}
                  />
                  正在生成画像...
                </>
              ) : (
                <>
                  生成 AI 扮演对象
                  <ArrowRight size={20} strokeWidth={2.4} />
                </>
              )}
            </div>
          </div>
        </div>
      </main>

      <AnimatedCursor
        points={CURSOR_PATH}
        clicks={[{start: 122, end: 130}]}
        visibleFrom={96}
        visibleUntil={154}
      />

      <AbsoluteFill
        style={{
          backgroundColor: COLORS.page,
          opacity: fadeToNext,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
