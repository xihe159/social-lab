import {
  ArrowRight,
  Check,
  Copy,
  RotateCcw,
  Send,
  Sparkles,
} from "lucide-react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

import {
  AnimatedCursor,
  type CursorPoint,
} from "../components/motion/AnimatedCursor";
import {demoSession} from "../data/demo-session";
import {COLORS, MOTION, RADII, SHADOWS, TYPOGRAPHY} from "../design/tokens";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1);
const REWRITE = demoSession.report.rewrite;

const REWRITE_SEGMENTS = [
  "老师您好，我整理了目前最确定的发现、对应依据，",
  "以及现在仍不能确定的部分。",
  "想请您帮我判断，下一步最值得优先验证哪一项。",
] as const;

const STRATEGY_OPTIONS = [
  {label: "保留事实", detail: "先说明已经完成了什么"},
  {label: "标注边界", detail: "区分判断与尚未确认之处"},
  {label: "收束请求", detail: "只提出一个可回答的问题"},
] as const;

const RESULT_METRICS = [
  {label: "表达清晰度", value: "+18"},
  {label: "回复意愿", value: "+12"},
  {label: "下一步明确度", value: "+21"},
] as const;

const appear = (frame: number, start: number, duration = 14) =>
  interpolate(frame, [start, start + duration], [0, 1], {
    ...CLAMP,
    easing: EASE_OUT,
  });

const ProductPill = ({children}: Readonly<{children: string}>) => (
  <span
    style={{
      display: "inline-flex",
      alignItems: "center",
      padding: "8px 12px",
      borderRadius: RADII.pill,
      backgroundColor: COLORS.limeSoft,
      color: COLORS.optionSelectedText,
      fontSize: 13,
      fontWeight: TYPOGRAPHY.weight.extraBold,
    }}
  >
    {children}
  </span>
);

export const RewriteRetryScene = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const workbenchProgress = spring({
    frame,
    fps,
    durationInFrames: 28,
    config: MOTION.cardSpring,
  });
  const previewProgress = spring({
    frame: frame - 8,
    fps,
    durationInFrames: 30,
    config: MOTION.gentleSpring,
  });

  const segment1 = appear(frame, 28, 14);
  const segment2 = appear(frame, 42, 14);
  const segment3 = appear(frame, 56, 14);
  const buttonPress = interpolate(frame, [100, 105, 111], [0, 1, 0], CLAMP);
  const retryProgress = interpolate(frame, [108, 128], [0, 1], {
    ...CLAMP,
    easing: EASE_OUT,
  });
  const chatOpacity = interpolate(frame, [112, 128], [0, 1], CLAMP);
  const summaryOpacity = interpolate(frame, [104, 124], [1, 0], CLAMP);
  const composerFill = interpolate(frame, [116, 138], [0, 1], CLAMP);
  const sendPress = interpolate(frame, [138, 142, 147], [0, 1, 0], CLAMP);
  const userBubble = appear(frame, 145, 12);
  const typingOpacity = interpolate(frame, [154, 162, 174, 178], [0, 1, 1, 0], CLAMP);
  const targetBubble = appear(frame, 174, 12);
  const resultProgress = appear(frame, 184, 16);
  const loopProgress = appear(frame, Math.min(198, durationInFrames - 12), 10);

  const cursorPoints: readonly CursorPoint[] = [
    {frame: 0, x: 1760, y: 930},
    {frame: 72, x: 900, y: 830},
    {frame: 100, x: 900, y: 830},
    {frame: 118, x: 1550, y: 790},
    {frame: 138, x: 1665, y: 790},
    {frame: Math.max(139, durationInFrames - 1), x: 1665, y: 790},
  ];

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
          right: 92,
          top: 50,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div>
          <div
            style={{
              color: COLORS.brand,
              fontSize: 16,
              fontWeight: TYPOGRAPHY.weight.extraBold,
              letterSpacing: "0.12em",
              textTransform: "uppercase",
            }}
          >
            Rewrite → Retry
          </div>
          <div
            style={{
              marginTop: 8,
              fontSize: 42,
              fontWeight: TYPOGRAPHY.weight.extraBold,
              letterSpacing: "-0.04em",
            }}
          >
            推荐写作，不止给出一句话
          </div>
        </div>
        <div style={{display: "flex", alignItems: "center", gap: 10}}>
          <ProductPill>场景与画像保持不变</ProductPill>
          <ProductPill>可直接继续模拟</ProductPill>
        </div>
      </div>

      <section
        style={{
          position: "absolute",
          left: 92,
          top: 150,
          width: 1040,
          height: 820,
          boxSizing: "border-box",
          padding: "30px 32px",
          borderRadius: 28,
          border: `1px solid ${COLORS.border}`,
          backgroundColor: COLORS.surface,
          boxShadow: SHADOWS.floating,
          opacity: workbenchProgress,
          transform: `translateY(${18 * (1 - workbenchProgress)}px)`,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{display: "flex", alignItems: "center", gap: 12}}>
            <span
              style={{
                width: 42,
                height: 42,
                display: "grid",
                placeItems: "center",
                borderRadius: 14,
                backgroundColor: COLORS.lavender,
                color: COLORS.brand,
              }}
            >
              <Sparkles size={22} strokeWidth={2.3} />
            </span>
            <div>
              <div
                style={{
                  fontSize: 25,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                }}
              >
                AI 推荐写作工作台
              </div>
              <div
                style={{
                  marginTop: 4,
                  color: COLORS.textSecondary,
                  fontSize: 14,
                  fontWeight: TYPOGRAPHY.weight.bold,
                }}
              >
                从原句问题，到结构重写，再到下一轮验证
              </div>
            </div>
          </div>
          <span
            style={{
              padding: "8px 12px",
              borderRadius: RADII.pill,
              backgroundColor: COLORS.pageSoft,
              color: COLORS.textSecondary,
              fontSize: 13,
              fontWeight: TYPOGRAPHY.weight.extraBold,
            }}
          >
            基于本轮报告生成
          </span>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "0.92fr 1.45fr",
            gap: 18,
            marginTop: 24,
          }}
        >
          <div
            style={{
              padding: "20px 20px",
              borderRadius: RADII.card,
              border: `1px solid ${COLORS.border}`,
              backgroundColor: COLORS.pageSoft,
            }}
          >
            <div
              style={{
                color: COLORS.textSecondary,
                fontSize: 13,
                fontWeight: TYPOGRAPHY.weight.extraBold,
              }}
            >
              原表达诊断
            </div>
            <div
              style={{
                marginTop: 12,
                fontSize: 17,
                fontWeight: TYPOGRAPHY.weight.bold,
                lineHeight: 1.65,
              }}
            >
              “我整理了目前的阶段结果，也想确认下一步应该优先推进什么。”
            </div>
            <div style={{display: "flex", flexWrap: "wrap", gap: 8, marginTop: 16}}>
              {["依据不够具体", "判断边界不清", "请求范围偏大"].map((label, index) => (
                <span
                  key={label}
                  style={{
                    padding: "7px 10px",
                    borderRadius: RADII.pill,
                    backgroundColor: index === 1 ? COLORS.warningSoft : COLORS.riskSoft,
                    color: COLORS.textSecondary,
                    fontSize: 12,
                    fontWeight: TYPOGRAPHY.weight.extraBold,
                    opacity: appear(frame, 12 + index * 8, 10),
                  }}
                >
                  {label}
                </span>
              ))}
            </div>
          </div>

          <div
            style={{
              padding: "20px 22px",
              borderRadius: RADII.card,
              border: `1px solid ${COLORS.optionSelectedBorder}`,
              background: `linear-gradient(135deg, ${COLORS.lavenderSurface}, ${COLORS.limeSoft})`,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div
                style={{
                  color: COLORS.brand,
                  fontSize: 14,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                }}
              >
                最推荐表达
              </div>
              <Copy size={17} color={COLORS.brand} strokeWidth={2.2} />
            </div>
            <div
              style={{
                marginTop: 12,
                minHeight: 108,
                color: COLORS.textPrimary,
                fontSize: 18,
                fontWeight: TYPOGRAPHY.weight.semibold,
                lineHeight: 1.72,
              }}
            >
              <span style={{opacity: segment1}}>{REWRITE_SEGMENTS[0]}</span>{" "}
              <span style={{opacity: segment2}}>{REWRITE_SEGMENTS[1]}</span>{" "}
              <span style={{opacity: segment3}}>{REWRITE_SEGMENTS[2]}</span>
            </div>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: 12,
            marginTop: 18,
          }}
        >
          {STRATEGY_OPTIONS.map((option, index) => {
            const progress = appear(frame, 48 + index * 10, 12);
            return (
              <div
                key={option.label}
                style={{
                  padding: "16px 16px",
                  borderRadius: RADII.card,
                  border: `1px solid ${index === 2 ? COLORS.optionSelectedBorder : COLORS.border}`,
                  backgroundColor: index === 2 ? COLORS.optionSelected : COLORS.surface,
                  opacity: progress,
                  transform: `translateY(${8 * (1 - progress)}px)`,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    color: index === 2 ? COLORS.optionSelectedText : COLORS.textPrimary,
                    fontSize: 15,
                    fontWeight: TYPOGRAPHY.weight.extraBold,
                  }}
                >
                  <Check size={16} strokeWidth={2.6} />
                  {option.label}
                </div>
                <div
                  style={{
                    marginTop: 7,
                    color: COLORS.textSecondary,
                    fontSize: 12,
                    fontWeight: TYPOGRAPHY.weight.bold,
                    lineHeight: 1.45,
                  }}
                >
                  {option.detail}
                </div>
              </div>
            );
          })}
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 20,
            marginTop: 22,
            paddingTop: 20,
            borderTop: `1px solid ${COLORS.border}`,
          }}
        >
          <div
            style={{
              color: COLORS.textSecondary,
              fontSize: 14,
              fontWeight: TYPOGRAPHY.weight.bold,
              lineHeight: 1.55,
            }}
          >
            推荐表达仍可继续编辑。你保留最终决定权，AI 负责把下一步变得可执行。
          </div>
          <div
            style={{
              flex: "0 0 auto",
              height: 56,
              display: "inline-flex",
              alignItems: "center",
              gap: 10,
              padding: "0 22px",
              borderRadius: RADII.card,
              backgroundColor: COLORS.cta,
              color: COLORS.surface,
              boxShadow: SHADOWS.button,
              fontSize: 16,
              fontWeight: TYPOGRAPHY.weight.extraBold,
              transform: `scale(${1 - buttonPress * 0.035})`,
            }}
          >
            <RotateCcw size={19} strokeWidth={2.4} />
            用推荐版本继续模拟
            <ArrowRight size={18} strokeWidth={2.4} />
          </div>
        </div>
      </section>

      <section
        style={{
          position: "absolute",
          right: 92,
          top: 150,
          width: 650,
          height: 820,
          overflow: "hidden",
          borderRadius: 30,
          border: `1px solid ${COLORS.border}`,
          backgroundColor: COLORS.surface,
          boxShadow: SHADOWS.floating,
          opacity: previewProgress,
          transform: `translateY(${18 * (1 - previewProgress)}px)`,
        }}
      >
        <div
          style={{
            height: 76,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 24px",
            borderBottom: `1px solid ${COLORS.border}`,
            backgroundColor: COLORS.pageSoft,
          }}
        >
          <div>
            <div
              style={{
                fontSize: 20,
                fontWeight: TYPOGRAPHY.weight.extraBold,
              }}
            >
              与研究导师继续模拟
            </div>
            <div
              style={{
                marginTop: 4,
                color: COLORS.cta,
                fontSize: 12,
                fontWeight: TYPOGRAPHY.weight.extraBold,
              }}
            >
              推荐版本已带入
            </div>
          </div>
          <ProductPill>同一画像</ProductPill>
        </div>

        <div
          style={{
            position: "absolute",
            left: 24,
            right: 24,
            top: 104,
            opacity: summaryOpacity,
            transform: `translateY(${-28 * retryProgress}px)`,
          }}
        >
          <div
            style={{
              padding: "20px 20px",
              borderRadius: RADII.card,
              backgroundColor: COLORS.lavenderSurface,
              color: COLORS.brand,
              fontSize: 15,
              fontWeight: TYPOGRAPHY.weight.extraBold,
            }}
          >
            推荐表达已准备好
          </div>
          <div
            style={{
              display: "grid",
              gap: 12,
              marginTop: 16,
            }}
          >
            {["场景与关系背景保留", "对象画像继续生效", "结果可以与上一轮对比"].map((label) => (
              <div
                key={label}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "15px 16px",
                  borderRadius: RADII.card,
                  border: `1px solid ${COLORS.border}`,
                  color: COLORS.textSecondary,
                  fontSize: 14,
                  fontWeight: TYPOGRAPHY.weight.bold,
                }}
              >
                <Check size={17} color={COLORS.cta} strokeWidth={2.6} />
                {label}
              </div>
            ))}
          </div>
        </div>

        <div
          style={{
            position: "absolute",
            inset: "92px 20px 20px",
            opacity: chatOpacity,
          }}
        >
          <div
            style={{
              height: 470,
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
              justifyContent: "flex-end",
              gap: 14,
              padding: "0 4px 12px",
            }}
          >
            <div
              style={{
                alignSelf: "flex-end",
                maxWidth: "88%",
                padding: "14px 16px",
                borderRadius: "18px 18px 4px 18px",
                backgroundColor: COLORS.lime,
                color: COLORS.limeText,
                fontSize: 15,
                fontWeight: TYPOGRAPHY.weight.semibold,
                lineHeight: 1.58,
                opacity: userBubble,
                transform: `translateY(${8 * (1 - userBubble)}px)`,
              }}
            >
              {REWRITE_SEGMENTS.join("")}
            </div>

            <div
              style={{
                alignSelf: "flex-start",
                padding: "10px 14px",
                borderRadius: RADII.pill,
                backgroundColor: COLORS.pageSoft,
                color: COLORS.textSecondary,
                fontSize: 13,
                fontWeight: TYPOGRAPHY.weight.bold,
                opacity: typingOpacity,
              }}
            >
              对方正在输入中…
            </div>

            <div
              style={{
                alignSelf: "flex-start",
                maxWidth: "88%",
                padding: "14px 16px",
                borderRadius: "18px 18px 18px 4px",
                backgroundColor: COLORS.lavender,
                color: COLORS.textPrimary,
                fontSize: 15,
                fontWeight: TYPOGRAPHY.weight.semibold,
                lineHeight: 1.58,
                opacity: targetBubble,
                transform: `translateY(${8 * (1 - targetBubble)}px)`,
              }}
            >
              这个版本更清楚。先把这三部分发给我，我会根据证据帮你判断哪项验证最值得先做。
            </div>
          </div>

          <div
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              bottom: 0,
              minHeight: 82,
              display: "flex",
              alignItems: "flex-end",
              gap: 10,
              padding: "12px 12px",
              borderRadius: 22,
              border: `1px solid ${COLORS.border}`,
              backgroundColor: COLORS.surface,
              boxShadow: SHADOWS.card,
              opacity: 1 - resultProgress,
              transform: `translateY(${resultProgress * 18}px)`,
            }}
          >
            <div
              style={{
                flex: 1,
                minHeight: 48,
                color: COLORS.textPrimary,
                fontSize: 14,
                fontWeight: TYPOGRAPHY.weight.medium,
                lineHeight: 1.45,
                whiteSpace: "pre-wrap",
              }}
            >
              {REWRITE.slice(0, Math.max(0, Math.round(REWRITE.length * composerFill)))}
            </div>
            <div
              style={{
                width: 48,
                height: 48,
                display: "grid",
                placeItems: "center",
                borderRadius: 16,
                backgroundColor: COLORS.brand,
                color: COLORS.surface,
                transform: `scale(${1 - sendPress * 0.06})`,
              }}
            >
              <Send size={21} strokeWidth={2.4} />
            </div>
          </div>
        </div>

        <div
          style={{
            position: "absolute",
            left: 20,
            right: 20,
            bottom: 20,
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: 10,
            opacity: resultProgress,
            transform: `translateY(${16 * (1 - resultProgress)}px)`,
            pointerEvents: "none",
          }}
        >
          {RESULT_METRICS.map((metric, index) => (
            <div
              key={metric.label}
              style={{
                padding: "14px 12px",
                borderRadius: RADII.card,
                border: `1px solid ${COLORS.optionSelectedBorder}`,
                backgroundColor: index === 0 ? COLORS.limeSoft : COLORS.surface,
                textAlign: "center",
                boxShadow: SHADOWS.card,
              }}
            >
              <div
                style={{
                  color: COLORS.optionSelectedText,
                  fontSize: 24,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                }}
              >
                {metric.value}
              </div>
              <div
                style={{
                  marginTop: 4,
                  color: COLORS.textSecondary,
                  fontSize: 11,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                }}
              >
                {metric.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      <div
        style={{
          position: "absolute",
          left: "50%",
          bottom: 30,
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "10px 16px",
          borderRadius: RADII.pill,
          border: `1px solid ${COLORS.border}`,
          backgroundColor: "rgba(255,255,255,0.90)",
          color: COLORS.textSecondary,
          boxShadow: SHADOWS.card,
          opacity: loopProgress,
          transform: `translateX(-50%) translateY(${8 * (1 - loopProgress)}px)`,
          fontSize: 13,
          fontWeight: TYPOGRAPHY.weight.extraBold,
        }}
      >
        <span style={{color: COLORS.brand}}>报告洞察</span>
        <ArrowRight size={15} />
        <span style={{color: COLORS.brand}}>推荐写作</span>
        <ArrowRight size={15} />
        <span style={{color: COLORS.optionSelectedText}}>继续模拟</span>
        <ArrowRight size={15} />
        <span style={{color: COLORS.optionSelectedText}}>对比结果</span>
      </div>

      <AnimatedCursor
        points={cursorPoints}
        clicks={[
          {start: 100, end: 111},
          {start: 138, end: 147},
        ]}
        visibleFrom={70}
        visibleUntil={Math.min(durationInFrames - 1, 156)}
      />
    </AbsoluteFill>
  );
};
