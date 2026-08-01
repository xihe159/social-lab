import {ArrowRight} from "lucide-react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  interpolateColors,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

import {
  AnimatedCursor,
  type CursorPoint,
} from "../components/motion/AnimatedCursor";
import {OptionChip} from "../components/product/OptionChip";
import {ProgressTrack} from "../components/product/ProgressTrack";
import {QuestionCard} from "../components/product/QuestionCard";
import {WorkflowSidebar} from "../components/product/WorkflowSidebar";
import {
  COLORS,
  LAYOUT,
  RADII,
  SHADOWS,
  TYPOGRAPHY,
} from "../design/tokens";

const EXPECTED_RESULT =
  "希望导师愿意提供推荐，并明确材料和截止时间。";

const EXPECTED_RESULT_CHARACTERS =
  Array.from(EXPECTED_RESULT);

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const CURSOR_PATH: readonly CursorPoint[] = [
  {
    frame: 0,
    x: 1690,
    y: 920,
  },
  {
    frame: 34,
    x: 855,
    y: 373,
  },
  {
    frame: 66,
    x: 855,
    y: 373,
  },
  {
    frame: 88,
    x: 855,
    y: 388,
  },
  {
    frame: 108,
    x: 855,
    y: 388,
  },
  {
    frame: 124,
    x: 1070,
    y: 390,
  },
  {
    frame: 160,
    x: 1070,
    y: 390,
  },
  {
    frame: 176,
    x: 875,
    y: 390,
  },
  {
    frame: 204,
    x: 875,
    y: 390,
  },
  {
    frame: 228,
    x: 1170,
    y: 690,
  },
  {
    frame: 239,
    x: 1170,
    y: 690,
  },
];


const getPressProgress = (
  frame: number,
  start: number,
  middle: number,
  end: number,
): number => {
  return interpolate(
    frame,
    [start, middle, end],
    [0, 1, 0],
    CLAMP,
  );
};

export const ScenarioFormScene = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const createSpring = (
    startFrame: number,
    durationInFrames = 24,
  ): number => {
    if (frame < startFrame) {
      return 0;
    }

    return spring({
      frame: frame - startFrame,
      fps,
      durationInFrames,
      config: {
        damping: 190,
        stiffness: 145,
        mass: 0.8,
        overshootClamping: true,
      },
    });
  };

  const pageProgress = createSpring(4, 28);
  const sidebarProgress = createSpring(8, 24);

  const card1Reveal = createSpring(12, 22);
  const card2Reveal = createSpring(16, 22);
  const card3Reveal = createSpring(20, 22);
  const card4Reveal = createSpring(24, 22);

  const requestSelected = interpolate(
    frame,
    [43, 55],
    [0, 1],
    CLAMP,
  );

  const requestPressed = getPressProgress(
    frame,
    44,
    48,
    52,
  );

  const urgencySelected = interpolate(
    frame,
    [89, 101],
    [0, 1],
    CLAMP,
  );

  const urgencyPressed = getPressProgress(
    frame,
    90,
    94,
    98,
  );

  const concernSelected = interpolate(
    frame,
    [177, 189],
    [0, 1],
    CLAMP,
  );

  const concernPressed = getPressProgress(
    frame,
    178,
    182,
    186,
  );

  const card1Complete = interpolate(
    frame,
    [53, 61],
    [0, 1],
    CLAMP,
  );

  const card2Complete = interpolate(
    frame,
    [99, 107],
    [0, 1],
    CLAMP,
  );

  const card3Complete = interpolate(
    frame,
    [158, 166],
    [0, 1],
    CLAMP,
  );

  const card4Complete = interpolate(
    frame,
    [187, 195],
    [0, 1],
    CLAMP,
  );

  const visibleResultCharacterCount = Math.floor(
    interpolate(
      frame,
      [124, 158],
      [0, EXPECTED_RESULT_CHARACTERS.length],
      {
        ...CLAMP,
        easing: Easing.bezier(0.22, 1, 0.36, 1),
      },
    ),
  );

  const visibleExpectedResult =
    EXPECTED_RESULT_CHARACTERS
      .slice(0, visibleResultCharacterCount)
      .join("");

  const textFocusProgress = interpolate(
    frame,
    [118, 126, 160, 168],
    [0, 1, 1, 0],
    CLAMP,
  );

  const textBorderColor = interpolateColors(
    textFocusProgress,
    [0, 1],
    [COLORS.border, COLORS.brand],
  );

  const scrollY = interpolate(
    frame,
    [0, 70, 90, 116, 136, 166, 188, 210, 239],
    [0, 0, -190, -190, -400, -400, -610, -610, -680],
    {
      ...CLAMP,
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    },
  );

  const progressValue = interpolate(
    frame,
    [0, 34, 210],
    [0.04, 0.14, 0.2],
    CLAMP,
  );

  const ctaProgress = createSpring(205, 24);

  const handoffLineOpacity = interpolate(
    frame,
    [0, 8, 20],
    [1, 1, 0],
    CLAMP,
  );

  const handoffLineScale = interpolate(
    frame,
    [0, 18],
    [1, 3.8],
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
      <WorkflowSidebar
        activeStep={1}
        progress={sidebarProgress}
      />

      <main
        style={{
          position: "absolute",
          inset: `0 0 0 ${LAYOUT.sidebarWidth}px`,
          overflow: "hidden",
          backgroundColor: COLORS.page,
          opacity: pageProgress,
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 70,
            right: 70,
            top: 34,
            zIndex: 20,
          }}
        >
          <ProgressTrack
            progress={progressValue}
            label="设置沟通场景"
            stepText="步骤 1 / 5"
          />
        </div>

        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: 94,
            bottom: 0,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: 760,
              margin: "0 auto",
              paddingBottom: 90,
              transform:
                `translateY(${24 * (1 - pageProgress) + scrollY}px)`,
              willChange: "transform",
            }}
          >
            <header
              style={{
                marginBottom: 26,
              }}
            >
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  minHeight: 34,
                  padding: "7px 14px",
                  borderRadius: RADII.pill,
                  backgroundColor: COLORS.lavender,
                  color: COLORS.brand,
                  fontSize: 16,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                }}
              >
                导师沟通 · 场景设置
              </div>

              <h1
                style={{
                  margin: "18px 0 10px",
                  color: COLORS.textPrimary,
                  fontSize: 46,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                  lineHeight: 1.12,
                  letterSpacing: "-0.035em",
                }}
              >
                把沟通目标说清楚
              </h1>

              <p
                style={{
                  margin: 0,
                  color: COLORS.textSecondary,
                  fontSize: 19,
                  lineHeight: 1.7,
                }}
              >
                Social Lab 会根据任务、时间和担心点，
                构建更贴近真实关系的模拟情境。
              </p>
            </header>

            <div
              style={{
                display: "grid",
                gap: 18,
              }}
            >
              <QuestionCard
                number={1}
                title="你想完成什么？"
                description="选择这次沟通最核心的任务。"
                revealProgress={card1Reveal}
                completionProgress={card1Complete}
              >
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 12,
                  }}
                >
                  <OptionChip
                    label="请求推荐信"
                    selectedProgress={requestSelected}
                    pressedProgress={requestPressed}
                  />

                  <OptionChip label="讨论课题安排" />
                  <OptionChip label="申请延期" />
                </div>
              </QuestionCard>

              <QuestionCard
                number={2}
                title="时间有多紧？"
                description="时间压力会影响对方的判断和回复方式。"
                revealProgress={card2Reveal}
                completionProgress={card2Complete}
              >
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 12,
                  }}
                >
                  <OptionChip
                    label="本周内需要确认"
                    selectedProgress={urgencySelected}
                    pressedProgress={urgencyPressed}
                  />

                  <OptionChip label="两周内" />
                  <OptionChip label="暂不紧急" />
                </div>
              </QuestionCard>

              <QuestionCard
                number={3}
                title="你希望得到什么结果？"
                description="用一句话说明理想结果，帮助模拟保持目标一致。"
                revealProgress={card3Reveal}
                completionProgress={card3Complete}
              >
                <div
                  style={{
                    minHeight: 92,
                    boxSizing: "border-box",
                    padding: "18px 20px",
                    border: `1px solid ${textBorderColor}`,
                    borderRadius: RADII.input,
                    backgroundColor: COLORS.surface,
                    boxShadow:
                      textFocusProgress > 0
                        ? `0 0 0 4px rgba(47, 47, 99, ${
                            0.08 * textFocusProgress
                          })`
                        : "none",
                    color: visibleExpectedResult
                      ? COLORS.textPrimary
                      : COLORS.textMuted,
                    fontSize: 18,
                    fontWeight: TYPOGRAPHY.weight.medium,
                    lineHeight: 1.7,
                  }}
                >
                  {visibleExpectedResult ||
                    "例如：希望对方明确是否愿意提供帮助……"}

                  <span
                    style={{
                      display: "inline-block",
                      width: 2,
                      height: 23,
                      marginLeft: 4,
                      verticalAlign: "middle",
                      borderRadius: RADII.pill,
                      backgroundColor: COLORS.brand,
                      opacity:
                        frame >= 124 && frame <= 162
                          ? 1
                          : 0,
                    }}
                  />
                </div>
              </QuestionCard>

              <QuestionCard
                number={4}
                title="你最担心哪里出问题？"
                description="选择最需要在模拟中重点观察的风险。"
                revealProgress={card4Reveal}
                completionProgress={card4Complete}
              >
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 12,
                  }}
                >
                  <OptionChip
                    label="担心给对方造成时间压力"
                    selectedProgress={concernSelected}
                    pressedProgress={concernPressed}
                  />

                  <OptionChip label="信息不够完整" />
                  <OptionChip label="语气显得催促" />
                </div>
              </QuestionCard>

              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  paddingTop: 8,
                  opacity: ctaProgress,
                  transform:
                    `translateY(${15 * (1 - ctaProgress)}px)`,
                }}
              >
                <div
                  style={{
                    minWidth: 236,
                    height: 58,
                    boxSizing: "border-box",
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
                  }}
                >
                  继续补充对方信息
                  <ArrowRight size={20} strokeWidth={2.4} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <AnimatedCursor
        points={CURSOR_PATH}
        clicks={[
          {
            start: 44,
            end: 52,
          },
          {
            start: 90,
            end: 98,
          },
          {
            start: 120,
            end: 128,
          },
          {
            start: 178,
            end: 186,
          },
        ]}
        visibleFrom={18}
        visibleUntil={235}
      />

      {/* 与 Scene 03 最后一帧中央青柠线衔接 */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          zIndex: 300,
          width: 64,
          height: 6,
          borderRadius: RADII.pill,
          backgroundColor: COLORS.lime,
          opacity: handoffLineOpacity,
          transform:
            `translate(-50%, -50%) scaleX(${handoffLineScale})`,
          transformOrigin: "center",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};