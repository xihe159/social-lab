import {
  COLORS,
  LAYOUT,
  RADII,
  TYPOGRAPHY,
} from "../../design/tokens";

export type BrandSidebarProps = {
  progress?: number;
};

export const BrandSidebar = ({
  progress = 1,
}: BrandSidebarProps) => {
  const opacity = progress;
  const translateX = -24 * (1 - progress);

  return (
    <aside
      style={{
        position: "absolute",
        inset: "0 auto 0 0",
        width: LAYOUT.sidebarWidth,
        boxSizing: "border-box",
        padding: 28,
        display: "flex",
        flexDirection: "column",
        backgroundColor: COLORS.pageSoft,
        borderRight: `1px solid ${COLORS.border}`,
        opacity,
        transform: `translateX(${translateX}px)`,
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
            flex: "0 0 auto",
            display: "grid",
            placeItems: "center",
            borderRadius: RADII.logo,
            backgroundColor: COLORS.brand,
            color: COLORS.surface,
            fontFamily: TYPOGRAPHY.fontFamily,
            fontSize: 18,
            fontWeight: TYPOGRAPHY.weight.extraBold,
          }}
        >
          SL
        </div>

        <div>
          <strong
            style={{
              display: "block",
              color: COLORS.textPrimary,
              fontFamily: TYPOGRAPHY.fontFamily,
              fontSize: 21,
              fontWeight: TYPOGRAPHY.weight.extraBold,
              lineHeight: 1.2,
            }}
          >
            Social Lab
          </strong>

          <span
            style={{
              display: "block",
              marginTop: 4,
              color: COLORS.textSecondary,
              fontFamily: TYPOGRAPHY.fontFamily,
              fontSize: 14,
              fontWeight: TYPOGRAPHY.weight.medium,
            }}
          >
            先演练，再开口
          </span>
        </div>
      </div>

      <div
        style={{
          width: 70,
          height: 3,
          marginTop: 34,
          borderRadius: RADII.pill,
          backgroundColor: COLORS.lime,
        }}
      />
    </aside>
  );
};

