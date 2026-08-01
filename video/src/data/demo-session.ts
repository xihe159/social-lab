export const demoSession = {
  scenario: "advisor",
  goal: "请求导师提供研究生申请推荐信",
  urgency: "本周内需要确认",
  desiredOutcome: "导师愿意查看材料并确认是否可以提供推荐",
  concern: "担心截止时间较近，给导师造成时间压力",
  person: {
    role: "研究生导师",
    relation: "合作顺畅，但平时联系不多",
    habit: "回复较慢，比较严谨，喜欢有逻辑和证据",
    chatLog: [
      "学生：老师您好，上次项目材料我已经按建议补充。",
      "导师：收到。请把数据来源和时间安排一并标清楚。",
    ],
  },
  persona: {
    title: "研究生导师 · 画像已生成",
    style: "理性、直接、重视准备程度",
    speed: "偏慢",
    focus: "材料完整性与时间安排",
    risk: "临近截止日期才提出请求",
    strategy:
      "先说明申请信息和截止时间，再明确已经准备好的材料，降低对方的额外工作量。",
  },
  initialState: {
    trust: 63,
    emotional: 8,
    pressure: 42,
    openness: 58,
  },
  messages: [
    {
      role: "user",
      text:
        "老师您好，我正在准备研究生申请，想请您帮忙写一封推荐信。学校截止时间是下月 15 日，我已经整理好了项目清单和材料说明。",
    },
    {
      role: "target",
      text:
        "可以。你先把申请项目、截止时间和推荐要求发给我，我确认一下时间安排。",
    },
  ],
  dynamicsAfterTurn: {
    trust: 66,
    willingness: 61,
    progress: 45,
    pressure: 40,
  },
  report: {
    score: 78,
    confidence: "中",
    range: [72, 83],
    resultLabel: "推进较顺利",
    likelyOutcome:
      "导师愿意查看材料，并在确认时间安排后决定是否提供推荐。",
    summary:
      "请求信息完整、材料准备充分，降低了导师判断成本；时间较紧仍然是主要风险。",
    factors: [
      {
        direction: "positive",
        title: "信息完整",
        impact: "显著正向",
      },
      {
        direction: "positive",
        title: "降低额外工作量",
        impact: "中度正向",
      },
      {
        direction: "negative",
        title: "截止时间较近",
        impact: "中度负向",
      },
    ],
    nextStep: "立即发送完整材料包，并明确最晚确认时间。",
    rewrite:
      "老师您好，我正在准备研究生申请，想请问您是否方便为我提供一封推荐信。学校最晚下月 15 日提交，我已经整理好项目清单、个人陈述和推荐要求。如果您时间上不方便，也请直接告诉我，我可以尽快调整安排。",
  },
} as const;

export type DemoSession = typeof demoSession;
