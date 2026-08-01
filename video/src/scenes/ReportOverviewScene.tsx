import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

import {ActionPanel} from "../components/product/ActionPanel";
import {FactorCard} from "../components/product/FactorCard";
import {ProgressTrack} from "../components/product/ProgressTrack";
import {ReportHero} from "../components/product/ReportHero";
import {WorkflowSidebar} from "../components/product/WorkflowSidebar";
import {demoSession} from "../data/demo-session";
import {COLORS, LAYOUT, MOTION, RADII, SHADOWS, TYPOGRAPHY} from "../design/tokens";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

export const ReportOverviewScene = () => {
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
      config: MOTION.cardSpring,
    });
  };

  const pageProgress = createSpring(0, 28);
  const sidebarProgress = createSpring(4, 24);
  const heroProgress = createSpring(0, 32);
  const score = Math.round(interpolate(frame, [20, 70], [0, 78], CLAMP));
  const metaProgress = interpolate(frame, [60, 100], [0, 1], CLAMP);
  const summaryProgress = interpolate(frame, [95, 160], [0, 1], CLAMP);
  const factor1 = createSpring(145, 28);
  const factor2 = createSpring(153, 28);
  const factor3 = createSpring(161, 28);
  const actionProgress = createSpring(200, 36);

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        backgroundColor: COLORS.page,
        color: COLORS.textPrimary,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <WorkflowSidebar activeStep={5} progress={sidebarProgress} />

      <main
        style={{
          position: "absolute",
          inset: `0 0 0 ${LAYOUT.sidebarWidth}px`,
          opacity: pageProgress,
          transform: `translateY(${16 * (1 - pageProgress)}px)`,
        }}
      >
        <div style={{position: "absolute", left: 70, right: 70, top: 34}}>
          <ProgressTrack
            progress={1}
            label="沟通报告"
            stepText="步骤 5 / 5"
          />
        </div>

        <div style={{width: 1040, margin: "96px auto 0"}}>
          <header
            style={{
              display: "flex",
              alignItems: "flex-end",
              justifyContent: "space-between",
              gap: 24,
              marginBottom: 18,
            }}
          >
            <div>
              <div
                style={{
                  display: "inline-flex",
                  padding: "7px 13px",
                  borderRadius: RADII.pill,
                  backgroundColor: COLORS.lavender,
                  color: COLORS.brand,
                  fontSize: 14,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                }}
              >
                Demo Data · 练习参考
              </div>
              <h1
                style={{
                  margin: "14px 0 0",
                  fontSize: 42,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                  letterSpacing: "-0.035em",
                }}
              >
                本轮沟通报告
              </h1>
            </div>
            <div
              style={{
                color: COLORS.textSecondary,
                fontSize: 14,
                lineHeight: 1.55,
                textAlign: "right",
              }}
            >
              分数和预测用于演练与决策支持，
              <br />
              不代表现实结果保证。
            </div>
          </header>

          <div style={{opacity: Math.max(metaProgress, summaryProgress * 0.7)}}>
            <ReportHero
              score={score}
              resultLabel={demoSession.report.resultLabel}
              confidence={demoSession.report.confidence}
              rangeText={`${demoSession.report.range[0]}–${demoSession.report.range[1]}`}
              summary={demoSession.report.summary}
              likelyOutcome={demoSession.report.likelyOutcome}
              revealProgress={heroProgress}
            />
          </div>

          <section
            style={{
              marginTop: 18,
              padding: "22px 24px 24px",
              borderRadius: RADII.card,
              border: `1px solid ${COLORS.border}`,
              backgroundColor: COLORS.surface,
              boxShadow: SHADOWS.card,
            }}
          >
            <h2
              style={{
                margin: "0 0 16px",
                fontSize: 23,
                fontWeight: TYPOGRAPHY.weight.extraBold,
              }}
            >
              最关键的三个影响
            </h2>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                gap: 14,
              }}
            >
              <FactorCard
                direction="positive"
                title={demoSession.report.factors[0].title}
                impact={demoSession.report.factors[0].impact}
                revealProgress={factor1}
              />
              <FactorCard
                direction="positive"
                title={demoSession.report.factors[1].title}
                impact={demoSession.report.factors[1].impact}
                revealProgress={factor2}
              />
              <FactorCard
                direction="negative"
                title={demoSession.report.factors[2].title}
                impact={demoSession.report.factors[2].impact}
                revealProgress={factor3}
              />
            </div>
          </section>

          <div style={{marginTop: 16}}>
            <ActionPanel
              text={demoSession.report.nextStep}
              revealProgress={actionProgress}
            />
          </div>
        </div>
      </main>
    </AbsoluteFill>
  );
};
