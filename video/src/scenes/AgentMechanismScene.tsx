import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

import {AgentEdge} from "../components/mechanism/AgentEdge";
import {AgentNode} from "../components/mechanism/AgentNode";
import {FlowParticle} from "../components/mechanism/FlowParticle";
import {MessageBubble} from "../components/product/MessageBubble";
import {demoSession} from "../data/demo-session";
import {COLORS, MOTION, RADII, SHADOWS, TYPOGRAPHY} from "../design/tokens";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const nodePulse = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, start + 8, end - 8, end], [0, 1, 1, 0], CLAMP);

export const AgentMechanismScene = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const panelProgress =
    frame < 24
      ? 0
      : spring({
          frame: frame - 24,
          fps,
          durationInFrames: 36,
          config: MOTION.cardSpring,
        });

  const chatScale = interpolate(frame, [0, 32], [1, 0.78], CLAMP);
  const chatX = interpolate(frame, [0, 32], [0, -342], CLAMP);
  const edgeProgress = interpolate(frame, [52, 86], [0, 1], CLAMP);

  const node1 = nodePulse(frame, 60, 92);
  const node2 = nodePulse(frame, 92, 124);
  const node3 = nodePulse(frame, 124, 164);
  const node4 = nodePulse(frame, 164, 214);

  const particleY = interpolate(
    frame,
    [60, 92, 124, 164, 204],
    [118, 118, 234, 350, 466],
    CLAMP,
  );
  const particleOpacity = interpolate(frame, [56, 66, 204, 214], [0, 1, 1, 0], CLAMP);
  const metricTagsProgress = interpolate(frame, [132, 148], [0, 1], CLAMP);
  const basisProgress = interpolate(frame, [176, 196], [0, 1], CLAMP);

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
          position: "absolute",
          left: "50%",
          top: 120,
          width: 840,
          height: 690,
          transform: `translateX(-50%) translateX(${chatX}px) scale(${chatScale})`,
          transformOrigin: "center",
        }}
      >
        <div
          style={{
            height: "100%",
            boxSizing: "border-box",
            padding: 28,
            borderRadius: RADII.hero,
            border: `1px solid ${COLORS.border}`,
            backgroundColor: COLORS.surface,
            boxShadow: SHADOWS.floating,
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              paddingBottom: 18,
              borderBottom: `1px solid ${COLORS.border}`,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 30,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                }}
              >
                与研究生导师模拟沟通
              </div>
              <div
                style={{
                  marginTop: 7,
                  color: COLORS.textSecondary,
                  fontSize: 15,
                }}
              >
                当前态度：谨慎
              </div>
            </div>
            <span
              style={{
                padding: "8px 12px",
                borderRadius: RADII.pill,
                backgroundColor: COLORS.lavender,
                color: COLORS.brand,
                fontSize: 13,
                fontWeight: TYPOGRAPHY.weight.bold,
              }}
            >
              材料完整性与时间安排
            </span>
          </div>
          <div style={{display: "grid", gap: 18, marginTop: 28}}>
            <MessageBubble role="user" text={demoSession.messages[0].text} compact />
            <MessageBubble role="target" text={demoSession.messages[1].text} compact />
          </div>
        </div>
      </div>

      <section
        style={{
          position: "absolute",
          right: 120,
          top: 105,
          width: 700,
          height: 760,
          boxSizing: "border-box",
          padding: "28px 30px",
          borderRadius: RADII.hero,
          border: `1px solid ${COLORS.border}`,
          backgroundColor: COLORS.mechanismPanel,
          boxShadow: SHADOWS.floating,
          opacity: panelProgress,
          transform: `translateX(${28 * (1 - panelProgress)}px)`,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <div
              style={{
                fontSize: 27,
                fontWeight: TYPOGRAPHY.weight.extraBold,
              }}
            >
              本轮模拟机制
            </div>
            <div
              style={{
                marginTop: 6,
                color: COLORS.textSecondary,
                fontSize: 15,
              }}
            >
              从对象画像到关系更新与报告依据
            </div>
          </div>
          <span
            style={{
              padding: "7px 11px",
              borderRadius: RADII.pill,
              backgroundColor: COLORS.warningSoft,
              color: COLORS.textSecondary,
              fontSize: 13,
              fontWeight: TYPOGRAPHY.weight.bold,
            }}
          >
            机制示意
          </span>
        </div>

        <div style={{position: "relative", height: 580, marginTop: 26}}>
          <svg
            width="100%"
            height="580"
            viewBox="0 0 640 580"
            style={{position: "absolute", inset: 0, overflow: "visible"}}
          >
            <AgentEdge x={320} y1={96} y2={146} progress={edgeProgress} />
            <AgentEdge x={320} y1={212} y2={262} progress={edgeProgress} />
            <AgentEdge x={320} y1={328} y2={378} progress={edgeProgress} />
            <FlowParticle x={320} y={particleY} opacity={particleOpacity} />
          </svg>

          <div style={{position: "absolute", left: 90, right: 90, top: 0}}>
            <AgentNode
              title="对象画像"
              subtitle="Persona"
              progress={node1}
              tone="lavender"
            />
          </div>
          <div style={{position: "absolute", left: 90, right: 90, top: 116}}>
            <AgentNode
              title="回复模拟"
              subtitle="Simulation"
              progress={node2}
            />
          </div>
          <div style={{position: "absolute", left: 90, right: 90, top: 232}}>
            <AgentNode
              title="关系状态更新"
              subtitle="State"
              progress={node3}
              tone="lime"
            >
              <div
                style={{
                  display: "flex",
                  gap: 8,
                  opacity: metricTagsProgress,
                }}
              >
                {['信任 +3', '压力 -2', '推进 +4'].map((tag) => (
                  <span
                    key={tag}
                    style={{
                      padding: "6px 9px",
                      borderRadius: RADII.pill,
                      backgroundColor: COLORS.surface,
                      color: COLORS.optionSelectedText,
                      fontSize: 12,
                      fontWeight: TYPOGRAPHY.weight.extraBold,
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </AgentNode>
          </div>
          <div style={{position: "absolute", left: 90, right: 90, top: 348}}>
            <AgentNode
              title="表达分析与结果预测"
              subtitle="Analysis · Prediction"
              progress={node4}
              tone="lavender"
            >
              <div
                style={{
                  color: COLORS.textSecondary,
                  fontSize: 13,
                  fontWeight: TYPOGRAPHY.weight.bold,
                  opacity: basisProgress,
                }}
              >
                为报告中的关键影响、预测范围与下一步提供依据
              </div>
            </AgentNode>
          </div>
        </div>
      </section>
    </AbsoluteFill>
  );
};
