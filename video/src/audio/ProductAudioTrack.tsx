import {Audio} from "@remotion/media";
import {Sequence, useRemotionEnvironment} from "remotion";

import {timeline} from "../timeline/product-film";
import {
  resolveProductAudioSettings,
  type ProductAudioSettingsInput,
} from "./audio-settings";
import {productSoundCues, type SoundCue} from "./sound-cues";
import {resolveSoundSource} from "./sound-library";

export type ProductAudioTrackProps = Readonly<{
  settings?: ProductAudioSettingsInput;
}>;

type TimelineSceneKey = keyof typeof timeline;

type AudioSceneTrackDefinition = Readonly<{
  idPrefix: `scene-${string}`;
  timelineKey: TimelineSceneKey;
  label: string;
}>;

/**
 * 音效按 Scene 建立稳定父级音轨。
 *
 * 之前每个 cue 都是根节点下的独立 Sequence，同时 Audio 默认被
 * showInTimeline=false 隐藏。对于只有两个短 cue 的 Scene 02，Studio
 * 时间轴上会看起来像整个 Scene 02 音轨消失。
 *
 * 现在 12 个 Scene 都有固定父级 Sequence；单条 Audio 是否展示仍由
 * showInTimeline 控制，音频渲染结果不受时间轴 UI 影响。
 */
const AUDIO_SCENE_TRACKS = [
  {
    idPrefix: "scene-01",
    timelineKey: "unsent",
    label: "Scene 01 - Unsent Message",
  },
  {
    idPrefix: "scene-02",
    timelineKey: "landing",
    label: "Scene 02 - Brand Landing",
  },
  {
    idPrefix: "scene-03",
    timelineKey: "picker",
    label: "Scene 03 - Scenario Picker",
  },
  {
    idPrefix: "scene-04",
    timelineKey: "scenarioForm",
    label: "Scene 04 - Scenario Form",
  },
  {
    idPrefix: "scene-05",
    timelineKey: "personSetup",
    label: "Scene 05 - Person Setup",
  },
  {
    idPrefix: "scene-06",
    timelineKey: "persona",
    label: "Scene 06 - Persona Reveal",
  },
  {
    idPrefix: "scene-07",
    timelineKey: "conversation",
    label: "Scene 07 - Conversation",
  },
  {
    idPrefix: "scene-08",
    timelineKey: "mechanism",
    label: "Scene 08 - Agent Mechanism",
  },
  {
    idPrefix: "scene-09",
    timelineKey: "dynamics",
    label: "Scene 09 - Dynamics",
  },
  {
    idPrefix: "scene-10",
    timelineKey: "report",
    label: "Scene 10 - Report Overview",
  },
  {
    idPrefix: "scene-11",
    timelineKey: "rewrite",
    label: "Scene 11 - Rewrite and Retry",
  },
  {
    idPrefix: "scene-12",
    timelineKey: "outro",
    label: "Scene 12 - Outro",
  },
] as const satisfies readonly AudioSceneTrackDefinition[];

const clamp01 = (value: number): number => {
  return Math.min(1, Math.max(0, value));
};

const getEnvelope = (localFrame: number, cue: SoundCue): number => {
  const fadeInFrames = Math.max(0, cue.fadeInFrames ?? 0);
  const fadeOutFrames = Math.max(0, cue.fadeOutFrames ?? 0);

  const fadeIn =
    fadeInFrames === 0 ? 1 : clamp01(localFrame / fadeInFrames);

  const remainingFrames = cue.durationInFrames - 1 - localFrame;
  const fadeOut =
    fadeOutFrames === 0
      ? 1
      : clamp01(remainingFrames / fadeOutFrames);

  return Math.min(fadeIn, fadeOut);
};

const belongsToScene = (
  cue: SoundCue,
  scene: AudioSceneTrackDefinition,
): boolean => {
  return cue.id.startsWith(`${scene.idPrefix}-`);
};

const getSceneTrackDuration = (
  sceneFrom: number,
  sceneDuration: number,
  cues: readonly SoundCue[],
): number => {
  const visualSceneEnd = sceneFrom + sceneDuration;
  const audioSceneEnd = cues.reduce((latestEnd, cue) => {
    return Math.max(latestEnd, cue.frame + cue.durationInFrames);
  }, visualSceneEnd);

  // 部分转场音效会自然延续到下一 Scene 的前几帧，因此父音轨允许保留尾音。
  return audioSceneEnd - sceneFrom;
};

export const ProductAudioTrack = ({
  settings: settingsInput,
}: ProductAudioTrackProps) => {
  const {isStudio} = useRemotionEnvironment();
  const settings = resolveProductAudioSettings(settingsInput);

  if (!settings.enabled || (isStudio && settings.studioMode === "off")) {
    return null;
  }

  const mutedCueIds = new Set(settings.mutedCueIds);
  const activeCues = productSoundCues.filter((cue) => {
    if (mutedCueIds.has(cue.id)) {
      return false;
    }

    if (isStudio && settings.studioMode === "key") {
      return cue.importance === "key";
    }

    return true;
  });

  return (
    <>
      {AUDIO_SCENE_TRACKS.map((sceneTrack) => {
        const sceneTiming = timeline[sceneTrack.timelineKey];
        const sceneCues = activeCues.filter((cue) => {
          return belongsToScene(cue, sceneTrack);
        });
        const trackDuration = getSceneTrackDuration(
          sceneTiming.from,
          sceneTiming.duration,
          sceneCues,
        );

        return (
          <Sequence
            key={sceneTrack.idPrefix}
            from={sceneTiming.from}
            durationInFrames={trackDuration}
            premountFor={settings.premountFrames}
            layout="none"
            name={`Audio · ${sceneTrack.label}`}
          >
            {sceneCues.map((cue) => {
              const localFrom = cue.frame - sceneTiming.from;
              const peakVolume =
                cue.volume *
                settings.masterVolume *
                settings.categoryVolumes[cue.category];

              return (
                <Audio
                  key={cue.id}
                  src={resolveSoundSource(
                    cue.assetId,
                    settings.assetOverrides,
                  )}
                  from={localFrom}
                  durationInFrames={cue.durationInFrames}
                  premountFor={settings.premountFrames}
                  volume={(localFrame) => {
                    return peakVolume * getEnvelope(localFrame, cue);
                  }}
                  playbackRate={cue.playbackRate ?? 1}
                  showInTimeline={settings.showInTimeline}
                  name={`SFX · ${cue.id}`}
                />
              );
            })}
          </Sequence>
        );
      })}
    </>
  );
};
