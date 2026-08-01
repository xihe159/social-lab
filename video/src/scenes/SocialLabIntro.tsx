import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

import {ComposerMock} from "../components/product/ComposerMock";
import {
  COLORS,
  MOTION,
  TYPOGRAPHY,
  VIDEO,
} from "../design/tokens";

const MESSAGE = "老师您好，我最近在准备研究生申请……";
const MESSAGE_CHARACTERS = Array.from(MESSAGE);

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

/**
 * 根据当前帧计算输入光标透明度。
 *
 * 54–81 帧分成：
 * 显示 → 隐藏 → 显示 → 隐藏
 */
const getCursorOpacity = (frame: number): number => {
  if (frame < 12) {
    return 0;
  }

  if (frame < 54) {
    return 1;
  }

  if (frame >= 82) {
    return 0;
  }

  const blinkSegment = Math.floor((frame - 54) / 7);

  return blinkSegment % 2 === 0 ? 1 : 0;
};

/**
 * V2 Scene 01：还没有发送的那句话
 *
 * 0–14 帧：输入卡片进入
 * 12–54 帧：消息逐字输入
 * 54–82 帧：输入光标闪烁
 * 70–100 帧：主文案进入
 * 100–119 帧：保持画面
 */
export const SocialLabIntro = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const cardOpacity = interpolate(
    frame,
    [0, 14],
    [0, 1],
    {
      ...CLAMP,
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    },
  );

  const cardTranslateY = interpolate(
    frame,
    [0, 14],
    [MOTION.smallLift, 0],
    {
      ...CLAMP,
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    },
  );

  const cardSpringProgress = spring({
    frame,
    fps,
    durationInFrames: 18,
    config: {
      damping: MOTION.gentleSpring.damping,
      stiffness: MOTION.gentleSpring.stiffness,
      mass: MOTION.gentleSpring.mass,
    },
    overshootClamping: true,
  });

  const cardScale = interpolate(
    cardSpringProgress,
    [0, 1],
    [0.988, 1],
    CLAMP,
  );

  const visibleCharacterCount = Math.floor(
    interpolate(
      frame,
      [12, 54],
      [0, MESSAGE_CHARACTERS.length],
      {
        ...CLAMP,
        easing: Easing.bezier(0.22, 1, 0.36, 1),
      },
    ),
  );

  const visibleMessage = MESSAGE_CHARACTERS
    .slice(0, visibleCharacterCount)
    .join("");

  const cursorOpacity = getCursorOpacity(frame);

  const copyOpacity = interpolate(
    frame,
    [70, 100],
    [0, 1],
    {
      ...CLAMP,
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    },
  );

  const copyTranslateY = interpolate(
    frame,
    [70, 100],
    [14, 0],
    {
      ...CLAMP,
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    },
  );

  return (
    <AbsoluteFill
      style={{
        boxSizing: "border-box",
        overflow: "hidden",
        padding: VIDEO.safeArea,
        alignItems: "center",
        justifyContent: "center",
        background:
          `linear-gradient(180deg, ${COLORS.pageSoft} 0%, ${COLORS.page} 100%)`,
        color: COLORS.textPrimary,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 1100,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <div
          style={{
            opacity: cardOpacity,
            transform:
              `translateY(${cardTranslateY}px) scale(${cardScale})`,
            transformOrigin: "center center",
            willChange: "transform, opacity",
          }}
        >
          <ComposerMock
            text={visibleMessage}
            cursorOpacity={cursorOpacity}
          />
        </div>

        <div
          style={{
            width: 1040,
            minHeight: 72,
            marginTop: 54,
            textAlign: "center",
            color: COLORS.textPrimary,
            fontFamily: TYPOGRAPHY.fontFamily,
            fontSize: TYPOGRAPHY.size.sceneCopy,
            fontWeight: TYPOGRAPHY.weight.extraBold,
            lineHeight: TYPOGRAPHY.lineHeight.compact,
            letterSpacing: "-0.02em",
            opacity: copyOpacity,
            transform: `translateY(${copyTranslateY}px)`,
            willChange: "transform, opacity",
          }}
        >
          有些重要的话，发送之前总要想很久。
        </div>
      </div>
    </AbsoluteFill>
  );
};