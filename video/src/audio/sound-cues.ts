import {
  ding,
  mouseClick,
  uiSwitch,
  whoosh,
} from "@remotion/sfx";

import {timeline} from "../timeline/product-film";

export type SoundCue = {
  id: string;
  frame: number;
  src: string;
  volume: number;
  durationInFrames: number;
  playbackRate?: number;
};

const createRepeatedCues = ({
  idPrefix,
  startFrame,
  endFrame,
  interval,
  src,
  volume,
  durationInFrames,
  playbackRates = [1.35, 1.5, 1.42],
}: {
  idPrefix: string;
  startFrame: number;
  endFrame: number;
  interval: number;
  src: string;
  volume: number;
  durationInFrames: number;
  playbackRates?: readonly number[];
}): SoundCue[] => {
  const cues: SoundCue[] = [];

  let index = 0;

  for (
    let frame = startFrame;
    frame <= endFrame;
    frame += interval
  ) {
    cues.push({
      id: `${idPrefix}-${index}`,
      frame,
      src,
      volume,
      durationInFrames,
      playbackRate:
        playbackRates[index % playbackRates.length],
    });

    index += 1;
  }

  return cues;
};

const clickCue = (
  id: string,
  frame: number,
  volume = 0.2,
): SoundCue => {
  return {
    id,
    frame,
    src: mouseClick,
    volume,
    durationInFrames: 12,
    playbackRate: 1.05,
  };
};

const switchCue = (
  id: string,
  frame: number,
  volume = 0.065,
): SoundCue => {
  return {
    id,
    frame,
    src: uiSwitch,
    volume,
    durationInFrames: 8,
    playbackRate: 1.15,
  };
};

const whooshCue = (
  id: string,
  frame: number,
  volume = 0.11,
): SoundCue => {
  return {
    id,
    frame,
    src: whoosh,
    volume,
    durationInFrames: 8,
    playbackRate: 1,
  };
};

const dingCue = (
  id: string,
  frame: number,
  volume = 0.1,
): SoundCue => {
  return {
    id,
    frame,
    src: ding,
    volume,
    durationInFrames: 24,
    playbackRate: 1,
  };
};

const cues: SoundCue[] = [
  /*
   * Scene 01：未发送的消息
   * 12–54 帧输入文字。
   * 每 3 帧播放一次短促 tick，而不是每一个字符都播放。
   */
  ...createRepeatedCues({
    idPrefix: "scene-01-typing",
    startFrame: timeline.unsent.from + 12,
    endFrame: timeline.unsent.from + 54,
    interval: 6,
    src: uiSwitch,
    volume: 0.035,
    durationInFrames: 4,
  }),

  /*
   * Scene 02：首页展开
   */
  whooshCue(
    "scene-02-match-cut",
    timeline.landing.from,
    0.12,
  ),

  switchCue(
    "scene-02-preview-content",
    timeline.landing.from + 28,
    0.055,
  ),

  /*
   * Scene 03：场景选择
   */
  clickCue(
    "scene-03-start-button-click",
    timeline.picker.from + 43,
  ),

  whooshCue(
    "scene-03-modal-open",
    timeline.picker.from + 49,
    0.13,
  ),

  switchCue(
    "scene-03-mentor-card",
    timeline.picker.from + 65,
    0.055,
  ),

  switchCue(
    "scene-03-work-card",
    timeline.picker.from + 69,
    0.045,
  ),

  switchCue(
    "scene-03-social-card",
    timeline.picker.from + 73,
    0.045,
  ),

  clickCue(
    "scene-03-mentor-click",
    timeline.picker.from + 146,
  ),

  dingCue(
    "scene-03-mentor-selected",
    timeline.picker.from + 150,
    0.085,
  ),

  whooshCue(
    "scene-03-exit",
    timeline.picker.from + 164,
    0.09,
  ),

  /*
   * Scene 04：场景表单
   */
  clickCue(
    "scene-04-goal-click",
    timeline.scenarioForm.from + 48,
    0.17,
  ),

  switchCue(
    "scene-04-goal-complete",
    timeline.scenarioForm.from + 60,
  ),

  clickCue(
    "scene-04-urgency-click",
    timeline.scenarioForm.from + 94,
    0.17,
  ),

  switchCue(
    "scene-04-urgency-complete",
    timeline.scenarioForm.from + 107,
  ),

  clickCue(
    "scene-04-text-focus",
    timeline.scenarioForm.from + 122,
    0.12,
  ),

  ...createRepeatedCues({
    idPrefix: "scene-04-result-typing",
    startFrame: timeline.scenarioForm.from + 124,
    endFrame: timeline.scenarioForm.from + 158,
    interval: 6,
    src: uiSwitch,
    volume: 0.032,
    durationInFrames: 4,
  }),

  switchCue(
    "scene-04-result-complete",
    timeline.scenarioForm.from + 166,
  ),

  clickCue(
    "scene-04-concern-click",
    timeline.scenarioForm.from + 182,
    0.17,
  ),

  switchCue(
    "scene-04-concern-complete",
    timeline.scenarioForm.from + 195,
  ),

  /*
   * Scene 05：对方信息设置
   */
  whooshCue(
    "scene-05-page-enter",
    timeline.personSetup.from,
    0.09,
  ),

  ...createRepeatedCues({
    idPrefix: "scene-05-role-typing",
    startFrame: timeline.personSetup.from + 32,
    endFrame: timeline.personSetup.from + 42,
    interval: 6,
    src: uiSwitch,
    volume: 0.032,
    durationInFrames: 4,
  }),

  ...createRepeatedCues({
    idPrefix: "scene-05-relation-typing",
    startFrame: timeline.personSetup.from + 49,
    endFrame: timeline.personSetup.from + 61,
    interval: 6,
    src: uiSwitch,
    volume: 0.032,
    durationInFrames: 4,
  }),

  ...createRepeatedCues({
    idPrefix: "scene-05-habit-typing",
    startFrame: timeline.personSetup.from + 66,
    endFrame: timeline.personSetup.from + 79,
    interval: 6,
    src: uiSwitch,
    volume: 0.032,
    durationInFrames: 4,
  }),

  switchCue(
    "scene-05-chat-line-one",
    timeline.personSetup.from + 84,
    0.045,
  ),

  switchCue(
    "scene-05-chat-line-two",
    timeline.personSetup.from + 101,
    0.045,
  ),

  clickCue(
    "scene-05-generate-click",
    timeline.personSetup.from + 154,
  ),

  whooshCue(
    "scene-05-generating",
    timeline.personSetup.from + 168,
    0.1,
  ),

  dingCue(
    "scene-05-generated",
    timeline.personSetup.from + 180,
    0.11,
  ),

  /*
   * Scene 06：Persona
   */
  whooshCue(
    "scene-06-page-enter",
    timeline.persona.from + 4,
    0.1,
  ),

  whooshCue(
    "scene-06-panels-split",
    timeline.persona.from + 28,
    0.09,
  ),

  switchCue(
    "scene-06-trait-one",
    timeline.persona.from + 70,
    0.05,
  ),

  switchCue(
    "scene-06-trait-two",
    timeline.persona.from + 74,
    0.045,
  ),

  switchCue(
    "scene-06-trait-three",
    timeline.persona.from + 78,
    0.045,
  ),

  switchCue(
    "scene-06-trait-four",
    timeline.persona.from + 82,
    0.05,
  ),

  switchCue(
    "scene-06-metrics",
    timeline.persona.from + 96,
    0.055,
  ),

  dingCue(
    "scene-06-strategy-ready",
    timeline.persona.from + 158,
    0.09,
  ),

  /*
   * Scene 07：模拟对话
   */
  ...createRepeatedCues({
    idPrefix: "scene-07-message-typing",
    startFrame: timeline.conversation.from,
    endFrame: timeline.conversation.from + 55,
    interval: 7,
    src: uiSwitch,
    volume: 0.034,
    durationInFrames: 4,
  }),

  clickCue(
    "scene-07-send-click",
    timeline.conversation.from + 65,
    0.21,
  ),

  switchCue(
    "scene-07-user-bubble",
    timeline.conversation.from + 76,
    0.055,
  ),

  switchCue(
    "scene-07-target-typing",
    timeline.conversation.from + 112,
    0.04,
  ),

  dingCue(
    "scene-07-target-response",
    timeline.conversation.from + 140,
    0.085,
  ),

  switchCue(
    "scene-07-focus-chip",
    timeline.conversation.from + 190,
    0.045,
  ),

  /*
   * Scene 08：Agent 协作机制
   */
  whooshCue(
    "scene-08-enter",
    timeline.mechanism.from,
    0.12,
  ),

  whooshCue(
    "scene-08-panel-open",
    timeline.mechanism.from + 24,
    0.09,
  ),

  whooshCue(
    "scene-08-edge-draw",
    timeline.mechanism.from + 52,
    0.08,
  ),

  switchCue(
    "scene-08-persona-agent",
    timeline.mechanism.from + 60,
    0.06,
  ),

  switchCue(
    "scene-08-simulation-agent",
    timeline.mechanism.from + 92,
    0.06,
  ),

  switchCue(
    "scene-08-state-agent",
    timeline.mechanism.from + 124,
    0.06,
  ),

  switchCue(
    "scene-08-prediction-agent",
    timeline.mechanism.from + 164,
    0.06,
  ),

  dingCue(
    "scene-08-mechanism-complete",
    timeline.mechanism.from + 198,
    0.075,
  ),

  /*
   * Scene 09：动态指标
   */
  whooshCue(
    "scene-09-enter",
    timeline.dynamics.from,
    0.09,
  ),

  switchCue(
    "scene-09-time-highlight",
    timeline.dynamics.from + 24,
    0.05,
  ),

  switchCue(
    "scene-09-material-highlight",
    timeline.dynamics.from + 72,
    0.05,
  ),

  switchCue(
    "scene-09-description-highlight",
    timeline.dynamics.from + 120,
    0.05,
  ),

  whooshCue(
    "scene-09-copy-enter",
    timeline.dynamics.from + 150,
    0.075,
  ),

  /*
   * Scene 10：报告
   */
  whooshCue(
    "scene-10-enter",
    timeline.report.from,
    0.11,
  ),

  switchCue(
    "scene-10-score-start",
    timeline.report.from + 20,
    0.055,
  ),

  dingCue(
    "scene-10-score-complete",
    timeline.report.from + 70,
    0.12,
  ),

  switchCue(
    "scene-10-factor-one",
    timeline.report.from + 145,
    0.05,
  ),

  switchCue(
    "scene-10-factor-two",
    timeline.report.from + 153,
    0.05,
  ),

  switchCue(
    "scene-10-factor-three",
    timeline.report.from + 161,
    0.05,
  ),

  whooshCue(
    "scene-10-action-panel",
    timeline.report.from + 200,
    0.075,
  ),

  /*
   * Scene 11：推荐改写与重试
   */
  whooshCue(
    "scene-11-enter",
    timeline.rewrite.from,
    0.1,
  ),

  switchCue(
    "scene-11-segment-one",
    timeline.rewrite.from + 24,
    0.05,
  ),

  switchCue(
    "scene-11-segment-two",
    timeline.rewrite.from + 40,
    0.05,
  ),

  switchCue(
    "scene-11-segment-three",
    timeline.rewrite.from + 56,
    0.05,
  ),

  switchCue(
    "scene-11-tag-one",
    timeline.rewrite.from + 66,
    0.04,
  ),

  switchCue(
    "scene-11-tag-two",
    timeline.rewrite.from + 74,
    0.04,
  ),

  switchCue(
    "scene-11-tag-three",
    timeline.rewrite.from + 82,
    0.04,
  ),

  clickCue(
    "scene-11-retry-click",
    timeline.rewrite.from + 103,
    0.2,
  ),

  whooshCue(
    "scene-11-match-cut",
    timeline.rewrite.from + 110,
    0.11,
  ),

  /*
   * Scene 12：收尾
   */
  whooshCue(
    "scene-12-enter",
    timeline.outro.from,
    0.1,
  ),

  dingCue(
    "scene-12-brand-settle",
    timeline.outro.from + 50,
    0.105,
  ),
];

export const productSoundCues: readonly SoundCue[] =
  cues.sort((a, b) => a.frame - b.frame);
