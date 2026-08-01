import {AbsoluteFill} from "remotion";

import {
  COLORS,
  LAYOUT,
  TYPOGRAPHY,
} from "../../design/tokens";
import {BrandSidebar} from "./BrandSidebar";
import {LandingHeroCard} from "./LandingHeroCard";
import {LandingPreviewCard} from "./LandingPreviewCard";

export type LandingPageMockProps = {
  sidebarProgress?: number;

  heroCardProgress?: number;
  badgeProgress?: number;
  titleProgress?: number;
  copyProgress?: number;
  buttonProgress?: number;
  buttonBreath?: number;

  previewCardProgress?: number;
  previewContentProgress?: number;
};

export const LandingPageMock = ({
  sidebarProgress = 1,

  heroCardProgress = 1,
  badgeProgress = 1,
  titleProgress = 1,
  copyProgress = 1,
  buttonProgress = 1,
  buttonBreath = 0,

  previewCardProgress = 1,
  previewContentProgress = 1,
}: LandingPageMockProps) => {
  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        backgroundColor: COLORS.page,
        color: COLORS.textPrimary,
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <BrandSidebar progress={sidebarProgress} />

      <main
        style={{
          position: "absolute",
          inset: `0 0 0 ${LAYOUT.sidebarWidth}px`,
          boxSizing: "border-box",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "54px 64px",
          backgroundColor: COLORS.page,
        }}
      >
        <div
          style={{
            width: LAYOUT.landingContentWidth,
            height: LAYOUT.landingHeroHeight,
            display: "grid",
            gridTemplateColumns:
              "minmax(0, 1.06fr) minmax(0, 0.94fr)",
            gap: 24,
            alignItems: "stretch",
          }}
        >
          <LandingHeroCard
            cardProgress={heroCardProgress}
            badgeProgress={badgeProgress}
            titleProgress={titleProgress}
            copyProgress={copyProgress}
            buttonProgress={buttonProgress}
            buttonBreath={buttonBreath}
          />

          <LandingPreviewCard
            cardProgress={previewCardProgress}
            contentProgress={previewContentProgress}
          />
        </div>
      </main>
    </AbsoluteFill>
  );
};
