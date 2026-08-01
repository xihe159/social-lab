import {Check} from "lucide-react";

import {
  COLORS,
  LAYOUT,
  RADII,
  TYPOGRAPHY,
} from "../../design/tokens";

type WorkflowStep = {
  number: number;
  title: string;
  description: string;
};

const STEPS: readonly WorkflowStep[] = [
  {
    number: 1,
    title: "场景",
    description: "定义沟通目标",
  },
  {
    number: 2,
    title: "对方",
    description: "补充对象信息",
  },
  {
    number: 3,
    title: "画像",
    description: "生成关系分身",
  },
  {
    number: 4,
    title: "模拟",
    description: "开始沟通练习",
  },
  {
    number: 5,
    title: "报告",
    description: "查看分析建议",
  },
];

export type WorkflowSidebarProps = {
  activeStep: number;
  progress?: number;
};

export const WorkflowSidebar = ({
  activeStep,
  progress = 1,
}: WorkflowSidebarProps) => {
  return (
    <aside
      style={{
        position: "absolute",
        inset: "0 auto 0 0",
        width: LAYOUT.sidebarWidth,
        boxSizing: "border-box",
        padding: "28px 24px",
        backgroundColor: COLORS.pageSoft,
        borderRight: `1px solid ${COLORS.border}`,
        opacity: progress,
        transform: `translateX(${-20 * (1 - progress)}px)`,
        fontFamily: TYPOGRAPHY.fontFamily,
        willChange: "transform, opacity",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 14,
        }}
      >
        <div
          style={{
            width: 46,
            height: 46,
            display: "grid",
            placeItems: "center",
            borderRadius: RADII.logo,
            backgroundColor: COLORS.brand,
            color: COLORS.surface,
            fontSize: 18,
            fontWeight: TYPOGRAPHY.weight.extraBold,
          }}
        >
          SL
        </div>

        <div>
          <div
            style={{
              color: COLORS.textPrimary,
              fontSize: 21,
              fontWeight: TYPOGRAPHY.weight.extraBold,
            }}
          >
            Social Lab
          </div>

          <div
            style={{
              marginTop: 4,
              color: COLORS.textSecondary,
              fontSize: 14,
              fontWeight: TYPOGRAPHY.weight.medium,
            }}
          >
            先演练，再开口
          </div>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gap: 10,
          marginTop: 44,
        }}
      >
        {STEPS.map((step) => {
          const isActive = step.number === activeStep;
          const isComplete = step.number < activeStep;

          return (
            <div
              key={step.number}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 14,
                minHeight: 68,
                boxSizing: "border-box",
                padding: "11px 13px",
                borderRadius: RADII.card,
                backgroundColor: isActive
                  ? COLORS.lavender
                  : "transparent",
              }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  flex: "0 0 auto",
                  display: "grid",
                  placeItems: "center",
                  borderRadius: 12,
                  backgroundColor:
                    isActive || isComplete
                      ? COLORS.lime
                      : COLORS.border,
                  color:
                    isActive || isComplete
                      ? COLORS.limeText
                      : COLORS.textMuted,
                  fontSize: 15,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                }}
              >
                {isComplete ? (
                  <Check size={18} strokeWidth={2.7} />
                ) : (
                  step.number
                )}
              </div>

              <div>
                <div
                  style={{
                    color: COLORS.textPrimary,
                    fontSize: 17,
                    fontWeight: TYPOGRAPHY.weight.bold,
                  }}
                >
                  {step.title}
                </div>

                <div
                  style={{
                    marginTop: 4,
                    color: COLORS.textSecondary,
                    fontSize: 13,
                    fontWeight: TYPOGRAPHY.weight.regular,
                  }}
                >
                  {step.description}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div
        style={{
          position: "absolute",
          left: 24,
          right: 24,
          bottom: 28,
          padding: 15,
          borderRadius: RADII.card,
          backgroundColor: COLORS.warningSoft,
          color: COLORS.textSecondary,
          fontSize: 13,
          lineHeight: 1.55,
        }}
      >
        视频使用固定演示数据，不包含真实用户隐私。
      </div>
    </aside>
  );
};
