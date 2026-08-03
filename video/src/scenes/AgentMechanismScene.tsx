import {Check} from "lucide-react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

import {AgentNode} from "../components/mechanism/AgentNode";
import {FlowParticle} from "../components/mechanism/FlowParticle";
import {MessageBubble} from "../components/product/MessageBubble";
import {demoSession} from "../data/demo-session";
import {COLORS, MOTION, RADII, SHADOWS, TYPOGRAPHY} from "../design/tokens";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1);

const AGENTS = [
  {
    title: "对象画像",
    subtitle: "Persona Agent",
    description: "还原对象的沟通偏好与关注重点",
    start: 18,
    complete: 46,
    tone: "lavender" as const,
  },
  {
    title: "回复模拟",
    subtitle: "Simulation Agent",
    description: "生成符合画像与关系状态的回应",
    start: 58,
    complete: 88,
    tone: "neutral" as const,
  },
  {
    title: "关系状态更新",
    subtitle: "State Agent",
    description: "根据本轮证据更新信任、压力与推进度",
    start: 104,
    complete: 136,
    tone: "lime" as const,
  },
  {
    title: "表达分析与结果预测",
    subtitle: "Prediction Agent",
    description: "解释关键影响并评估可能结果",
    start: 152,
    complete: 194,
    tone: "lavender" as const,
  },
] as const;

const FLOW_HEIGHT = 566;
const CARD_TOPS = [0, 144, 288, 432] as const;
const RAIL_X = 30;
const CARD_LEFT = 104;
const NODE_CENTERS = CARD_TOPS.map((top) => top + 62);

const completionMotion = (frame: number, completeAt: number) => {
  const y = interpolate(
    frame,
    [completeAt, completeAt + 4, completeAt + 9, completeAt + 14],
    [0, -8, 3, 0],
    CLAMP,
  );
  const scale = interpolate(
    frame,
    [completeAt, completeAt + 4, completeAt + 9, completeAt + 14],
    [1, 1.026, 0.995, 1],
    CLAMP,
  );

  return {y, scale};
};

const getAgentProgress = (
  frame: number,
  start: number,
  complete: number,
): number =>
  interpolate(frame, [start, complete], [0, 1], {
    ...CLAMP,
    easing: EASE_OUT,
  });

const AgentCard = ({
  frame,
  agent,
  index,
}: Readonly<{
  frame: number;
  agent: (typeof AGENTS)[number];
  index: number;
}>) => {
  const entry = interpolate(
    frame,
    [agent.start - 7, agent.start + 10],
    [0, 1],
    {...CLAMP, easing: EASE_OUT},
  );
  const progress = getAgentProgress(frame, agent.start, agent.complete);
  const started = frame >= agent.start;
  const completed = frame >= agent.complete;
  const completion = completionMotion(frame, agent.complete);
  const status = completed ? "已完成" : started ? "分析中" : "等待中";

  return (
    <div
      style={{
        position: "absolute",
        left: CARD_LEFT,
        right: 0,
        top: CARD_TOPS[index],
        zIndex: 2,
        opacity: entry,
        transform: `translateX(${18 * (1 - entry)}px) translateY(${completion.y}px) scale(${completion.scale})`,
        transformOrigin: "center left",
        willChange: "transform, opacity",
      }}
    >
      <AgentNode
        title={agent.title}
        subtitle={agent.subtitle}
        progress={progress}
        tone={agent.tone}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0, 1fr) 88px",
            alignItems: "end",
            gap: 18,
          }}
        >
          <div>
            <div
              style={{
                color: COLORS.textSecondary,
                fontSize: 13,
                fontWeight: TYPOGRAPHY.weight.bold,
                lineHeight: 1.45,
              }}
            >
              {agent.description}
            </div>
            <div
              style={{
                height: 6,
                marginTop: 10,
                overflow: "hidden",
                borderRadius: 999,
                backgroundColor: COLORS.border,
              }}
            >
              <div
                style={{
                  width: `${progress * 100}%`,
                  height: "100%",
                  borderRadius: 999,
                  background: completed
                    ? `linear-gradient(90deg, ${COLORS.cta}, ${COLORS.lime})`
                    : COLORS.brand,
                }}
              />
            </div>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-end",
              gap: 8,
              color: completed
                ? COLORS.optionSelectedText
                : started
                  ? COLORS.brand
                  : COLORS.textMuted,
              fontSize: 12,
              fontWeight: TYPOGRAPHY.weight.extraBold,
            }}
          >
            <span
              style={{
                width: 26,
                height: 26,
                display: "grid",
                placeItems: "center",
                borderRadius: 999,
                border: `1px solid ${
                  completed ? COLORS.optionSelectedBorder : COLORS.border
                }`,
                backgroundColor: completed ? COLORS.lime : COLORS.pageSoft,
                color: completed ? COLORS.limeText : COLORS.textMuted,
              }}
            >
              {completed ? <Check size={16} strokeWidth={2.8} /> : index + 1}
            </span>
            {status}
          </div>
        </div>
      </AgentNode>
    </div>
  );
};

const VerticalAgentFlow = ({frame}: Readonly<{frame: number}>) => {
  const particleY = interpolate(
    frame,
    [
      AGENTS[0].start,
      AGENTS[0].complete,
      AGENTS[1].start,
      AGENTS[1].complete,
      AGENTS[2].start,
      AGENTS[2].complete,
      AGENTS[3].start,
      AGENTS[3].complete,
    ],
    [
      NODE_CENTERS[0],
      NODE_CENTERS[0],
      NODE_CENTERS[1],
      NODE_CENTERS[1],
      NODE_CENTERS[2],
      NODE_CENTERS[2],
      NODE_CENTERS[3],
      NODE_CENTERS[3],
    ],
    CLAMP,
  );
  const particleOpacity = interpolate(
    frame,
    [AGENTS[0].start - 4, AGENTS[0].start + 4, AGENTS[3].complete, AGENTS[3].complete + 10],
    [0, 1, 1, 0],
    CLAMP,
  );

  return (
    <div
      style={{
        position: "relative",
        height: FLOW_HEIGHT,
        marginTop: 20,
      }}
    >
      <svg
        width="100%"
        height={FLOW_HEIGHT}
        style={{
          position: "absolute",
          inset: 0,
          zIndex: 1,
          overflow: "visible",
        }}
      >
        {AGENTS.slice(0, -1).map((agent, index) => {
          const nextAgent = AGENTS[index + 1];
          const progress = interpolate(
            frame,
            [agent.complete - 2, nextAgent.start + 8],
            [0, 1],
            {...CLAMP, easing: EASE_OUT},
          );
          const y1 = NODE_CENTERS[index] + 18;
          const y2 = NODE_CENTERS[index + 1] - 18;

          return (
            <line
              key={agent.subtitle}
              x1={RAIL_X}
              x2={RAIL_X}
              y1={y1}
              y2={y2}
              stroke={COLORS.mechanismLine}
              strokeWidth={3}
              strokeLinecap="round"
              pathLength={1}
              strokeDasharray={1}
              strokeDashoffset={1 - progress}
            />
          );
        })}

        {AGENTS.map((agent, index) => {
          const entry = interpolate(
            frame,
            [agent.start - 7, agent.start + 8],
            [0, 1],
            {...CLAMP, easing: EASE_OUT},
          );
          const completed = frame >= agent.complete;

          return (
            <line
              key={`${agent.subtitle}-bridge`}
              x1={RAIL_X + 16}
              x2={CARD_LEFT - 18}
              y1={NODE_CENTERS[index]}
              y2={NODE_CENTERS[index]}
              stroke={
                completed ? COLORS.optionSelectedBorder : COLORS.mechanismLine
              }
              strokeWidth={2}
              strokeLinecap="round"
              opacity={entry}
            />
          );
        })}

        {AGENTS.map((agent, index) => {
          const entry = interpolate(
            frame,
            [agent.start - 7, agent.start + 8],
            [0, 1],
            {...CLAMP, easing: EASE_OUT},
          );
          const completed = frame >= agent.complete;
          const completion = completionMotion(frame, agent.complete);

          return (
            <g
              key={agent.subtitle}
              transform={`translate(0 ${completion.y}) scale(${completion.scale})`}
              style={{transformOrigin: `${RAIL_X}px ${NODE_CENTERS[index]}px`}}
            >
              <circle
                cx={RAIL_X}
                cy={NODE_CENTERS[index]}
                r={16}
                fill={completed ? COLORS.lime : COLORS.surface}
                stroke={completed ? COLORS.optionSelectedBorder : COLORS.border}
                strokeWidth={2}
                opacity={entry}
              />
              <text
                x={RAIL_X}
                y={NODE_CENTERS[index] + 5}
                textAnchor="middle"
                fill={completed ? COLORS.limeText : COLORS.textMuted}
                fontSize={13}
                fontWeight={800}
                opacity={entry}
              >
                {completed ? "✓" : index + 1}
              </text>
            </g>
          );
        })}

        <FlowParticle x={RAIL_X} y={particleY} opacity={particleOpacity} />
      </svg>

      {AGENTS.map((agent, index) => (
        <AgentCard
          key={agent.subtitle}
          frame={frame}
          agent={agent}
          index={index}
        />
      ))}
    </div>
  );
};

export const AgentMechanismScene = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const panelProgress = spring({
    frame,
    fps,
    durationInFrames: 30,
    config: MOTION.cardSpring,
  });
  const contextProgress = spring({
    frame: frame - 6,
    fps,
    durationInFrames: 32,
    config: MOTION.gentleSpring,
  });
  const allDone = frame >= 214;
  const completeBounce = completionMotion(frame, 214);
  const completeProgress = interpolate(frame, [194, 218], [0, 1], {
    ...CLAMP,
    easing: EASE_OUT,
  });

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
          left: 92,
          top: 78,
          width: 650,
          opacity: contextProgress,
          transform: `translateX(${interpolate(contextProgress, [0, 1], [-28, 0], CLAMP)}px)`,
        }}
      >
        <div
          style={{
            color: COLORS.brand,
            fontSize: 16,
            fontWeight: TYPOGRAPHY.weight.extraBold,
            letterSpacing: "0.11em",
            textTransform: "uppercase",
          }}
        >
          Conversation Evidence
        </div>
        <div
          style={{
            marginTop: 10,
            fontSize: 42,
            fontWeight: TYPOGRAPHY.weight.extraBold,
            lineHeight: 1.08,
            letterSpacing: "-0.035em",
          }}
        >
          一次回应，如何被生成与判断
        </div>
      </div>

      <section
        style={{
          position: "absolute",
          left: 92,
          top: 205,
          width: 650,
          height: 650,
          boxSizing: "border-box",
          padding: 28,
          borderRadius: RADII.hero,
          border: `1px solid ${COLORS.border}`,
          backgroundColor: COLORS.surface,
          boxShadow: SHADOWS.floating,
          opacity: contextProgress,
          transform: `translateY(${18 * (1 - contextProgress)}px)`,
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
                fontSize: 28,
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

        <div style={{display: "grid", gap: 18, marginTop: 26}}>
          <MessageBubble role="user" text={demoSession.messages[0].text} compact />
          <MessageBubble role="target" text={demoSession.messages[1].text} compact />
        </div>

        <div
          style={{
            position: "absolute",
            left: 28,
            right: 28,
            bottom: 28,
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: 10,
          }}
        >
          {["对话证据", "对象画像", "关系状态"].map((label, index) => (
            <div
              key={label}
              style={{
                padding: "12px 10px",
                borderRadius: RADII.card,
                border: `1px solid ${COLORS.border}`,
                backgroundColor:
                  index === 1 ? COLORS.lavenderSurface : COLORS.pageSoft,
                color: index === 1 ? COLORS.brand : COLORS.textSecondary,
                textAlign: "center",
                fontSize: 13,
                fontWeight: TYPOGRAPHY.weight.extraBold,
              }}
            >
              {label}
            </div>
          ))}
        </div>
      </section>

      <section
        style={{
          position: "absolute",
          left: 790,
          right: 92,
          top: 72,
          height: 842,
          boxSizing: "border-box",
          padding: "30px 34px 28px",
          borderRadius: 28,
          border: `1px solid ${COLORS.border}`,
          backgroundColor: COLORS.mechanismPanel,
          boxShadow: SHADOWS.floating,
          opacity: panelProgress,
          transform: `translateX(${30 * (1 - panelProgress)}px)`,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
          }}
        >
          <div>
            <div
              style={{
                fontSize: 30,
                fontWeight: TYPOGRAPHY.weight.extraBold,
              }}
            >
              本轮模拟机制
            </div>
            <div
              style={{
                marginTop: 7,
                color: COLORS.textSecondary,
                fontSize: 15,
              }}
            >
              四个 Agent 纵向协作，逐步形成一次判断
            </div>
          </div>
          <span
            style={{
              padding: "8px 12px",
              borderRadius: RADII.pill,
              backgroundColor: allDone ? COLORS.limeSoft : COLORS.warningSoft,
              color: allDone
                ? COLORS.optionSelectedText
                : COLORS.textSecondary,
              fontSize: 13,
              fontWeight: TYPOGRAPHY.weight.extraBold,
            }}
          >
            {allDone ? "分析完成" : "多智能体协作中"}
          </span>
        </div>

        <VerticalAgentFlow frame={frame} />

        <div
          style={{
            position: "absolute",
            left: 34,
            right: 34,
            bottom: 26,
            height: 58,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 18,
            padding: "0 18px",
            borderRadius: RADII.card,
            border: `1px solid ${
              allDone ? COLORS.optionSelectedBorder : COLORS.border
            }`,
            backgroundColor: allDone ? COLORS.limeSoft : COLORS.surface,
            boxShadow: allDone
              ? "0 14px 34px rgba(79, 157, 122, 0.16)"
              : "none",
            opacity: interpolate(frame, [186, 204], [0, 1], CLAMP),
            transform: `translateY(${completeBounce.y}px) scale(${completeBounce.scale})`,
          }}
        >
          <div style={{display: "flex", alignItems: "center", gap: 12}}>
            <span
              style={{
                width: 30,
                height: 30,
                display: "grid",
                placeItems: "center",
                borderRadius: 999,
                backgroundColor: allDone ? COLORS.lime : COLORS.pageSoft,
                color: allDone ? COLORS.limeText : COLORS.textMuted,
              }}
            >
              {allDone ? <Check size={18} strokeWidth={2.8} /> : "…"}
            </span>
            <div>
              <div
                style={{
                  fontSize: 15,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                  color: allDone
                    ? COLORS.optionSelectedText
                    : COLORS.textPrimary,
                }}
              >
                {allDone ? "分析已完成" : "正在汇总分析"}
              </div>
              <div
                style={{
                  marginTop: 3,
                  color: COLORS.textSecondary,
                  fontSize: 12,
                  fontWeight: TYPOGRAPHY.weight.bold,
                }}
              >
                即将进入沟通结果与推荐写作
              </div>
            </div>
          </div>
          <div
            style={{
              width: 220,
              height: 8,
              overflow: "hidden",
              borderRadius: 999,
              backgroundColor: COLORS.border,
            }}
          >
            <div
              style={{
                width: `${completeProgress * 100}%`,
                height: "100%",
                borderRadius: 999,
                background: `linear-gradient(90deg, ${COLORS.cta}, ${COLORS.lime})`,
              }}
            />
          </div>
        </div>
      </section>
    </AbsoluteFill>
  );
};
