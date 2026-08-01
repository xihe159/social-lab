import {
  COLORS,
  RADII,
  SHADOWS,
  TYPOGRAPHY,
} from "../../design/tokens";

type ProbabilityBar = {
  width: number;
  color: string;
};

const probabilityBars: ProbabilityBar[] = [
  {
    width: 68,
    color: COLORS.previewBlue,
  },
  {
    width: 20,
    color: COLORS.previewAmber,
  },
  {
    width: 7,
    color: COLORS.previewRed,
  },
  {
    width: 5,
    color: COLORS.previewSlate,
  },
];

export type LandingPreviewCardProps = {
  cardProgress?: number;
  contentProgress?: number;
};

export const LandingPreviewCard = ({
  cardProgress = 1,
  contentProgress = 1,
}: LandingPreviewCardProps) => {
  return (
    <section
      style={{
        height: "100%",
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        gap: 20,
        padding: 26,
        border: `1px solid ${COLORS.border}`,
        borderRadius: 22,
        backgroundColor: COLORS.surface,
        boxShadow: SHADOWS.card,
        opacity: cardProgress,
        transform:
          `translateY(${14 * (1 - cardProgress)}px) ` +
          `scale(${0.992 + cardProgress * 0.008})`,
        willChange: "transform, opacity",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          minHeight: 58,
          paddingBottom: 17,
          borderBottom: `1px solid ${COLORS.border}`,
          opacity: contentProgress,
        }}
      >
        <span
          style={{
            color: COLORS.textSecondary,
            fontFamily: TYPOGRAPHY.fontFamily,
            fontSize: 18,
            fontWeight: TYPOGRAPHY.weight.medium,
          }}
        >
          本轮沟通成功率
        </span>

        <strong
          style={{
            color: COLORS.brand,
            fontFamily: TYPOGRAPHY.fontFamily,
            fontSize: 48,
            fontWeight: TYPOGRAPHY.weight.extraBold,
            lineHeight: 1,
          }}
        >
          68%
        </strong>
      </div>

      <div
        style={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: 14,
          opacity: contentProgress,
          transform:
            `translateY(${12 * (1 - contentProgress)}px)`,
        }}
      >
        <p
          style={{
            alignSelf: "flex-end",
            maxWidth: "82%",
            margin: 0,
            padding: "15px 18px",
            borderRadius: 18,
            backgroundColor: COLORS.lime,
            color: COLORS.limeText,
            fontFamily: TYPOGRAPHY.fontFamily,
            fontSize: 18,
            fontWeight: TYPOGRAPHY.weight.medium,
            lineHeight: 1.6,
          }}
        >
          老师您好，我想请您帮我写推荐信。
        </p>

        <p
          style={{
            alignSelf: "flex-start",
            maxWidth: "86%",
            margin: 0,
            padding: "15px 18px",
            borderRadius: 18,
            backgroundColor: COLORS.lavenderSurface,
            color: COLORS.textPrimary,
            fontFamily: TYPOGRAPHY.fontFamily,
            fontSize: 17,
            fontWeight: TYPOGRAPHY.weight.regular,
            lineHeight: 1.65,
          }}
        >
          你先把申请项目、截止时间和推荐信要求发给我，我看一下是否来得及安排。
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gap: 9,
          minHeight: 59,
          opacity: contentProgress,
        }}
      >
        {probabilityBars.map((bar, index) => {
          const delayedProgress = Math.max(
            0,
            Math.min(1, contentProgress * 1.2 - index * 0.06),
          );

          return (
            <div
              key={`${bar.color}-${bar.width}`}
              style={{
                width: `${bar.width * delayedProgress}%`,
                height: 8,
                borderRadius: RADII.pill,
                backgroundColor: bar.color,
              }}
            />
          );
        })}
      </div>
    </section>
  );
};
