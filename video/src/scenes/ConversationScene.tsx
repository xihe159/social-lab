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
import {MessageBubble} from "../components/product/MessageBubble";
import {ProgressTrack} from "../components/product/ProgressTrack";
import {WorkflowSidebar} from "../components/product/WorkflowSidebar";
import {demoSession} from "../data/demo-session";
import {COLORS, LAYOUT, MOTION, RADII, TYPOGRAPHY} from "../design/tokens";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const USER_MESSAGE = demoSession.messages[0].text;
const USER_MESSAGE_CHARACTERS = Array.from(USER_MESSAGE);

const CURSOR_PATH: readonly CursorPoint[] = [
  {frame: 0, x: 1660, y: 920},
  {frame: 52, x: 1300, y: 886},
  {frame: 64, x: 1250, y: 885},
  {frame: 78, x: 1250, y: 885},
  {frame: 299, x: 1250, y: 885},
];

export const ConversationScene = () => {
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
  const typedCharacterCount = Math.floor(
    interpolate(frame, [0, 55], [0, USER_MESSAGE_CHARACTERS.length], {
      ...CLAMP,
      easing: Easing.bezier(0.22, 1, 0.36, 1),
    }),
  );
  const typedText = USER_MESSAGE_CHARACTERS.slice(0, typedCharacterCount).join("");
  const sendPressed = interpolate(frame, [61, 65, 70], [0, 1, 0], CLAMP);
  const clearProgress = interpolate(frame, [72, 80], [0, 1], CLAMP);
  const userBubbleProgress = createSpring(72, 30);
  const targetBubbleProgress = createSpring(136, 38);
  const typingOpacity = interpolate(
    frame,
    [104, 112, 128, 138],
    [0, 1, 1, 0],
    CLAMP,
  );
  const chatTranslateY = interpolate(frame, [72, 136, 185], [0, -8, -34], CLAMP);
  const chipEmphasis = interpolate(
    frame,
    [185, 205, 230, 250],
    [0, 1, 1, 0],
    CLAMP,
  );

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        backgroundColor: COLORS.page,
        color: COLORS.textPrimary,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <WorkflowSidebar activeStep={4} progress={sidebarProgress} />

      <main
        style={{
          position: "absolute",
          inset: `0 0 0 ${LAYOUT.sidebarWidth}px`,
          opacity: pageProgress,
          transform: `translateY(${14 * (1 - pageProgress)}px)`,
        }}
      >
        <div style={{position: "absolute", left: 70, right: 70, top: 34}}>
          <ProgressTrack
            progress={0.8}
            label="模拟沟通"
            stepText="步骤 4 / 5"
          />
        </div>

        <div style={{width: 760, margin: "104px auto 0"}}>
          <header
            style={{
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "space-between",
              gap: 24,
            }}
          >
            <div>
              <h1
                style={{
                  margin: 0,
                  fontSize: 42,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                  letterSpacing: "-0.035em",
                }}
              >
                与研究生导师模拟沟通
              </h1>
              <div
                style={{
                  marginTop: 9,
                  color: COLORS.textSecondary,
                  fontSize: 17,
                  fontWeight: TYPOGRAPHY.weight.medium,
                }}
              >
                当前态度：谨慎
              </div>
            </div>
            <div
              style={{
                height: 44,
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                padding: "0 15px",
                borderRadius: RADII.input,
                border: `1px solid ${COLORS.borderStrong}`,
                backgroundColor: COLORS.surface,
                color: COLORS.brand,
                fontSize: 15,
                fontWeight: TYPOGRAPHY.weight.bold,
              }}
            >
              <RotateCcw size={17} strokeWidth={2.3} />
              重新开始
            </div>
          </header>

          <div
            style={{
              display: "inline-flex",
              marginTop: 22,
              padding: "9px 14px",
              borderRadius: RADII.pill,
              backgroundColor: COLORS.lavender,
              color: COLORS.brand,
              fontSize: 15,
              fontWeight: TYPOGRAPHY.weight.bold,
              boxShadow:
                chipEmphasis > 0
                  ? `0 0 0 ${4 * chipEmphasis}px rgba(200,244,122,${0.24 * chipEmphasis})`
                  : "none",
            }}
          >
            对方目前关注：材料完整性与时间安排
          </div>

          <div
            style={{
              height: 548,
              marginTop: 18,
              display: "grid",
              gridTemplateRows: "1fr auto",
              gap: 18,
            }}
          >
            <div
              style={{
                overflow: "hidden",
                padding: "8px 4px 0",
              }}
            >
              <div
                style={{
                  display: "grid",
                  gap: 18,
                  transform: `translateY(${chatTranslateY}px)`,
                }}
              >
                <MessageBubble
                  role="user"
                  text={USER_MESSAGE}
                  revealProgress={userBubbleProgress}
                />

                <div
                  style={{
                    marginLeft: 8,
                    color: COLORS.cta,
                    fontSize: 14,
                    fontWeight: TYPOGRAPHY.weight.bold,
                    opacity: typingOpacity,
                  }}
                >
                  对方正在输入中...
                </div>

                <MessageBubble
                  role="target"
                  text={demoSession.messages[1].text}
                  revealProgress={targetBubbleProgress}
                />
              </div>
            </div>

            <ChatComposer
              text={clearProgress >= 1 ? "" : typedText}
              cursorOpacity={frame <= 55 ? 1 : 0}
              revealProgress={1}
              sendPressedProgress={sendPressed}
              height={86}
            />
          </div>
        </div>
      </main>

      <AnimatedCursor
        points={CURSOR_PATH}
        clicks={[{start: 61, end: 70}]}
        visibleFrom={42}
        visibleUntil={86}
      />
    </AbsoluteFill>
  );
};
