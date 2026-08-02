export const FPS = 30;

type FrameRange = Readonly<{
  from: number;
  duration: number;
}>;

const after = (range: FrameRange): number => range.from + range.duration;

const unsent = {from: 0, duration: 120} as const;
// Scene 02：删除末尾无动作停顿，保留 Match Cut、首页建立和 CTA 呼吸。
const landing = {from: after(unsent), duration: 126} as const;
const picker = {from: after(landing), duration: 180} as const;
const scenarioForm = {from: after(picker), duration: 240} as const;
// Scene 05：压缩字段完成后的等待，将生成动作提前并在 180 帧内完成转场。
const personSetup = {from: after(scenarioForm), duration: 180} as const;
const persona = {from: after(personSetup), duration: 240} as const;
const conversation = {from: after(persona), duration: 300} as const;
const mechanism = {from: after(conversation), duration: 240} as const;
const dynamics = {from: after(mechanism), duration: 210} as const;
const report = {from: after(dynamics), duration: 270} as const;
const rewrite = {from: after(report), duration: 150} as const;
const outro = {from: after(rewrite), duration: 90} as const;

export const timeline = {
  unsent,
  landing,
  picker,
  scenarioForm,
  personSetup,
  persona,
  conversation,
  mechanism,
  dynamics,
  report,
  rewrite,
  outro,
} as const;

export type ProductSceneKey = keyof typeof timeline;

export const PRODUCT_FILM_DURATION = after(outro);
