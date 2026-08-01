import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

import {ComposerMock} from "../components/product/ComposerMock";
import {LandingPageMock} from "../components/product/LandingPageMock";
import {
  COLORS,
  MOTION,
  TYPOGRAPHY,
} from "../design/tokens";

const MESSAGE = "老师您好，我最近在准备研究生申请……";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

export type BrandLandingSceneProps = {
  /**
   * 当场景没有放进 Sequence，而是直接使用全片帧数时，
   * 可以通过此参数指定它从哪一帧开始。
   *
   * 放在 Sequence 中时保持默认 0。
   */
  startFrameOffset?: number;
};

export const BrandLandingScene = ({
  startFrameOffset = 0,
}: BrandLandingSceneProps) => {
  const rawFrame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const frame = Math.max(0, rawFrame - startFrameOffset);

  const createSpring = (
    startFrame: number,
    durationInFrames = 24,
  ) => {
    if (frame < startFrame) {
      return 0;
    }

    return spring({
      frame: frame - startFrame,
      fps,
      durationInFrames,
      config: {
        damping: MOTION.gentleSpring.damping,
        stiffness: MOTION.gentleSpring.stiffness,
        mass: MOTION.gentleSpring.mass,
        overshootClamping: true,
      },
    });
  };

  // Scene 01 Composer 到首页右侧 Preview 的 Match Cut
  const matchProgress = createSpring(0, 26);

  const composerTranslateX = interpolate(
    matchProgress,
    [0, 1],
    [0, 506],
    CLAMP,
  );

  const composerTranslateY = interpolate(
    matchProgress,
    [0, 1],
    [0, -36],
    CLAMP,
  );

  const composerScale = interpolate(
    matchProgress,
    [0, 1],
    [1, 0.72],
    CLAMP,
  );

  const composerOpacity = interpolate(
    frame,
    [18, 31],
    [1, 0],
    {
      ...CLAMP,
      easing: Easing.inOut(Easing.ease),
    },
  );

  const oldCopyOpacity = interpolate(
    frame,
    [0, 13],
    [1, 0],
    CLAMP,
  );

  const oldCopyTranslateY = interpolate(
    frame,
    [0, 13],
    [0, -10],
    CLAMP,
  );

  // 首页各区域进入
  const previewCardProgress = createSpring(8, 28);
  const previewContentProgress = createSpring(26, 30);

  const sidebarProgress = createSpring(18, 24);
  const heroCardProgress = createSpring(24, 26);

  // Hero 内元素按照 4 帧间隔错峰
  const badgeProgress = createSpring(32, 22);
  const titleProgress = createSpring(36, 24);
  const copyProgress = createSpring(40, 24);
  const buttonProgress = createSpring(44, 24);

  // CTA 只呼吸一次，不无限循环
  const buttonBreath = interpolate(
    frame,
    [96, 108, 120, 132],
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
      <LandingPageMock
        sidebarProgress={sidebarProgress}
        heroCardProgress={heroCardProgress}
        badgeProgress={badgeProgress}
        titleProgress={titleProgress}
        copyProgress={copyProgress}
        buttonProgress={buttonProgress}
        buttonBreath={buttonBreath}
        previewCardProgress={previewCardProgress}
        previewContentProgress={previewContentProgress}
      />

      {/* 保留 Scene 01 的结尾文案，前 13 帧内淡出 */}
      <div
        style={{
          position: "absolute",
          top: 648,
          left: 0,
          right: 0,
          zIndex: 20,
          textAlign: "center",
          color: COLORS.textPrimary,
          fontFamily: TYPOGRAPHY.fontFamily,
          fontSize: TYPOGRAPHY.size.sceneCopy,
          fontWeight: TYPOGRAPHY.weight.extraBold,
          lineHeight: TYPOGRAPHY.lineHeight.compact,
          letterSpacing: "-0.02em",
          opacity: oldCopyOpacity,
          transform: `translateY(${oldCopyTranslateY}px)`,
          pointerEvents: "none",
          willChange: "transform, opacity",
        }}
      >
        有些重要的话，发送之前总要想很久。
      </div>

      {/* Scene 01 Composer 的共享元素 Match Cut */}
      <div
        style={{
          position: "absolute",
          top: 365,
          left: "50%",
          zIndex: 30,
          width: 760,
          opacity: composerOpacity,
          transform:
            `translateX(-50%) ` +
            `translate(${composerTranslateX}px, ${composerTranslateY}px) ` +
            `scale(${composerScale})`,
          transformOrigin: "center center",
          pointerEvents: "none",
          willChange: "transform, opacity",
        }}
      >
        <ComposerMock
          text={MESSAGE}
          cursorOpacity={0}
        />
      </div>
    </AbsoluteFill>
  );
};
