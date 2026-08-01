import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
} from "remotion";

import {EvidenceHighlight} from "../components/product/EvidenceHighlight";
import {MetricDeltaCard} from "../components/product/MetricDeltaCard";
import {COLORS, RADII, SHADOWS, TYPOGRAPHY} from "../design/tokens";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const animatedValue = (
  frame: number,
  startFrame: number,
  endFrame: number,
  from: number,
  to: number,
) =>
  Math.round(
    interpolate(frame, [startFrame, endFrame], [from, to], CLAMP),
  );

export const DynamicsScene = () => {
  const frame = useCurrentFrame();

  const cardsProgress = interpolate(frame, [0, 24], [0, 1], CLAMP);
  const timeHighlight = interpolate(frame, [24, 44, 64, 72], [0, 1, 1, 0.6], CLAMP);
  const materialHighlight = interpolate(frame, [72, 92, 112, 120], [0, 1, 1, 0.6], CLAMP);
  const descriptionHighlight = interpolate(frame, [120, 136, 156, 164], [0, 1, 1, 0.6], CLAMP);

  const trust = animatedValue(frame, 24, 72, 63, 66);
  const willingness = animatedValue(frame, 72, 120, 58, 61);
  const progress = animatedValue(frame, 120, 164, 41, 45);
  const pressure = animatedValue(frame, 120, 164, 42, 40);

  const copyProgress = interpolate(frame, [150, 192], [0, 1], CLAMP);

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        backgroundColor: COLORS.page,
        color: COLORS.textPrimary,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div
        style={{
          width: 1320,
          margin: "118px auto 0",
          display: "grid",
          gridTemplateColumns: "1.25fr 0.75fr",
          gap: 28,
          alignItems: "start",
        }}
      >
        <section
          style={{
            boxSizing: "border-box",
            padding: "34px 38px",
            borderRadius: RADII.hero,
            border: `1px solid ${COLORS.border}`,
            backgroundColor: COLORS.surface,
            boxShadow: SHADOWS.floating,
          }}
        >
          <div
            style={{
              display: "inline-flex",
              padding: "8px 12px",
              borderRadius: RADII.pill,
              backgroundColor: COLORS.lavender,
              color: COLORS.brand,
              fontSize: 14,
              fontWeight: TYPOGRAPHY.weight.extraBold,
            }}
          >
            本轮表达证据
          </div>
          <div
            style={{
              marginTop: 28,
              color: COLORS.textPrimary,
              fontSize: 31,
              fontWeight: TYPOGRAPHY.weight.bold,
              lineHeight: 1.95,
            }}
          >
            老师您好，我正在准备研究生申请，想请您帮忙写一封推荐信。学校
            <EvidenceHighlight progress={timeHighlight}>
              截止时间是下月 15 日
            </EvidenceHighlight>
            ，我
            <EvidenceHighlight progress={materialHighlight}>
              已经整理好了项目清单
            </EvidenceHighlight>
            和
            <EvidenceHighlight progress={descriptionHighlight}>
              材料说明
            </EvidenceHighlight>
            。
          </div>
          <div
            style={{
              marginTop: 26,
              color: COLORS.textSecondary,
              fontSize: 16,
              lineHeight: 1.65,
            }}
          >
            清晰事实降低判断成本，具体准备降低额外工作量，也让对方更容易给出可执行回复。
          </div>
        </section>

        <div style={{display: "grid", gap: 14}}>
          <MetricDeltaCard
            label="对方信任"
            value={trust}
            delta={trust - 63}
            barPercent={trust}
            revealProgress={cardsProgress}
          />
          <MetricDeltaCard
            label="沟通意愿"
            value={willingness}
            delta={willingness - 58}
            barPercent={willingness}
            revealProgress={cardsProgress}
          />
          <MetricDeltaCard
            label="目标推进"
            value={progress}
            delta={progress - 41}
            barPercent={progress}
            revealProgress={cardsProgress}
          />
          <MetricDeltaCard
            label="压力"
            value={pressure}
            delta={pressure - 42}
            barPercent={pressure}
            revealProgress={cardsProgress}
          />
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 94,
          textAlign: "center",
          color: COLORS.textPrimary,
          fontSize: 46,
          fontWeight: TYPOGRAPHY.weight.extraBold,
          letterSpacing: "-0.035em",
          opacity: copyProgress,
          transform: `translateY(${16 * (1 - copyProgress)}px)`,
        }}
      >
        每一句话，都会改变对方的状态。
      </div>
    </AbsoluteFill>
  );
};
