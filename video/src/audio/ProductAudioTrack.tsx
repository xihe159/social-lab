import {Audio} from "@remotion/media";
import {useMemo} from "react";
import {useRemotionEnvironment} from "remotion";

import {
  productSoundCues,
  type SoundCue,
} from "./sound-cues";

type StudioAudioMode = "off" | "key" | "full";

/**
 * off：Studio 完全静音，不挂载 Audio
 * key：Studio 只播放关键音效
 * full：Studio 播放全部音效，可能导致卡顿
 */
const STUDIO_AUDIO_MODE: StudioAudioMode = "key";

const STUDIO_CUE_IDS = new Set<string>([
  "scene-02-match-cut",

  "scene-03-start-button-click",
  "scene-03-modal-open",
  "scene-03-mentor-click",
  "scene-03-mentor-selected",

  "scene-04-goal-click",
  "scene-04-urgency-click",
  "scene-04-text-focus",
  "scene-04-concern-click",

  "scene-05-page-enter",
  "scene-05-generate-click",
  "scene-05-generated",

  "scene-06-page-enter",
  "scene-06-strategy-ready",

  "scene-07-send-click",
  "scene-07-target-response",

  "scene-08-enter",
  "scene-08-mechanism-complete",

  "scene-09-enter",

  "scene-10-enter",
  "scene-10-score-complete",

  "scene-11-enter",
  "scene-11-retry-click",
  "scene-11-match-cut",

  "scene-12-enter",
  "scene-12-brand-settle",
]);

const getStudioSoundCues = (
  cues: readonly SoundCue[],
  mode: StudioAudioMode,
): readonly SoundCue[] => {
  switch (mode) {
    case "off":
      return [];

    case "full":
      return cues;

    case "key":
      return cues.filter((cue) =>
        STUDIO_CUE_IDS.has(cue.id),
      );

    default: {
      const exhaustiveCheck: never = mode;
      return exhaustiveCheck;
    }
  }
};

export const ProductAudioTrack = () => {
  const {isStudio} = useRemotionEnvironment();

  const studioSoundCues = useMemo(() => {
    return getStudioSoundCues(
      productSoundCues,
      STUDIO_AUDIO_MODE,
    );
  }, []);

  const activeSoundCues = isStudio
    ? studioSoundCues
    : productSoundCues;

  if (activeSoundCues.length === 0) {
    return null;
  }

  return (
    <>
      {activeSoundCues.map((cue) => {
        return (
          <Audio
            key={cue.id}
            name={`SFX · ${cue.id}`}
            src={cue.src}
            from={cue.frame}
            durationInFrames={cue.durationInFrames}
            volume={() => cue.volume}
            playbackRate={cue.playbackRate ?? 1}
            showInTimeline={false}
          />
        );
      })}
    </>
  );
};
