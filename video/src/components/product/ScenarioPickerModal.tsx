import type {ComponentType} from "react";
import {
  BriefcaseBusiness,
  Check,
  GraduationCap,
  HandHeart,
} from "lucide-react";

import {
  COLORS,
  RADII,
  TYPOGRAPHY,
} from "../../design/tokens";

export type ScenarioId =
  | "mentor"
  | "workplace"
  | "social";

type ScenarioDefinition = {
  id: ScenarioId;
  title: string;
  description: string;
  Icon: ComponentType<{
    size?: number;
    strokeWidth?: number;
    color?: string;
  }>;
};

const SCENARIOS: readonly ScenarioDefinition[] = [
  {
    id: "mentor",
    title: "导师",
    description:
      "推荐信、课题沟通、学业安排与重要请求。",
    Icon: GraduationCap,
  },
  {
    id: "workplace",
    title: "职场",
    description:
      "反馈、协作、汇报、谈判与边界表达。",
    Icon: BriefcaseBusiness,
  },
  {
    id: "social",
    title: "社交",
    description:
      "朋友、家人、关系修复与困难话题。",
    Icon: HandHeart,
  },
];

export type ScenarioPickerModalProps = {
  modalProgress: number;
  labelProgress: number;
  cardProgresses: readonly [
    number,
    number,
    number,
  ];

  hoveredScenario?: ScenarioId;
  pressedScenario?: ScenarioId;
  selectedScenario?: ScenarioId;
};

const clamp01 = (value: number): number => {
  return Math.max(0, Math.min(1, value));
};

export const ScenarioPickerModal = ({
  modalProgress,
  labelProgress,
  cardProgresses,
  hoveredScenario,
  pressedScenario,
  selectedScenario,
}: ScenarioPickerModalProps) => {
  const safeModalProgress = clamp01(modalProgress);

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: "50%",
        zIndex: 100,
        width: 820,
        minHeight: 486,
        boxSizing: "border-box",
        padding: "68px 36px 38px",
        borderRadius: 28,
        backgroundColor: COLORS.modalDark,
        boxShadow:
          "0 38px 100px rgba(10, 12, 25, 0.34)",
        opacity: safeModalProgress,
        transform:
          `translate(-50%, -50%) ` +
          `translateY(${18 * (1 - safeModalProgress)}px) ` +
          `scale(${0.96 + safeModalProgress * 0.04})`,
        transformOrigin: "center center",
        fontFamily: TYPOGRAPHY.fontFamily,
        willChange: "transform, opacity",
      }}
    >
      {/* 黄色旋转标题 */}
      <div
        style={{
          position: "absolute",
          left: 48,
          top: -25,
          padding: "14px 24px",
          borderRadius: RADII.pill,
          backgroundColor: COLORS.modalYellow,
          color: COLORS.modalDark,
          fontSize: 23,
          fontWeight: TYPOGRAPHY.weight.extraBold,
          letterSpacing: "-0.01em",
          opacity: labelProgress,
          transform:
            `translateY(${12 * (1 - labelProgress)}px) ` +
            `rotate(-8deg)`,
          transformOrigin: "left center",
          whiteSpace: "nowrap",
        }}
      >
        选择你的沟通场景
      </div>

      <div
        style={{
          marginBottom: 30,
          color: COLORS.surface,
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: 34,
            fontWeight: TYPOGRAPHY.weight.extraBold,
            letterSpacing: "-0.025em",
          }}
        >
          你准备和谁沟通？
        </h2>

        <p
          style={{
            margin: "12px 0 0",
            color: "rgba(255, 255, 255, 0.62)",
            fontSize: 18,
            fontWeight: TYPOGRAPHY.weight.regular,
            lineHeight: 1.6,
          }}
        >
          选择最接近的关系类型，让后续问题更贴近真实情境。
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
          gap: 18,
        }}
      >
        {SCENARIOS.map((scenario, index) => {
          const progress = clamp01(
            cardProgresses[index],
          );

          const isHovered =
            hoveredScenario === scenario.id;

          const isPressed =
            pressedScenario === scenario.id;

          const isSelected =
            selectedScenario === scenario.id;

          const hoverProgress =
            isHovered || isSelected ? 1 : 0;

          const scale = isPressed
            ? 0.985
            : 1 + hoverProgress * 0.012;

          const Icon = scenario.Icon;

          return (
            <div
              key={scenario.id}
              style={{
                position: "relative",
                minHeight: 238,
                boxSizing: "border-box",
                display: "flex",
                flexDirection: "column",
                padding: "24px 22px",
                borderRadius: 20,
                border:
                  `2px solid ${
                    hoverProgress > 0
                      ? COLORS.brand
                      : "transparent"
                  }`,
                backgroundColor:
                  hoverProgress > 0
                    ? COLORS.lavenderSurface
                    : "#F7F8FF",
                boxShadow:
                  hoverProgress > 0
                    ? "0 18px 36px rgba(8, 10, 24, 0.20)"
                    : "0 10px 26px rgba(8, 10, 24, 0.12)",
                opacity: progress,
                transform:
                  `translateY(${18 * (1 - progress)}px) ` +
                  `scale(${scale})`,
                transformOrigin: "center center",
                color: COLORS.textPrimary,
                willChange:
                  "transform, opacity, background-color",
              }}
            >
              {isSelected ? (
                <div
                  style={{
                    position: "absolute",
                    right: 16,
                    top: 16,
                    width: 28,
                    height: 28,
                    display: "grid",
                    placeItems: "center",
                    borderRadius: "50%",
                    backgroundColor: COLORS.brand,
                    color: COLORS.surface,
                  }}
                >
                  <Check
                    size={18}
                    strokeWidth={2.8}
                  />
                </div>
              ) : null}

              <div
                style={{
                  width: 54,
                  height: 54,
                  display: "grid",
                  placeItems: "center",
                  borderRadius: 16,
                  backgroundColor:
                    hoverProgress > 0
                      ? COLORS.limeSoft
                      : COLORS.lavender,
                  color: COLORS.brand,
                }}
              >
                <Icon
                  size={28}
                  strokeWidth={2.1}
                  color={COLORS.brand}
                />
              </div>

              <h3
                style={{
                  margin: "24px 0 10px",
                  fontSize: 24,
                  fontWeight: TYPOGRAPHY.weight.extraBold,
                  letterSpacing: "-0.015em",
                }}
              >
                {scenario.title}
              </h3>

              <p
                style={{
                  margin: 0,
                  color: COLORS.textSecondary,
                  fontSize: 17,
                  fontWeight: TYPOGRAPHY.weight.regular,
                  lineHeight: 1.65,
                }}
              >
                {scenario.description}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
