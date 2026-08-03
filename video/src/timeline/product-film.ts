export const FPS = 30;

type FrameRange = Readonly<{
  from: number;
  duration: number;
}>;

const after = (range: FrameRange): number => range.from + range.duration;

const unsent = {from: 0, duration: 120} as const;
// Scene 02：仅保留首页稳定态、CTA 呼吸与点击，进一步压缩无操作停留。
const landing = {from: after(unsent), duration: 60} as const;
// Scene 03：选择确认后立即进入退出动画，不再长时间停留在已选状态。
const picker = {from: after(landing), duration: 144} as const;
const scenarioForm = {from: after(picker), duration: 240} as const;
// Scene 05：压缩字段完成后的等待，将生成动作提前并在 180 帧内完成转场。
const personSetup = {from: after(scenarioForm), duration: 180} as const;
const persona = {from: after(personSetup), duration: 240} as const;
// Scene 07：承接 Scene 02/03 释放的 48 帧，使两轮对话的输入、思考与回复更自然。
const conversation = {from: after(persona), duration: 402} as const;
const mechanism = {from: after(conversation), duration: 240} as const;
const dynamics = {from: after(mechanism), duration: 210} as const;
// Scene 10/11：总时长保持 420 帧；将 60 帧从报告阅读转给“推荐写作后继续对话”。
const report = {from: after(dynamics), duration: 210} as const;
const rewrite = {from: after(report), duration: 210} as const;
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
