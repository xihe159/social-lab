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
import {COLORS, MOTION, TYPOGRAPHY} from "../design/tokens";

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

  const createSpring = (startFrame: number, durationInFrames = 24) => {
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

  // Scene 01 Composer 到首页右侧 Preview 的 Match Cut。
  const matchProgress = createSpring(0, 24);
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
  const composerScale = interpolate(matchProgress, [0, 1], [1, 0.72], CLAMP);
  const composerOpacity = interpolate(frame, [16, 29], [1, 0], {
    ...CLAMP,
    easing: Easing.inOut(Easing.ease),
  });

  const oldCopyOpacity = interpolate(frame, [0, 11], [1, 0], CLAMP);
  const oldCopyTranslateY = interpolate(frame, [0, 11], [0, -10], CLAMP);

  // 首页区域进入时间整体前移，避免内容已完成后继续静止。
  const previewCardProgress = createSpring(6, 26);
  const previewContentProgress = createSpring(22, 27);
  const sidebarProgress = createSpring(14, 22);
  const heroCardProgress = createSpring(20, 24);
  const badgeProgress = createSpring(27, 20);
  const titleProgress = createSpring(31, 22);
  const copyProgress = createSpring(35, 22);
  const buttonProgress = createSpring(39, 22);

  // CTA 呼吸与镜头缓慢推进覆盖场景后半段，让画面始终保持轻微变化。
  const buttonBreath = interpolate(
    frame,
    [72, 83, 96, 109],
    [0, 1, 1, 0],
    CLAMP,
  );
  const cameraProgress = interpolate(frame, [24, 124], [0, 1], {
    ...CLAMP,
    easing: Easing.inOut(Easing.ease),
  });
  const pageScale = interpolate(cameraProgress, [0, 1], [1.018, 1.052], CLAMP);
  const pageTranslateY = interpolate(cameraProgress, [0, 1], [8, -8], CLAMP);
  const pageTranslateX = interpolate(cameraProgress, [0, 1], [2, -5], CLAMP);
  const sceneOpacity = interpolate(frame, [0, 7, 119, 125], [0.96, 1, 1, 0.985], CLAMP);

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        backgroundColor: COLORS.page,
        color: COLORS.textPrimary,
        fontFamily: TYPOGRAPHY.fontFamily,
        opacity: sceneOpacity,
      }}
    >
      <AbsoluteFill
        style={{
          transform: `translate(${pageTranslateX}px, ${pageTranslateY}px) scale(${pageScale})`,
          transformOrigin: "50% 48%",
          willChange: "transform",
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
      </AbsoluteFill>

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
        <ComposerMock text={MESSAGE} cursorOpacity={0} />
      </div>
    </AbsoluteFill>
  );
};
