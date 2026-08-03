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
  cardTransition("scene-02-preview-settle", at("landing", 20), 0.06),

  // Scene 03：CTA 30 帧点击；Modal 4 帧进入；卡片 16/22/28 帧建立；72 帧选择，88 帧开始退出。
  click("scene-03-start-button-click", at("landing", 30), 0, 0.22),
  cue(
    "scene-03-modal-open",
    at("picker", 4),
    "transition.modalOpen",
    "transition",
    0.1,
    20,
    "key",
    {fadeOutFrames: 7},
  ),
  cardTransition("scene-03-mentor-card", at("picker", 16), 0.06),
  cardTransition("scene-03-work-card", at("picker", 22), 0.05),
  cardTransition("scene-03-social-card", at("picker", 28), 0.05),
  click("scene-03-mentor-click", at("picker", 72), 1, 0.22),
  completed("scene-03-mentor-selected", at("picker", 78), 0.09),
  pageTransition("scene-03-exit", at("picker", 88), 0.085, "detail"),

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

  // Scene 05：表单字段在 28/45/62 帧进入，154 帧点击生成，180 帧完成。
  pageTransition("scene-05-page-enter", at("personSetup", 0), 0.07),
  ...typingTicks({
    idPrefix: "scene-05-role-typing",
    startFrame: at("personSetup", 32),
    endFrame: at("personSetup", 42),
    interval: 5,
  }),
  ...typingTicks({
    idPrefix: "scene-05-relation-typing",
    startFrame: at("personSetup", 49),
    endFrame: at("personSetup", 61),
    interval: 6,
  }),
  ...typingTicks({
    idPrefix: "scene-05-habit-typing",
    startFrame: at("personSetup", 66),
    endFrame: at("personSetup", 79),
    interval: 6,
  }),
  selected("scene-05-chat-line-one", at("personSetup", 84), 0.04),
  selected("scene-05-chat-line-two", at("personSetup", 101), 0.04),
  click("scene-05-generate-click", at("personSetup", 154), 5, 0.19),
  pageTransition("scene-05-generating", at("personSetup", 168), 0.075),
  completed("scene-05-generated", at("personSetup", 172), 0.1),

  // Scene 06：面板 28 帧分开，特质 70/74/78/82，策略 150 帧出现。
  pageTransition("scene-06-page-enter", at("persona", 4), 0.08),
  cardTransition("scene-06-panels-split", at("persona", 28), 0.06),
  selected("scene-06-trait-one", at("persona", 70), 0.045),
  selected("scene-06-trait-two", at("persona", 74), 0.04),
  selected("scene-06-trait-three", at("persona", 78), 0.04),
  selected("scene-06-trait-four", at("persona", 82), 0.045),
  completed("scene-06-metrics", at("persona", 96), 0.065, "detail"),
  completed("scene-06-strategy-ready", at("persona", 158), 0.085),
  click("scene-06-start-conversation", at("persona", 220), 6, 0.23),
  pageTransition("scene-06-to-conversation", at("persona", 228), 0.09),

  // Scene 07：承接 Scene 02/03 释放的 48 帧，放慢两轮输入、思考、回复与结束分析节奏。
  cue(
    "scene-07-message-typing",
    at("conversation", 8),
    "typing.loop",
    "typing",
    0.027,
    62,
    "detail",
    {playbackRate: 1.08, fadeInFrames: 2, fadeOutFrames: 8},
  ),
  click("scene-07-send-click", at("conversation", 74), 6, 0.24),
  selected("scene-07-user-bubble", at("conversation", 82), 0.065),
  selected("scene-07-target-typing", at("conversation", 96), 0.05),
  completed("scene-07-target-response", at("conversation", 152), 0.1),
  selected("scene-07-focus-chip", at("conversation", 190), 0.055),
  cue(
    "scene-07-second-message-typing",
    at("conversation", 190),
    "typing.loop",
    "typing",
    0.027,
    78,
    "detail",
    {playbackRate: 1.06, fadeInFrames: 2, fadeOutFrames: 8},
  ),
  click("scene-07-second-send-click", at("conversation", 274), 7, 0.24),
  selected("scene-07-second-user-bubble", at("conversation", 282), 0.065),
  selected("scene-07-second-target-typing", at("conversation", 294), 0.05),
  completed("scene-07-second-target-response", at("conversation", 348), 0.1),
  click("scene-07-finish-click", at("conversation", 382), 8, 0.22),

  // Scene 08：保留移动端多代理机制页，四个 Agent 依次处理。
  pageTransition("scene-08-enter", at("mechanism", 0), 0.1),
  cardTransition("scene-08-panel-open", at("mechanism", 6), 0.055),
  pageTransition("scene-08-edge-draw", at("mechanism", 18), 0.055, "detail"),
  agentPulse("scene-08-persona-agent", at("mechanism", 18)),
  agentPulse("scene-08-simulation-agent", at("mechanism", 58)),
  agentPulse("scene-08-state-agent", at("mechanism", 104)),
  agentPulse("scene-08-prediction-agent", at("mechanism", 152)),
  completed("scene-08-mechanism-complete", at("mechanism", 214), 0.13),

  // Scene 09：从已完成的 Agent 页面直接进入报告，避免等待或骨架屏。
  pageTransition("scene-09-enter", at("dynamics", 8), 0.075),
  selected("scene-09-time-highlight", at("dynamics", 22), 0.045),
  completed("scene-09-material-highlight", at("dynamics", 42), 0.075),
  selected("scene-09-description-highlight", at("dynamics", 118), 0.045),
  cardTransition("scene-09-copy-enter", at("dynamics", 164), 0.05),

  // Scene 10：从报告聚焦到推荐写作工作台，依次识别问题、重构三段逻辑并进入继续对话。
  pageTransition("scene-10-enter", at("report", 0), 0.09),
  cardTransition("scene-10-workbench-focus", at("report", 18), 0.06),
  selected("scene-10-issue-judgement", at("report", 30), 0.04),
  selected("scene-10-issue-evidence", at("report", 42), 0.04),
  selected("scene-10-issue-request", at("report", 54), 0.04),
  selected("scene-10-structure-fact", at("report", 66), 0.045),
  selected("scene-10-structure-judgement", at("report", 84), 0.045),
  selected("scene-10-structure-request", at("report", 102), 0.045),
  cue(
    "scene-10-rewrite-typing",
    at("report", 82),
    "typing.loop",
    "typing",
    0.022,
    66,
    "detail",
    {playbackRate: 1.08, fadeInFrames: 2, fadeOutFrames: 8},
  ),
  completed("scene-10-rewrite-ready", at("report", 146), 0.085),
  softClick("scene-10-tone-control", at("report", 154), 0.09),
  softClick("scene-10-goal-control", at("report", 164), 0.09),
  softClick("scene-10-length-control", at("report", 174), 0.09),
  click("scene-10-continue-click", at("report", 196), 9, 0.19),
  pageTransition("scene-10-to-conversation", at("report", 204), 0.09),

  // Scene 11：推荐版本自动带回对话，上屏、发送、获得回复，并展示结果提升闭环。
  pageTransition("scene-11-enter", at("rewrite", 0), 0.08),
  cue(
    "scene-11-composer-fill",
    at("rewrite", 8),
    "typing.loop",
    "typing",
    0.021,
    40,
    "detail",
    {playbackRate: 1.1, fadeInFrames: 2, fadeOutFrames: 7},
  ),
  click("scene-11-send-click", at("rewrite", 56), 10, 0.2),
  selected("scene-11-user-bubble", at("rewrite", 64), 0.05),
  selected("scene-11-target-typing", at("rewrite", 86), 0.035),
  completed("scene-11-target-response", at("rewrite", 122), 0.08),
  selected("scene-11-score-update", at("rewrite", 146), 0.05),
  selected("scene-11-willingness-up", at("rewrite", 150), 0.04),
  selected("scene-11-warmth-up", at("rewrite", 160), 0.04),
  selected("scene-11-clarity-up", at("rewrite", 170), 0.04),
  cardTransition("scene-11-loop-rewrite", at("rewrite", 180), 0.05),
  cardTransition("scene-11-loop-conversation", at("rewrite", 188), 0.05),
  cardTransition("scene-11-loop-compare", at("rewrite", 196), 0.05),
  completed("scene-11-ad-settle", at("rewrite", 204), 0.075),

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
