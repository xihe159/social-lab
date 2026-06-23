import type { ScenarioKey, ScenarioPreset } from "./social-lab-types";

export const scenarioPresets: Record<ScenarioKey, ScenarioPreset> = {
  advisor: {
    label: "导师沟通",
    summary: "推荐信 / 催回复 / 申请延期",
    role: "我的导师",
    goal: "我想请导师帮我写推荐信",
    outcome: "希望导师愿意帮忙，并且不要觉得我太唐突",
    relation: "我上过他的课，也帮他做过一次项目。",
    habit: "回复慢，比较严格，喜欢有逻辑的人，不喜欢被催。",
    title: "导师画像",
    chatTitle: "导师 · 推荐信模拟",
    style: "理性型",
    speed: "偏慢",
    focus: "逻辑、材料完整度",
    risk: "不喜欢被催促",
    strategy:
      "先说明申请背景和截止时间，再提出请求；主动提供材料、草稿和时间安排，降低对方时间成本。",
    state: {
      trust: 65,
      respect: 80,
      familiarity: 45,
      affinity: 35,
      authority: 90,
      emotional: 10,
    },
  },
  work: {
    label: "职场沟通",
    summary: "谈加薪 / 拒绝额外工作 / 汇报",
    role: "我的直属领导",
    goal: "我想和领导讨论加薪或调整工作量",
    outcome: "希望对方认真考虑我的贡献，并给出明确下一步",
    relation: "我入职一年左右，平时能按时完成任务，但还没有很深入的私人关系。",
    habit: "重视结果和数据，沟通直接，时间比较紧。",
    title: "领导画像",
    chatTitle: "领导 · 向上沟通模拟",
    style: "结果导向",
    speed: "中等",
    focus: "绩效、业务影响",
    risk: "不喜欢空泛诉求",
    strategy:
      "先用具体成果建立讨论基础，再提出诉求和可衡量方案，避免只强调个人感受。",
    state: {
      trust: 58,
      respect: 72,
      familiarity: 52,
      affinity: 38,
      authority: 82,
      emotional: 5,
    },
  },
  social: {
    label: "社交沟通",
    summary: "道歉 / 拒绝请求 / 处理冲突",
    role: "我的朋友",
    goal: "我想拒绝一个不太方便答应的请求",
    outcome: "希望清楚表达边界，同时不让关系变僵",
    relation: "我们认识很久，但最近对方经常提出让我为难的请求。",
    habit: "比较敏感，容易追问原因，但也重视真诚。",
    title: "朋友画像",
    chatTitle: "朋友 · 拒绝请求模拟",
    style: "情绪敏感型",
    speed: "较快",
    focus: "是否被重视、理由是否真诚",
    risk: "容易把拒绝理解成疏远",
    strategy:
      "先肯定关系，再清楚说明边界；不用过度解释，但可以给出一个可接受的替代方案。",
    state: {
      trust: 72,
      respect: 68,
      familiarity: 78,
      affinity: 70,
      authority: 18,
      emotional: -8,
    },
  },
};

export const scenarioKeys = Object.keys(scenarioPresets) as ScenarioKey[];

export const stepLabels = ["开始", "场景", "人物", "画像", "模拟", "报告"];

export const stepDescriptions = [
  "选择沟通场景",
  "明确目标",
  "描述目标对象",
  "确认模拟参数",
  "多轮对话预演",
  "预测与表达优化",
];

export const stateLabels = [
  ["trust", "信任", "有合作基础"],
  ["respect", "尊重", "互动中保持礼貌"],
  ["familiarity", "熟悉", "接触频率与了解程度"],
  ["affinity", "亲近", "情感距离"],
  ["authority", "权力距离", "需要更克制和完整"],
  ["emotional", "情绪影响", "过往互动带来的情绪余量"],
] as const;
