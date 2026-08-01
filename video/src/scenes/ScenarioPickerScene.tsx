import {
  AbsoluteFill,
  Easing,
  Freeze,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {ArrowRight} from "lucide-react";

import {
  AnimatedCursor,
  type CursorPoint,
} from "../components/motion/AnimatedCursor";
import {
  ScenarioPickerModal,
  type ScenarioId,
} from "../components/product/ScenarioPickerModal";
import {
  COLORS,
  RADII,
  TYPOGRAPHY,
} from "../design/tokens";
import {BrandLandingScene} from "./BrandLandingScene";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

/**
 * 1920 × 1080 画布上的鼠标轨迹。
 *
 * 0–38：从右下方进入，移动到 CTA
 * 38–95：停留在 CTA
 * 95–128：移动到“导师”卡片
 * 128–159：Hover 与点击
 */
const CURSOR_PATH: readonly CursorPoint[] = [
  {
    frame: 0,
    x: 1760,
    y: 930,
  },
  {
    frame: 18,
    x: 1260,
    y: 830,
  },
  {
    frame: 38,
    x: 605,
    y: 705,
  },
  {
    frame: 95,
    x: 605,
    y: 705,
  },
  {
    frame: 128,
    x: 706,
    y: 560,
  },
  {
    frame: 159,
    x: 706,
    y: 560,
  },
  {
    frame: 179,
    x: 706,
    y: 560,
  },
];

const getMentorInteractionState = (
  frame: number,
): {
  hoveredScenario?: ScenarioId;
  pressedScenario?: ScenarioId;
  selectedScenario?: ScenarioId;
} => {
  if (frame >= 148) {
    return {
      hoveredScenario: "mentor",
      selectedScenario: "mentor",
    };
  }

  if (frame >= 145) {
    return {
      hoveredScenario: "mentor",
      pressedScenario: "mentor",
    };
  }

  if (frame >= 128) {
    return {
      hoveredScenario: "mentor",
    };
  }

  return {};
};

/**
 * Scene 03：选择沟通场景
 *
 * 0–38     鼠标进入并移动至 CTA
 * 38–42    CTA Hover
 * 42–45    CTA 按压
 * 45–72    遮罩与 Modal 进入
 * 65–95    三张场景卡 stagger
 * 95–128   鼠标移动到导师
 * 128–145  导师 Hover
 * 145–148  导师 Click
 * 148–160  选中反馈
 * 160–179  向 Scene 04 淡出
 */
export const ScenarioPickerScene = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const overlayOpacity = interpolate(
    frame,
    [45, 62],
    [0, 1],
    {
      ...CLAMP,
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    },
  );

  const backgroundBlur = interpolate(
    frame,
    [45, 65],
    [0, 6],
    CLAMP,
  );

  const backgroundScale = interpolate(
    frame,
    [45, 65],
    [1, 1.008],
    CLAMP,
  );

  const modalProgress =
    frame < 49
      ? 0
      : spring({
          frame: frame - 49,
          fps,
          durationInFrames: 23,
          config: {
            damping: 180,
            stiffness: 145,
            mass: 0.8,
            overshootClamping: true,
          },
        });

  const labelProgress =
    frame < 54
      ? 0
      : spring({
          frame: frame - 54,
          fps,
          durationInFrames: 20,
          config: {
            damping: 170,
            stiffness: 150,
            mass: 0.75,
            overshootClamping: true,
          },
        });

  const createCardProgress = (
    startFrame: number,
  ): number => {
    if (frame < startFrame) {
      return 0;
    }

    return spring({
      frame: frame - startFrame,
      fps,
      durationInFrames: 24,
      config: {
        damping: 190,
        stiffness: 150,
        mass: 0.8,
        overshootClamping: true,
      },
    });
  };

  const cardProgresses = [
    createCardProgress(65),
    createCardProgress(69),
    createCardProgress(73),
  ] as const;

  const ctaHoverProgress = interpolate(
    frame,
    [34, 40],
    [0, 1],
    CLAMP,
  );

  const ctaPressProgress = interpolate(
    frame,
    [42, 44, 47],
    [0, 1, 0],
    CLAMP,
  );

  const ctaScale =
    1 +
    ctaHoverProgress * 0.008 -
    ctaPressProgress * 0.026;

  const ctaShadowAlpha =
    0.24 +
    ctaHoverProgress * 0.14;

  const interactionState =
    getMentorInteractionState(frame);

  const exitOpacity = interpolate(
    frame,
    [160, 179],
    [0, 1],
    {
      ...CLAMP,
      easing: Easing.inOut(Easing.ease),
    },
  );

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        backgroundColor: COLORS.page,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      {/* 冻结 Scene 02 最后一帧，保证无缝衔接 */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          filter: `blur(${backgroundBlur}px)`,
          transform: `scale(${backgroundScale})`,
          transformOrigin: "center",
          willChange: "filter, transform",
        }}
      >
        <Freeze frame={149}>
          <BrandLandingScene />
        </Freeze>
      </div>

      {/*
       * 覆盖原 CTA，用于表现 Hover 和 3 帧按压。
       * 坐标与 Scene 02 的 Hero CTA 对齐。
       */}
      <div
        style={{
          position: "absolute",
          left: 502,
          top: 675,
          zIndex: 35,
          minWidth: 172,
          height: 56,
          boxSizing: "border-box",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 10,
          padding: "0 27px",
          borderRadius: 16,
          backgroundColor:
            ctaHoverProgress > 0
              ? COLORS.ctaHover
              : COLORS.cta,
          color: COLORS.surface,
          boxShadow:
            `0 12px 28px rgba(79, 157, 122, ` +
            `${ctaShadowAlpha})`,
          fontSize: 19,
          fontWeight: TYPOGRAPHY.weight.extraBold,
          transform: `scale(${ctaScale})`,
          transformOrigin: "center center",
          opacity: 1 - overlayOpacity,
          willChange:
            "transform, box-shadow, background-color",
        }}
      >
        开始模拟
        <ArrowRight
          size={20}
          strokeWidth={2.4}
        />
      </div>

      {/* 深色遮罩 */}
      <AbsoluteFill
        style={{
          zIndex: 50,
          backgroundColor:
            `rgba(20, 22, 34, ` +
            `${0.58 * overlayOpacity})`,
          backdropFilter:
            `blur(${backgroundBlur}px)`,
          WebkitBackdropFilter:
            `blur(${backgroundBlur}px)`,
          pointerEvents: "none",
        }}
      />

      <ScenarioPickerModal
        modalProgress={modalProgress}
        labelProgress={labelProgress}
        cardProgresses={cardProgresses}
        hoveredScenario={
          interactionState.hoveredScenario
        }
        pressedScenario={
          interactionState.pressedScenario
        }
        selectedScenario={
          interactionState.selectedScenario
        }
      />

      <AnimatedCursor
        points={CURSOR_PATH}
        clicks={[
          {
            start: 42,
            end: 47,
          },
          {
            start: 145,
            end: 150,
          },
        ]}
        visibleFrom={2}
        visibleUntil={170}
      />

      {/*
       * Scene 04 过渡底色。
       * 最后 20 帧覆盖模态框，为浅色表单页面做准备。
       */}
      <AbsoluteFill
        style={{
          zIndex: 300,
          backgroundColor: COLORS.page,
          opacity: exitOpacity,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            width: 64,
            height: 6,
            borderRadius: RADII.pill,
            backgroundColor: COLORS.lime,
            opacity: interpolate(
              exitOpacity,
              [0.55, 1],
              [0, 1],
              CLAMP,
            ),
            transform:
              `translate(-50%, -50%) ` +
              `scaleX(${interpolate(
                exitOpacity,
                [0.55, 1],
                [0.2, 1],
                CLAMP,
              )})`,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};