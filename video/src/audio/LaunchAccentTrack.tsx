import {Audio} from "@remotion/media";
import {Sequence} from "remotion";

import {PRODUCT_FILM_DURATION, timeline} from "../timeline/product-film";
import {
  resolveSoundSource,
  type SoundAssetId,
  type SoundAssetOverrides,
} from "./sound-library";

type LaunchAccentCue = Readonly<{
  id: string;
  frame: number;
  durationInFrames: number;
  assetId: SoundAssetId;
  volume: number;
  playbackRate?: number;
  fadeInFrames?: number;
  fadeOutFrames?: number;
}>;

export type LaunchAccentTrackSettings = Readonly<{
  enabled?: boolean;
  volume?: number;
  showInTimeline?: boolean;
  assetOverrides?: SoundAssetOverrides;
}>;

export type LaunchAccentTrackProps = Readonly<{
  settings?: LaunchAccentTrackSettings;
}>;

const clamp = (value: number, min: number, max: number): number => {
  if (!Number.isFinite(value)) {
    return min;
  }

  return Math.min(max, Math.max(min, value));
};

const clamp01 = (value: number): number => clamp(value, 0, 1);

const cue = (
  id: string,
  frame: number,
  durationInFrames: number,
  assetId: SoundAssetId,
  volume: number,
  options: Partial<
    Pick<
      LaunchAccentCue,
      "playbackRate" | "fadeInFrames" | "fadeOutFrames"
    >
  > = {},
): LaunchAccentCue => ({
  id,
  frame,
  durationInFrames,
  assetId,
  volume,
  ...options,
});

/**
 * 只负责“发布片层”的强调音效。
 * 产品点击、输入、Agent 与报告音效仍由 ProductAudioTrack 负责。
 */
const launchAccentCues: readonly LaunchAccentCue[] = [
  cue(
    "launch-opening-mark",
    timeline.unsent.from + 4,
    54,
    "brand.logo",
    0.12,
    {fadeInFrames: 2, fadeOutFrames: 12},
  ),
  cue(
    "launch-product-reveal",
    timeline.landing.from,
    32,
    "transition.pageSoft",
    0.1,
    {fadeOutFrames: 10},
  ),
  cue(
    "launch-setup-chapter",
    timeline.picker.from + 2,
    34,
    "transition.cardSlide",
    0.075,
    {fadeOutFrames: 10},
  ),
  cue(
    "launch-persona-proof",
    timeline.persona.from + 18,
    34,
    "status.selected",
    0.09,
    {fadeOutFrames: 12},
  ),
  cue(
    "launch-conversation-proof",
    timeline.conversation.from + 14,
    38,
    "transition.pageSoft",
    0.08,
    {fadeOutFrames: 14},
  ),

  // Scene 08：Agent 激活与完成跳动严格对齐。
  cue("launch-agent-persona-start", timeline.mechanism.from + 18, 20, "status.agentPulse", 0.075, {fadeOutFrames: 7}),
  cue("launch-agent-persona-done", timeline.mechanism.from + 46, 18, "status.selected", 0.055, {playbackRate: 1.06, fadeOutFrames: 6}),
  cue("launch-agent-simulation-start", timeline.mechanism.from + 58, 20, "status.agentPulse", 0.075, {fadeOutFrames: 7}),
  cue("launch-agent-simulation-done", timeline.mechanism.from + 88, 18, "status.selected", 0.055, {playbackRate: 1.06, fadeOutFrames: 6}),
  cue("launch-agent-state-start", timeline.mechanism.from + 104, 20, "status.agentPulse", 0.078, {fadeOutFrames: 7}),
  cue("launch-agent-state-done", timeline.mechanism.from + 136, 18, "status.selected", 0.058, {playbackRate: 1.06, fadeOutFrames: 6}),
  cue("launch-agent-prediction-start", timeline.mechanism.from + 152, 22, "status.agentPulse", 0.084, {fadeOutFrames: 8}),
  cue("launch-agent-prediction-done", timeline.mechanism.from + 194, 20, "status.selected", 0.062, {playbackRate: 1.05, fadeOutFrames: 7}),
  cue("launch-mechanism-complete", timeline.mechanism.from + 214, 26, "status.completed", 0.12, {fadeInFrames: 2, fadeOutFrames: 9}),

  cue(
    "launch-report-proof",
    timeline.report.from + 12,
    42,
    "status.reportReady",
    0.105,
    {fadeOutFrames: 14},
  ),

  // Scene 11：诊断 → 重写 → 继续模拟 → 结果对比。
  cue("launch-rewrite-workbench", timeline.rewrite.from + 6, 32, "transition.pageSoft", 0.105, {fadeOutFrames: 11}),
  cue("launch-rewrite-issue-1", timeline.rewrite.from + 14, 12, "status.selected", 0.045, {playbackRate: 1.08, fadeOutFrames: 4}),
  cue("launch-rewrite-issue-2", timeline.rewrite.from + 22, 12, "status.selected", 0.045, {playbackRate: 1.1, fadeOutFrames: 4}),
  cue("launch-rewrite-issue-3", timeline.rewrite.from + 30, 12, "status.selected", 0.05, {playbackRate: 1.12, fadeOutFrames: 4}),
  cue("launch-rewrite-typing", timeline.rewrite.from + 28, 46, "typing.loop", 0.058, {playbackRate: 1.06, fadeInFrames: 4, fadeOutFrames: 9}),
  cue("launch-rewrite-strategy-1", timeline.rewrite.from + 48, 12, "click.soft", 0.05, {fadeOutFrames: 4}),
  cue("launch-rewrite-strategy-2", timeline.rewrite.from + 58, 12, "click.soft", 0.05, {fadeOutFrames: 4}),
  cue("launch-rewrite-strategy-3", timeline.rewrite.from + 68, 14, "status.selected", 0.065, {fadeOutFrames: 5}),
  cue("launch-retry-click", timeline.rewrite.from + 104, 16, "click.primary", 0.13, {fadeOutFrames: 5}),
  cue("launch-retry-match-cut", timeline.rewrite.from + 112, 30, "transition.cardSlide", 0.09, {fadeOutFrames: 10}),
  cue("launch-retry-composer-fill", timeline.rewrite.from + 116, 24, "typing.loop", 0.05, {playbackRate: 1.08, fadeInFrames: 3, fadeOutFrames: 7}),
  cue("launch-retry-send", timeline.rewrite.from + 142, 14, "click.alternate", 0.13, {fadeOutFrames: 5}),
  cue("launch-retry-user-bubble", timeline.rewrite.from + 148, 14, "status.selected", 0.052, {fadeOutFrames: 5}),
  cue("launch-retry-response", timeline.rewrite.from + 174, 24, "status.completed", 0.09, {fadeInFrames: 2, fadeOutFrames: 8}),
  cue("launch-retry-metric-1", timeline.rewrite.from + 184, 12, "status.selected", 0.052, {playbackRate: 1.04, fadeOutFrames: 4}),
  cue("launch-retry-metric-2", timeline.rewrite.from + 192, 12, "status.selected", 0.052, {playbackRate: 1.08, fadeOutFrames: 4}),
  cue("launch-retry-metric-3", timeline.rewrite.from + 200, 10, "status.completed", 0.07, {fadeOutFrames: 6}),

  cue(
    "launch-closing-mark",
    timeline.outro.from,
    Math.min(72, timeline.outro.duration),
    "brand.logo",
    0.14,
    {fadeInFrames: 2, fadeOutFrames: 18},
  ),
];

export const LaunchAccentTrack = ({
  settings,
}: LaunchAccentTrackProps) => {
  const enabled = settings?.enabled ?? true;
  const masterVolume = clamp(settings?.volume ?? 1, 0, 1.5);
  const showInTimeline = settings?.showInTimeline ?? true;
  const overrides = settings?.assetOverrides ?? {};

  if (!enabled) {
    return null;
  }

  return (
    <>
      {launchAccentCues.map((item) => {
        const safeDuration = Math.min(
          item.durationInFrames,
          PRODUCT_FILM_DURATION - item.frame,
        );

        if (safeDuration <= 0) {
          return null;
        }

        return (
          <Sequence
            key={item.id}
            from={item.frame}
            durationInFrames={safeDuration}
            layout="none"
            name={`Launch SFX · ${item.id}`}
          >
            <Audio
              src={resolveSoundSource(item.assetId, overrides)}
              playbackRate={item.playbackRate ?? 1}
              showInTimeline={showInTimeline}
              name={`Launch SFX · ${item.id}`}
              volume={(localFrame) => {
                const fadeInFrames = Math.max(0, item.fadeInFrames ?? 0);
                const fadeOutFrames = Math.max(0, item.fadeOutFrames ?? 0);
                const fadeIn =
                  fadeInFrames === 0
                    ? 1
                    : clamp01(localFrame / fadeInFrames);
                const framesRemaining = safeDuration - 1 - localFrame;
                const fadeOut =
                  fadeOutFrames === 0
                    ? 1
                    : clamp01(framesRemaining / fadeOutFrames);

                return item.volume * masterVolume * Math.min(fadeIn, fadeOut);
              }}
            />
          </Sequence>
        );
      })}
    </>
  );
};
