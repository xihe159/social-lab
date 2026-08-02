import {Audio} from "@remotion/media";
import {staticFile, useRemotionEnvironment} from "remotion";

import {PRODUCT_FILM_DURATION} from "../timeline/product-film";
import {
  resolveProductBgmSettings,
  type ProductBgmSettingsInput,
} from "./bgm-settings";

export type ProductBgmTrackProps = Readonly<{
  settings?: ProductBgmSettingsInput;
}>;

const clamp01 = (value: number): number => {
  return Math.min(1, Math.max(0, value));
};

const isRemoteOrBrowserUrl = (src: string): boolean => {
  return /^(https?:|data:|blob:)/i.test(src);
};

export const resolveBgmSource = (src: string): string => {
  if (isRemoteOrBrowserUrl(src)) {
    return src;
  }

  return staticFile(src.replace(/^\/+/, ""));
};

export const ProductBgmTrack = ({settings: settingsInput}: ProductBgmTrackProps) => {
  const {isStudio} = useRemotionEnvironment();
  const settings = resolveProductBgmSettings(settingsInput);

  if (!settings.enabled) {
    return null;
  }

  return (
    <Audio
      src={resolveBgmSource(settings.src)}
      durationInFrames={PRODUCT_FILM_DURATION}
      trimBefore={settings.trimBeforeFrames}
      loop={settings.loop}
      loopVolumeCurveBehavior="extend"
      playbackRate={settings.playbackRate}
      muted={isStudio && settings.muteInStudio}
      showInTimeline={settings.showInTimeline}
      name="BGM · Product Film"
      volume={(frame) => {
        const fadeIn =
          settings.fadeInFrames === 0
            ? 1
            : clamp01(frame / settings.fadeInFrames);
        const framesRemaining = PRODUCT_FILM_DURATION - 1 - frame;
        const fadeOut =
          settings.fadeOutFrames === 0
            ? 1
            : clamp01(framesRemaining / settings.fadeOutFrames);

        return settings.volume * Math.min(fadeIn, fadeOut);
      }}
      onError={() => "fail"}
    />
  );
};
