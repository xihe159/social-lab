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
import {COLORS, LAYOUT, MOTION, RADII, SHADOWS, TYPOGRAPHY} from "../design/tokens";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const CURSOR_PATH: readonly CursorPoint[] = [
  {frame: 0, x: 1700, y: 930},
  {frame: 128, x: 1420, y: 830},
  {frame: 150, x: 1135, y: 850},
  {frame: 174, x: 1135, y: 850},
  {frame: 209, x: 1135, y: 850},
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

  const createSpring = (startFrame: number, durationInFrames = 24) => {
    if (frame < startFrame) {
      return 0;
    }

    return spring({
      frame: frame - startFrame,
      fps,
      durationInFrames,
      config: MOTION.gentleSpring,
    });
  };

  const pageProgress = createSpring(0, 28);
  const sidebarProgress = createSpring(4, 24);
  const roleProgress = createSpring(28, 20);
  const relationProgress = createSpring(45, 20);
  const habitProgress = createSpring(62, 20);
  const chatProgress = createSpring(79, 22);
  const privacyProgress = interpolate(frame, [108, 138], [0, 1], CLAMP);
  const buttonProgress = createSpring(124, 22);
  const loadingProgress = interpolate(frame, [168, 178], [0, 1], CLAMP);
  const buttonPress = interpolate(frame, [150, 154, 158], [0, 1, 0], CLAMP);

  const roleText = revealText(demoSession.person.role, frame, 32, 42);
  const relationText = revealText(demoSession.person.relation, frame, 49, 61);
  const habitText = revealText(demoSession.person.habit, frame, 66, 79);
  const chatText =
    frame < 84
      ? ""
      : demoSession.person.chatLog
          .slice(0, frame >= 101 ? 2 : 1)
          .join("\n");

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
          transform: `translateY(${18 * (1 - pageProgress)}px)`,
        }}
      >
        <div style={{position: "absolute", left: 70, right: 70, top: 34}}>
          <ProgressTrack
            progress={0.4}
            label="补充对方信息"
            stepText="步骤 2 / 5"
          />
        </div>

        <div
          style={{
            width: LAYOUT.formWidth,
            margin: "108px auto 0",
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
                margin: "18px 0 10px",
                fontSize: 46,
                fontWeight: TYPOGRAPHY.weight.extraBold,
                lineHeight: 1.12,
                letterSpacing: "-0.035em",
              }}
            >
              你希望 AI 扮演谁？
            </h1>
            <p
              style={{
                margin: 0,
                color: COLORS.textSecondary,
                fontSize: 19,
                lineHeight: 1.7,
              }}
            >
              补充身份、关系和沟通习惯，让模拟不再是泛化回答。
            </p>
          </header>

          <div style={{display: "grid", gap: 17, marginTop: 24}}>
            <FormFieldMock
              label="对方身份"
              value={roleText}
              placeholder="例如：研究生导师"
              revealProgress={roleProgress}
              focusProgress={interpolate(frame, [30, 36, 43, 47], [0, 1, 1, 0], CLAMP)}
            />
            <FormFieldMock
              label="当前关系"
              value={relationText}
              placeholder="描述你们目前的关系"
              revealProgress={relationProgress}
              focusProgress={interpolate(frame, [47, 52, 62, 66], [0, 1, 1, 0], CLAMP)}
            />
            <FormFieldMock
              label="沟通习惯"
              value={habitText}
              placeholder="例如：回复较慢、比较严谨"
              revealProgress={habitProgress}
              focusProgress={interpolate(frame, [64, 69, 80, 84], [0, 1, 1, 0], CLAMP)}
            />
            <FormFieldMock
              label="可选聊天记录"
              value={chatText}
              placeholder="粘贴匿名化后的聊天记录"
              helper="仅用于演示画像生成逻辑，请勿放入真实敏感信息。"
              multiline
              revealProgress={chatProgress}
              focusProgress={interpolate(frame, [81, 87, 104, 108], [0, 1, 1, 0], CLAMP)}
            />
          </div>

          <div
            style={{
              marginTop: 16,
              color: "#8B8D98",
              fontSize: 13,
              lineHeight: 1.55,
              opacity: privacyProgress,
            }}
          >
            视频示例已做匿名处理；产品使用时请避免提交不必要的个人敏感信息。
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              marginTop: 20,
              opacity: buttonProgress,
              transform: `translateY(${12 * (1 - buttonProgress)}px)`,
            }}
          >
            <div
              style={{
                minWidth: 248,
                height: 58,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 10,
                padding: "0 24px",
                borderRadius: RADII.card,
                backgroundColor: COLORS.cta,
                color: COLORS.surface,
                boxShadow: SHADOWS.button,
                fontSize: 18,
                fontWeight: TYPOGRAPHY.weight.extraBold,
                transform: `scale(${1 - buttonPress * 0.025})`,
              }}
            >
              {loadingProgress > 0 ? (
                <>
                  <LoaderCircle
                    size={21}
                    strokeWidth={2.3}
                    style={{transform: `rotate(${frame * 18}deg)`}}
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
        clicks={[{start: 150, end: 158}]}
        visibleFrom={118}
        visibleUntil={182}
      />

      <AbsoluteFill
        style={{
          backgroundColor: COLORS.page,
          opacity: interpolate(frame, [198, 209], [0, 0.7], {
            ...CLAMP,
            easing: Easing.inOut(Easing.ease),
          }),
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
