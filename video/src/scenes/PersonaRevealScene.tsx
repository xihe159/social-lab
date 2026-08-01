import {ArrowRight, Sparkles} from "lucide-react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

import {PersonaTraitTile} from "../components/product/PersonaTraitTile";
import {ProgressTrack} from "../components/product/ProgressTrack";
import {RelationshipMetricRow} from "../components/product/RelationshipMetricRow";
import {WorkflowSidebar} from "../components/product/WorkflowSidebar";
import {demoSession} from "../data/demo-session";
import {COLORS, LAYOUT, MOTION, RADII, SHADOWS, TYPOGRAPHY} from "../design/tokens";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

export const PersonaRevealScene = () => {
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

  const pageProgress = createSpring(4, 28);
  const sidebarProgress = createSpring(8, 24);
  const splitProgress = createSpring(28, 42);
  const trait1 = createSpring(70, 22);
  const trait2 = createSpring(74, 22);
  const trait3 = createSpring(78, 22);
  const trait4 = createSpring(82, 22);
  const metricProgress = interpolate(frame, [92, 150], [0, 1], CLAMP);
  const strategyProgress = createSpring(150, 30);
  const buttonProgress = createSpring(190, 30);

  const leftTranslate = interpolate(splitProgress, [0, 1], [118, 0], CLAMP);
  const rightTranslate = interpolate(splitProgress, [0, 1], [-118, 0], CLAMP);

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        backgroundColor: COLORS.page,
        color: COLORS.textPrimary,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <WorkflowSidebar activeStep={3} progress={sidebarProgress} />

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
            progress={0.6}
            label="查看对象画像"
            stepText="步骤 3 / 5"
          />
        </div>

        <div style={{width: 1080, margin: "104px auto 0"}}>
          <header>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                padding: "7px 14px",
                borderRadius: RADII.pill,
                backgroundColor: COLORS.lavender,
                color: COLORS.brand,
                fontSize: 16,
                fontWeight: TYPOGRAPHY.weight.extraBold,
              }}
            >
              <Sparkles size={18} strokeWidth={2.2} />
              AI 对象画像
            </div>
            <h1
              style={{
                margin: "18px 0 8px",
                fontSize: 46,
                fontWeight: TYPOGRAPHY.weight.extraBold,
                letterSpacing: "-0.035em",
              }}
            >
              {demoSession.persona.title}
            </h1>
            <p
              style={{
                margin: 0,
                color: COLORS.textSecondary,
                fontSize: 18,
                lineHeight: 1.65,
              }}
            >
              AI 将根据这个画像扮演对方，并持续结合关系状态生成回应。
            </p>
          </header>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1.08fr 0.92fr",
              gap: 22,
              marginTop: 24,
            }}
          >
            <section
              style={{
                boxSizing: "border-box",
                padding: 24,
                borderRadius: RADII.hero,
                border: `1px solid ${COLORS.border}`,
                backgroundColor: COLORS.surface,
                boxShadow: SHADOWS.card,
                opacity: splitProgress,
                transform: `translateX(${leftTranslate}px) scale(${0.98 + splitProgress * 0.02})`,
              }}
            >
              <h2
                style={{
                  margin: "0 0 18px",
                  fontSize: 24,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                }}
              >
                Persona Card
              </h2>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                  gap: 14,
                }}
              >
                <PersonaTraitTile
                  label="沟通风格"
                  value={demoSession.persona.style}
                  revealProgress={trait1}
                />
                <PersonaTraitTile
                  label="回复速度"
                  value={demoSession.persona.speed}
                  revealProgress={trait2}
                />
                <PersonaTraitTile
                  label="关注重点"
                  value={demoSession.persona.focus}
                  revealProgress={trait3}
                />
                <PersonaTraitTile
                  label="风险点"
                  value={demoSession.persona.risk}
                  revealProgress={trait4}
                  tone="risk"
                />
              </div>
            </section>

            <section
              style={{
                boxSizing: "border-box",
                padding: 24,
                borderRadius: RADII.hero,
                border: `1px solid ${COLORS.border}`,
                backgroundColor: COLORS.surface,
                boxShadow: SHADOWS.card,
                opacity: splitProgress,
                transform: `translateX(${rightTranslate}px) scale(${0.98 + splitProgress * 0.02})`,
              }}
            >
              <h2
                style={{
                  margin: "0 0 22px",
                  fontSize: 24,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                }}
              >
                Relationship State
              </h2>
              <div style={{display: "grid", gap: 22}}>
                <RelationshipMetricRow
                  label="信任"
                  displayValue="63"
                  fillPercent={63}
                  progress={metricProgress}
                />
                <RelationshipMetricRow
                  label="情绪"
                  displayValue="+8"
                  fillPercent={54}
                  progress={metricProgress}
                />
                <RelationshipMetricRow
                  label="压力"
                  displayValue="42"
                  fillPercent={42}
                  progress={metricProgress}
                />
                <RelationshipMetricRow
                  label="开放度"
                  displayValue="58"
                  fillPercent={58}
                  progress={metricProgress}
                />
              </div>
            </section>
          </div>

          <section
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 24,
              marginTop: 20,
              padding: "22px 24px",
              borderRadius: RADII.card,
              backgroundColor: COLORS.limeSoft,
              opacity: strategyProgress,
              transform: `translateY(${16 * (1 - strategyProgress)}px)`,
            }}
          >
            <div>
              <div
                style={{
                  color: COLORS.optionSelectedText,
                  fontSize: 14,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                }}
              >
                推荐策略
              </div>
              <div
                style={{
                  maxWidth: 760,
                  marginTop: 8,
                  color: COLORS.textPrimary,
                  fontSize: 19,
                  fontWeight: TYPOGRAPHY.weight.bold,
                  lineHeight: 1.6,
                }}
              >
                先说明申请信息和截止时间，再明确你已经准备好的材料，
                <span style={{color: COLORS.optionSelectedText}}>
                  降低对方的额外工作量。
                </span>
              </div>
            </div>
            <div
              style={{
                height: 54,
                minWidth: 164,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 9,
                padding: "0 23px",
                borderRadius: RADII.card,
                backgroundColor: COLORS.cta,
                color: COLORS.surface,
                boxShadow: SHADOWS.button,
                fontSize: 18,
                fontWeight: TYPOGRAPHY.weight.extraBold,
                opacity: buttonProgress,
                transform: `translateY(${12 * (1 - buttonProgress)}px)`,
              }}
            >
              开始模拟
              <ArrowRight size={20} strokeWidth={2.4} />
            </div>
          </section>
        </div>
      </main>
    </AbsoluteFill>
  );
};
