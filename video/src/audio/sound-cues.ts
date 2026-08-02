import {PRODUCT_FILM_DURATION, timeline} from "../timeline/product-film";
import type {AudioCategory} from "./audio-settings";
import {
  selectDeterministicValue,
  type SoundAssetId,
} from "./sound-library";

export type SoundCueImportance = "key" | "detail";

export type SoundCue = Readonly<{
  id: string;
  frame: number;
  assetId: SoundAssetId;
  category: AudioCategory;
  volume: number;
  durationInFrames: number;
  playbackRate?: number;
  fadeInFrames?: number;
  fadeOutFrames?: number;
  importance: SoundCueImportance;
}>;

type SceneKey = keyof typeof timeline;

const at = (scene: SceneKey, localFrame: number): number => {
  return timeline[scene].from + localFrame;
};

const cue = (
  id: string,
  frame: number,
  assetId: SoundAssetId,
  category: AudioCategory,
  volume: number,
  durationInFrames: number,
  importance: SoundCueImportance = "detail",
  options: Pick<
    SoundCue,
    "playbackRate" | "fadeInFrames" | "fadeOutFrames"
  > = {},
): SoundCue => ({
  id,
  frame,
  assetId,
  category,
  volume,
  durationInFrames,
  importance,
  ...options,
});

const TYPING_ASSETS = [
  "typing.keySlow",
  "typing.keyLaptop",
] as const satisfies readonly SoundAssetId[];

const TYPING_RATES = [1.28, 1.38, 1.48] as const;
const CLICK_RATES = [0.98, 1, 1.03] as const;

const typingTicks = ({
  idPrefix,
  startFrame,
  endFrame,
  interval,
  volume = 0.032,
}: {
  idPrefix: string;
  startFrame: number;
  endFrame: number;
  interval: number;
  volume?: number;
}): SoundCue[] => {
  const result: SoundCue[] = [];

  for (
    let frame = startFrame, index = 0;
    frame <= endFrame;
    frame += interval, index += 1
  ) {
    result.push(
      cue(
        `${idPrefix}-${index}`,
        frame,
        selectDeterministicValue(TYPING_ASSETS, index),
        "typing",
        volume,
        4,
        "detail",
        {
          playbackRate: selectDeterministicValue(TYPING_RATES, index),
          fadeOutFrames: 2,
        },
      ),
    );
  }

  return result;
};

const click = (
  id: string,
  frame: number,
  variant: number,
  volume = 0.18,
  importance: SoundCueImportance = "key",
): SoundCue =>
  cue(
    id,
    frame,
    variant % 2 === 0 ? "click.primary" : "click.alternate",
    "click",
    volume,
    10,
    importance,
    {
      playbackRate: selectDeterministicValue(CLICK_RATES, variant),
      fadeOutFrames: 3,
    },
  );

const softClick = (
  id: string,
  frame: number,
  volume = 0.1,
): SoundCue =>
  cue(id, frame, "click.soft", "click", volume, 8, "detail", {
    playbackRate: 1.04,
    fadeOutFrames: 3,
  });

const selected = (
  id: string,
  frame: number,
  volume = 0.055,
  importance: SoundCueImportance = "detail",
): SoundCue =>
  cue(
    id,
    frame,
    "status.selected",
    "status",
    volume,
    12,
    importance,
    {playbackRate: 1.06, fadeOutFrames: 4},
  );

const completed = (
  id: string,
  frame: number,
  volume = 0.09,
  importance: SoundCueImportance = "key",
): SoundCue =>
  cue(
    id,
    frame,
    "status.completed",
    "status",
    volume,
    26,
    importance,
    {fadeInFrames: 2, fadeOutFrames: 8},
  );

const pageTransition = (
  id: string,
  frame: number,
  volume = 0.08,
  importance: SoundCueImportance = "key",
): SoundCue =>
  cue(
    id,
    frame,
    "transition.pageSoft",
    "transition",
    volume,
    20,
    importance,
    {fadeInFrames: 1, fadeOutFrames: 7},
  );

const cardTransition = (
  id: string,
  frame: number,
  volume = 0.06,
): SoundCue =>
  cue(
    id,
    frame,
    "transition.cardSlide",
    "transition",
    volume,
    18,
    "detail",
    {fadeOutFrames: 6},
  );

const agentPulse = (id: string, frame: number): SoundCue =>
  cue(
    id,
    frame,
    "status.agentPulse",
    "status",
    0.052,
    18,
    "detail",
    {playbackRate: 1.04, fadeOutFrames: 6},
  );

const cues: SoundCue[] = [
  // Scene 01：文字在 12–54 帧逐字出现。
  ...typingTicks({
    idPrefix: "scene-01-typing",
    startFrame: at("unsent", 12),
    endFrame: at("unsent", 54),
    interval: 6,
  }),

  // Scene 02：首帧完成 Composer 到首页 Preview 的 Match Cut。
  pageTransition("scene-02-match-cut", at("landing", 0), 0.1),
  cardTransition("scene-02-preview-settle", at("landing", 28), 0.05),

  // Scene 03：CTA 42–45 按压；Modal 49 开始；卡片 65/69/73；导师 145–148 点击。
  click("scene-03-start-button-click", at("picker", 43), 0, 0.19),
  cue(
    "scene-03-modal-open",
    at("picker", 49),
    "transition.modalOpen",
    "transition",
    0.1,
    20,
    "key",
    {fadeOutFrames: 7},
  ),
  cardTransition("scene-03-mentor-card", at("picker", 65), 0.05),
  cardTransition("scene-03-work-card", at("picker", 69), 0.04),
  cardTransition("scene-03-social-card", at("picker", 73), 0.04),
  click("scene-03-mentor-click", at("picker", 146), 1, 0.18),
  completed("scene-03-mentor-selected", at("picker", 150), 0.075),
  pageTransition("scene-03-exit", at("picker", 164), 0.065, "detail"),

  // Scene 04：各题点击、输入和完成反馈与现有光标/卡片动画对齐。
  click("scene-04-goal-click", at("scenarioForm", 48), 2, 0.16),
  selected("scene-04-goal-complete", at("scenarioForm", 60)),
  click("scene-04-urgency-click", at("scenarioForm", 94), 3, 0.16),
  selected("scene-04-urgency-complete", at("scenarioForm", 107)),
  softClick("scene-04-text-focus", at("scenarioForm", 122), 0.11),
  ...typingTicks({
    idPrefix: "scene-04-result-typing",
    startFrame: at("scenarioForm", 124),
    endFrame: at("scenarioForm", 158),
    interval: 6,
    volume: 0.029,
  }),
  selected("scene-04-result-complete", at("scenarioForm", 166)),
  click("scene-04-concern-click", at("scenarioForm", 182), 4, 0.16),
  selected("scene-04-concern-complete", at("scenarioForm", 195)),

  // Scene 05：字段紧凑进入，126 帧点击，146 帧进入生成完成反馈。
  pageTransition("scene-05-page-enter", at("personSetup", 0), 0.07),
  ...typingTicks({
    idPrefix: "scene-05-role-typing",
    startFrame: at("personSetup", 18),
    endFrame: at("personSetup", 28),
    interval: 5,
  }),
  ...typingTicks({
    idPrefix: "scene-05-relation-typing",
    startFrame: at("personSetup", 30),
    endFrame: at("personSetup", 42),
    interval: 6,
  }),
  ...typingTicks({
    idPrefix: "scene-05-habit-typing",
    startFrame: at("personSetup", 46),
    endFrame: at("personSetup", 60),
    interval: 6,
  }),
  selected("scene-05-chat-line-one", at("personSetup", 70), 0.04),
  selected("scene-05-chat-line-two", at("personSetup", 84), 0.04),
  click("scene-05-generate-click", at("personSetup", 126), 5, 0.19),
  pageTransition("scene-05-generating", at("personSetup", 136), 0.075),
  completed("scene-05-generated", at("personSetup", 146), 0.1),

  // Scene 06：面板 28 帧分开，特质 70/74/78/82，策略 150 帧出现。
  pageTransition("scene-06-page-enter", at("persona", 4), 0.08),
  cardTransition("scene-06-panels-split", at("persona", 28), 0.06),
  selected("scene-06-trait-one", at("persona", 70), 0.045),
  selected("scene-06-trait-two", at("persona", 74), 0.04),
  selected("scene-06-trait-three", at("persona", 78), 0.04),
  selected("scene-06-trait-four", at("persona", 82), 0.045),
  completed("scene-06-metrics", at("persona", 96), 0.065, "detail"),
  completed("scene-06-strategy-ready", at("persona", 158), 0.085),

  // Scene 07：输入 0–55，按钮 61–70，用户气泡 76，目标回复 140。
  cue(
    "scene-07-message-typing",
    at("conversation", 0),
    "typing.loop",
    "typing",
    0.023,
    56,
    "detail",
    {playbackRate: 1.08, fadeInFrames: 2, fadeOutFrames: 8},
  ),
  click("scene-07-send-click", at("conversation", 65), 6, 0.2),
  selected("scene-07-user-bubble", at("conversation", 76), 0.05),
  selected("scene-07-target-typing", at("conversation", 112), 0.035),
  completed("scene-07-target-response", at("conversation", 140), 0.08),
  selected("scene-07-focus-chip", at("conversation", 190), 0.04),

  // Scene 08：面板 24、连线 52、四个 Agent 60/92/124/164。
  pageTransition("scene-08-enter", at("mechanism", 0), 0.1),
  cardTransition("scene-08-panel-open", at("mechanism", 24), 0.055),
  pageTransition("scene-08-edge-draw", at("mechanism", 52), 0.055, "detail"),
  agentPulse("scene-08-persona-agent", at("mechanism", 60)),
  agentPulse("scene-08-simulation-agent", at("mechanism", 92)),
  agentPulse("scene-08-state-agent", at("mechanism", 124)),
  agentPulse("scene-08-prediction-agent", at("mechanism", 164)),
  completed("scene-08-mechanism-complete", at("mechanism", 198), 0.07),

  // Scene 09：证据高亮依次从 24/72/120 帧开始，150 帧文案进入。
  pageTransition("scene-09-enter", at("dynamics", 0), 0.075),
  selected("scene-09-time-highlight", at("dynamics", 24), 0.045),
  selected("scene-09-material-highlight", at("dynamics", 72), 0.045),
  selected("scene-09-description-highlight", at("dynamics", 120), 0.045),
  cardTransition("scene-09-copy-enter", at("dynamics", 150), 0.05),

  // Scene 10：评分 20–70，因素 145/153/161，行动面板 200。
  pageTransition("scene-10-enter", at("report", 0), 0.09),
  selected("scene-10-score-start", at("report", 20), 0.05),
  cue(
    "scene-10-score-complete",
    at("report", 70),
    "status.reportReady",
    "status",
    0.11,
    24,
    "key",
    {fadeOutFrames: 8},
  ),
  selected("scene-10-factor-one", at("report", 145), 0.045),
  selected("scene-10-factor-two", at("report", 153), 0.045),
  selected("scene-10-factor-three", at("report", 161), 0.045),
  cardTransition("scene-10-action-panel", at("report", 200), 0.055),

  // Scene 11：改写段落和标签依次进入，103 帧按下重试，110 帧转场。
  pageTransition("scene-11-enter", at("rewrite", 0), 0.08),
  selected("scene-11-segment-one", at("rewrite", 24), 0.045),
  selected("scene-11-segment-two", at("rewrite", 40), 0.045),
  selected("scene-11-segment-three", at("rewrite", 56), 0.045),
  selected("scene-11-tag-one", at("rewrite", 66), 0.035),
  selected("scene-11-tag-two", at("rewrite", 74), 0.035),
  selected("scene-11-tag-three", at("rewrite", 82), 0.035),
  click("scene-11-retry-click", at("rewrite", 103), 7, 0.19),
  pageTransition("scene-11-match-cut", at("rewrite", 110), 0.09),

  // Scene 12：品牌 18–50 帧显现，在 50 帧落定。
  pageTransition("scene-12-enter", at("outro", 0), 0.08),
  cue(
    "scene-12-brand-settle",
    at("outro", 50),
    "brand.logo",
    "brand",
    0.1,
    40,
    "key",
    {fadeInFrames: 3, fadeOutFrames: 12},
  ),
];

const sortedCues = [...cues].sort((a, b) => a.frame - b.frame);
const cueIds = sortedCues.map((item) => item.id);

if (cueIds.length !== new Set(cueIds).size) {
  throw new Error("sound-cues.ts contains duplicate SoundCue IDs");
}

for (const item of sortedCues) {
  if (!Number.isInteger(item.frame) || item.frame < 0) {
    throw new Error(`Invalid frame for sound cue: ${item.id}`);
  }

  if (
    !Number.isInteger(item.durationInFrames) ||
    item.durationInFrames <= 0
  ) {
    throw new Error(`Invalid duration for sound cue: ${item.id}`);
  }

  if (item.frame + item.durationInFrames > PRODUCT_FILM_DURATION) {
    throw new Error(`Sound cue exceeds product film: ${item.id}`);
  }
}

export const productSoundCues: readonly SoundCue[] = sortedCues;
