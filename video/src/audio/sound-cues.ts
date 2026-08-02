import {timeline} from "../timeline/product-film";
import {
  SOUNDS,
  selectDeterministicValue,
} from "./sound-library";

export type SoundCue = Readonly<{
  id: string;
  frame: number;
  src: string;
  volume: number;
  durationInFrames: number;
  playbackRate?: number;
}>;

const TYPING_SOURCES = [
  SOUNDS.typing.key01,
  SOUNDS.typing.key02,
] as const;

const TYPING_RATES = [1.32, 1.42, 1.5] as const;
const CLICK_RATES = [0.98, 1, 1.03] as const;

const createTypingCues = ({
  idPrefix,
  startFrame,
  endFrame,
  interval,
  volume = 0.028,
}: {
  idPrefix: string;
  startFrame: number;
  endFrame: number;
  interval: number;
  volume?: number;
}): SoundCue[] => {
  const result: SoundCue[] = [];
  let index = 0;

  for (
    let frame = startFrame;
    frame <= endFrame;
    frame += interval
  ) {
    result.push({
      id: `${idPrefix}-${index}`,
      frame,
      src: selectDeterministicValue(
        TYPING_SOURCES,
        index,
      ),
      volume,
      durationInFrames: 3,
      playbackRate: selectDeterministicValue(
        TYPING_RATES,
        index,
      ),
    });

    index += 1;
  }

  return result;
};

const createClickCue = (
  id: string,
  frame: number,
  variant: number,
  volume = 0.18,
): SoundCue => {
  return {
    id,
    frame,
    src:
      variant % 2 === 0
        ? SOUNDS.click.primary01
        : SOUNDS.click.primary02,
    volume,
    durationInFrames: 10,
    playbackRate: selectDeterministicValue(
      CLICK_RATES,
      variant,
    ),
  };
};

const createSecondaryClickCue = (
  id: string,
  frame: number,
  volume = 0.11,
): SoundCue => {
  return {
    id,
    frame,
    src: SOUNDS.click.secondary01,
    volume,
    durationInFrames: 8,
    playbackRate: 1.06,
  };
};

const createSelectedCue = (
  id: string,
  frame: number,
  volume = 0.055,
): SoundCue => {
  return {
    id,
    frame,
    src: SOUNDS.status.selected,
    volume,
    durationInFrames: 10,
    playbackRate: 1.08,
  };
};

const createCompletedCue = (
  id: string,
  frame: number,
  volume = 0.09,
): SoundCue => {
  return {
    id,
    frame,
    src: SOUNDS.status.completed,
    volume,
    durationInFrames: 24,
  };
};

const createReportReadyCue = (
  id: string,
  frame: number,
  volume = 0.11,
): SoundCue => {
  return {
    id,
    frame,
    src: SOUNDS.status.reportReady,
    volume,
    durationInFrames: 28,
  };
};

const createAgentPulseCue = (
  id: string,
  frame: number,
  volume = 0.052,
): SoundCue => {
  return {
    id,
    frame,
    src: SOUNDS.status.agentPulse,
    volume,
    durationInFrames: 16,
    playbackRate: 1.04,
  };
};

const createPageTransitionCue = (
  id: string,
  frame: number,
  volume = 0.08,
): SoundCue => {
  return {
    id,
    frame,
    src: SOUNDS.transitions.pageSoft,
    volume,
    durationInFrames: 18,
  };
};

const createModalTransitionCue = (
  id: string,
  frame: number,
  volume = 0.09,
): SoundCue => {
  return {
    id,
    frame,
    src: SOUNDS.transitions.modalOpen,
    volume,
    durationInFrames: 18,
  };
};

const createCardTransitionCue = (
  id: string,
  frame: number,
  volume = 0.065,
): SoundCue => {
  return {
    id,
    frame,
    src: SOUNDS.transitions.cardSlide,
    volume,
    durationInFrames: 16,
  };
};

const createTypingLoopCue = (
  id: string,
  frame: number,
  durationInFrames: number,
  volume = 0.025,
): SoundCue => {
  return {
    id,
    frame,
    src: SOUNDS.typing.loop,
    volume,
    durationInFrames,
  };
};

const createBrandCue = (
  id: string,
  frame: number,
  volume = 0.11,
): SoundCue => {
  return {
    id,
    frame,
    src: SOUNDS.brand.logo,
    volume,
    durationInFrames: 40,
  };
};

const cues: SoundCue[] = [
  // Scene 01：未发送消息
  ...createTypingCues({
    idPrefix: "scene-01-typing",
    startFrame: timeline.unsent.from + 12,
    endFrame: timeline.unsent.from + 54,
    interval: 6,
  }),

  // Scene 02：首页
  createPageTransitionCue(
    "scene-02-match-cut",
    timeline.landing.from,
    0.1,
  ),
  createCardTransitionCue(
    "scene-02-preview-content",
    timeline.landing.from + 28,
    0.05,
  ),

  // Scene 03：场景选择
  createClickCue(
    "scene-03-start-button-click",
    timeline.picker.from + 43,
    0,
  ),
  createModalTransitionCue(
    "scene-03-modal-open",
    timeline.picker.from + 49,
    0.1,
  ),
  createCardTransitionCue(
    "scene-03-mentor-card",
    timeline.picker.from + 65,
    0.05,
  ),
  createCardTransitionCue(
    "scene-03-work-card",
    timeline.picker.from + 69,
    0.04,
  ),
  createCardTransitionCue(
    "scene-03-social-card",
    timeline.picker.from + 73,
    0.04,
  ),
  createClickCue(
    "scene-03-mentor-click",
    timeline.picker.from + 146,
    1,
  ),
  createCompletedCue(
    "scene-03-mentor-selected",
    timeline.picker.from + 150,
    0.08,
  ),
  createPageTransitionCue(
    "scene-03-exit",
    timeline.picker.from + 164,
    0.07,
  ),

  // Scene 04：结构化场景表单
  createClickCue(
    "scene-04-goal-click",
    timeline.scenarioForm.from + 48,
    2,
    0.16,
  ),
  createSelectedCue(
    "scene-04-goal-complete",
    timeline.scenarioForm.from + 60,
  ),
  createClickCue(
    "scene-04-urgency-click",
    timeline.scenarioForm.from + 94,
    3,
    0.16,
  ),
  createSelectedCue(
    "scene-04-urgency-complete",
    timeline.scenarioForm.from + 107,
  ),
  createSecondaryClickCue(
    "scene-04-text-focus",
    timeline.scenarioForm.from + 122,
  ),
  ...createTypingCues({
    idPrefix: "scene-04-result-typing",
    startFrame: timeline.scenarioForm.from + 124,
    endFrame: timeline.scenarioForm.from + 158,
    interval: 6,
  }),
  createSelectedCue(
    "scene-04-result-complete",
    timeline.scenarioForm.from + 166,
  ),
  createClickCue(
    "scene-04-concern-click",
    timeline.scenarioForm.from + 182,
    4,
    0.16,
  ),
  createSelectedCue(
    "scene-04-concern-complete",
    timeline.scenarioForm.from + 195,
  ),

  // Scene 05：对方信息
  createPageTransitionCue(
    "scene-05-page-enter",
    timeline.personSetup.from,
    0.07,
  ),
  ...createTypingCues({
    idPrefix: "scene-05-role-typing",
    startFrame: timeline.personSetup.from + 32,
    endFrame: timeline.personSetup.from + 42,
    interval: 6,
  }),
  ...createTypingCues({
    idPrefix: "scene-05-relation-typing",
    startFrame: timeline.personSetup.from + 49,
    endFrame: timeline.personSetup.from + 61,
    interval: 6,
  }),
  ...createTypingCues({
    idPrefix: "scene-05-habit-typing",
    startFrame: timeline.personSetup.from + 66,
    endFrame: timeline.personSetup.from + 79,
    interval: 6,
  }),
  createSelectedCue(
    "scene-05-chat-line-one",
    timeline.personSetup.from + 84,
    0.04,
  ),
  createSelectedCue(
    "scene-05-chat-line-two",
    timeline.personSetup.from + 101,
    0.04,
  ),
  createClickCue(
    "scene-05-generate-click",
    timeline.personSetup.from + 154,
    5,
  ),
  createPageTransitionCue(
    "scene-05-generating",
    timeline.personSetup.from + 168,
    0.08,
  ),
  createCompletedCue(
    "scene-05-generated",
    timeline.personSetup.from + 180,
    0.1,
  ),

  // Scene 06：Persona
  createPageTransitionCue(
    "scene-06-page-enter",
    timeline.persona.from + 4,
    0.08,
  ),
  createCardTransitionCue(
    "scene-06-panels-split",
    timeline.persona.from + 28,
    0.06,
  ),
  createSelectedCue(
    "scene-06-trait-one",
    timeline.persona.from + 70,
    0.045,
  ),
  createSelectedCue(
    "scene-06-trait-two",
    timeline.persona.from + 74,
    0.04,
  ),
  createSelectedCue(
    "scene-06-trait-three",
    timeline.persona.from + 78,
    0.04,
  ),
  createSelectedCue(
    "scene-06-trait-four",
    timeline.persona.from + 82,
    0.045,
  ),
  createCompletedCue(
    "scene-06-metrics",
    timeline.persona.from + 96,
    0.065,
  ),
  createCompletedCue(
    "scene-06-strategy-ready",
    timeline.persona.from + 158,
    0.085,
  ),

  // Scene 07：模拟对话
  createTypingLoopCue(
    "scene-07-message-typing",
    timeline.conversation.from,
    55,
    0.022,
  ),
  createClickCue(
    "scene-07-send-click",
    timeline.conversation.from + 65,
    6,
    0.2,
  ),
  createSelectedCue(
    "scene-07-user-bubble",
    timeline.conversation.from + 76,
    0.05,
  ),
  createSelectedCue(
    "scene-07-target-typing",
    timeline.conversation.from + 112,
    0.035,
  ),
  createCompletedCue(
    "scene-07-target-response",
    timeline.conversation.from + 140,
    0.08,
  ),
  createSelectedCue(
    "scene-07-focus-chip",
    timeline.conversation.from + 190,
    0.04,
  ),

  // Scene 08：Agent 机制示意
  createPageTransitionCue(
    "scene-08-enter",
    timeline.mechanism.from,
    0.1,
  ),
  createCardTransitionCue(
    "scene-08-panel-open",
    timeline.mechanism.from + 24,
    0.055,
  ),
  createPageTransitionCue(
    "scene-08-edge-draw",
    timeline.mechanism.from + 52,
    0.055,
  ),
  createAgentPulseCue(
    "scene-08-persona-agent",
    timeline.mechanism.from + 60,
  ),
  createAgentPulseCue(
    "scene-08-simulation-agent",
    timeline.mechanism.from + 92,
  ),
  createAgentPulseCue(
    "scene-08-state-agent",
    timeline.mechanism.from + 124,
  ),
  createAgentPulseCue(
    "scene-08-prediction-agent",
    timeline.mechanism.from + 164,
  ),
  createCompletedCue(
    "scene-08-mechanism-complete",
    timeline.mechanism.from + 198,
    0.07,
  ),

  // Scene 09：动态指标
  createPageTransitionCue(
    "scene-09-enter",
    timeline.dynamics.from,
    0.075,
  ),
  createSelectedCue(
    "scene-09-time-highlight",
    timeline.dynamics.from + 24,
    0.045,
  ),
  createSelectedCue(
    "scene-09-material-highlight",
    timeline.dynamics.from + 72,
    0.045,
  ),
  createSelectedCue(
    "scene-09-description-highlight",
    timeline.dynamics.from + 120,
    0.045,
  ),
  createCardTransitionCue(
    "scene-09-copy-enter",
    timeline.dynamics.from + 150,
    0.05,
  ),

  // Scene 10：报告
  createPageTransitionCue(
    "scene-10-enter",
    timeline.report.from,
    0.09,
  ),
  createSelectedCue(
    "scene-10-score-start",
    timeline.report.from + 20,
    0.05,
  ),
  createReportReadyCue(
    "scene-10-score-complete",
    timeline.report.from + 70,
    0.11,
  ),
  createSelectedCue(
    "scene-10-factor-one",
    timeline.report.from + 145,
    0.045,
  ),
  createSelectedCue(
    "scene-10-factor-two",
    timeline.report.from + 153,
    0.045,
  ),
  createSelectedCue(
    "scene-10-factor-three",
    timeline.report.from + 161,
    0.045,
  ),
  createCardTransitionCue(
    "scene-10-action-panel",
    timeline.report.from + 200,
    0.055,
  ),

  // Scene 11：改写与重试
  createPageTransitionCue(
    "scene-11-enter",
    timeline.rewrite.from,
    0.08,
  ),
  createSelectedCue(
    "scene-11-segment-one",
    timeline.rewrite.from + 24,
    0.045,
  ),
  createSelectedCue(
    "scene-11-segment-two",
    timeline.rewrite.from + 40,
    0.045,
  ),
  createSelectedCue(
    "scene-11-segment-three",
    timeline.rewrite.from + 56,
    0.045,
  ),
  createSelectedCue(
    "scene-11-tag-one",
    timeline.rewrite.from + 66,
    0.035,
  ),
  createSelectedCue(
    "scene-11-tag-two",
    timeline.rewrite.from + 74,
    0.035,
  ),
  createSelectedCue(
    "scene-11-tag-three",
    timeline.rewrite.from + 82,
    0.035,
  ),
  createClickCue(
    "scene-11-retry-click",
    timeline.rewrite.from + 103,
    7,
    0.19,
  ),
  createPageTransitionCue(
    "scene-11-match-cut",
    timeline.rewrite.from + 110,
    0.09,
  ),

  // Scene 12：收尾
  createPageTransitionCue(
    "scene-12-enter",
    timeline.outro.from,
    0.08,
  ),
  createBrandCue(
    "scene-12-brand-settle",
    timeline.outro.from + 50,
    0.1,
  ),
];

const sortedCues = [...cues].sort((a, b) => {
  return a.frame - b.frame;
});

const cueIds = sortedCues.map((cue) => cue.id);
const uniqueCueIds = new Set(cueIds);

if (cueIds.length !== uniqueCueIds.size) {
  throw new Error(
    "sound-cues.ts contains duplicate SoundCue IDs",
  );
}

export const productSoundCues: readonly SoundCue[] =
  sortedCues;
