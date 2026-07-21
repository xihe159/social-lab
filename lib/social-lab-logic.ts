import { scenarioPresets } from "./social-lab-data";
import type {
  FormData,
  Persona,
  RelationshipState,
  ScenarioKey,
  SimulationReport,
} from "./social-lab-types";

const clamp = (
  value: number,
  min = 0,
  max = 100,
) => Math.max(min, Math.min(max, value));

export function formFromScenario(
  scenario: ScenarioKey,
): FormData {
  const preset = scenarioPresets[scenario];

  return {
    goal: preset.goal,
    outcome: preset.outcome,
    role: preset.role,
    relation: preset.relation,
    habit: preset.habit,
    chatLog: "",
  };
}

export function buildPersona(
  scenario: ScenarioKey,
  form: FormData,
): Persona {
  const preset = scenarioPresets[scenario];
  const state: RelationshipState = {
    ...preset.state,
  };

  if (
    form.relation.includes("项目") ||
    form.relation.includes("合作")
  ) {
    state.trust += 4;
  }

  if (
    form.relation.includes("不熟") ||
    form.relation.includes("很少")
  ) {
    state.familiarity -= 12;
  }

  if (
    form.habit.includes("严格") ||
    form.habit.includes("领导") ||
    form.habit.includes("导师")
  ) {
    state.authority += 4;
  }

  if (form.habit.includes("敏感")) {
    state.emotional -= 8;
  }

  Object.keys(state).forEach((key) => {
    const stateKey = key as keyof RelationshipState;

    state[stateKey] = clamp(
      state[stateKey],
      stateKey === "emotional" ? -100 : 0,
    );
  });

  return {
    title: `${(form.role || preset.role).replace(/^我的/, "")}画像`,
    style: inferStyle(form.habit, preset.style),
    speed: form.habit.includes("慢")
      ? "偏慢"
      : preset.speed,
    focus: inferFocus(
      form.goal,
      form.habit,
      preset.focus,
    ),
    risk: inferRisk(form.habit, preset.risk),
    strategy: buildStrategy(
      form.goal,
      form.relation,
      preset.strategy,
    ),
    state,
  };
}

function inferStyle(
  text: string,
  fallback: string,
) {
  if (/严格|逻辑|数据/.test(text)) {
    return "理性型";
  }

  if (/敏感|情绪/.test(text)) {
    return "情绪敏感型";
  }

  if (/直接|结果/.test(text)) {
    return "结果导向";
  }

  return fallback;
}

function inferFocus(
  goal: string,
  habit: string,
  fallback: string,
) {
  if (goal.includes("推荐信")) {
    return "截止时间、材料完整度";
  }

  if (goal.includes("加薪")) {
    return "绩效证据、业务贡献";
  }

  if (goal.includes("拒绝")) {
    return "边界表达、关系维护";
  }

  if (habit.includes("逻辑")) {
    return "逻辑、背景说明";
  }

  return fallback;
}

function inferRisk(
  habit: string,
  fallback: string,
) {
  if (habit.includes("催")) {
    return "不喜欢被催促";
  }

  if (habit.includes("敏感")) {
    return "容易误解语气";
  }

  if (habit.includes("直接")) {
    return "不喜欢模糊表达";
  }

  return fallback;
}

function buildStrategy(
  goal: string,
  relation: string,
  fallback: string,
) {
  if (!goal || goal.length < 8) {
    return fallback;
  }

  const context = relation
    ? "先用你们已有关系做轻量铺垫，"
    : "";

  return `${context}把“${goal}”拆成背景、具体请求、对方成本和可选退出空间四部分表达，避免一上来直接施压。`;
}

export function firstTargetMessage(
  scenario: ScenarioKey,
) {
  if (scenario === "work") {
    return "你可以先说一下想讨论的具体事项，以及你认为目前工作量或薪酬需要调整的依据。";
  }

  if (scenario === "social") {
    return "你可以直接说，我会听。但我也希望知道你为什么不方便。";
  }

  return "你可以先把申请项目、截止时间和推荐信要求发给我，我看一下是否来得及安排。";
}

export function buildReply(
  scenario: ScenarioKey,
  text: string,
) {
  const polite = /老师|您好|请问|谢谢|麻烦|方便/.test(text);
  const hasDetail = /截止|时间|材料|项目|背景|原因|数据|成果|安排|草稿|要求/.test(
    text,
  );
  const pushy = /必须|马上|尽快|为什么不|你应该|催/.test(text);

  if (pushy) {
    if (scenario === "social") {
      return "我理解你着急，但这个说法会让我有点压力。你可以更直接说你的边界。";
    }

    return "我现在不一定能马上处理。如果事情比较急，你需要把具体截止时间和材料先说明清楚。";
  }

  if (scenario === "work") {
    return hasDetail
      ? "如果你能把过去一段时间的成果、影响和你希望调整的方案整理一下，我们可以约个时间具体谈。"
      : "这个话题可以讨论，但我需要看到更具体的依据。你先整理一下目标、贡献和期望方案。";
  }

  if (scenario === "social") {
    return polite && hasDetail
      ? "谢谢你直接说清楚。虽然我可能会有点失落，但我能理解你的安排。"
      : "我听到了，不过我还是想知道你是不方便这一次，还是以后都不太想帮这个忙？";
  }

  if (polite && hasDetail) {
    return "可以。你先把申请项目、截止时间、推荐信要求和个人材料发给我，我看一下时间是否来得及。";
  }

  if (polite) {
    return "可以先说说具体是哪类项目、什么时候截止，以及需要我提供什么内容吗？";
  }

  return "你这个请求我需要更多背景。请先说明申请项目、截止时间和你希望我如何配合。";
}

export function scoreMessage(
  currentScore: number,
  text: string,
) {
  let delta = 0;

  if (/您好|请问|谢谢|麻烦|方便/.test(text)) {
    delta += 4;
  }

  if (/截止|时间|材料|项目|背景|原因|数据|成果|安排|草稿|要求/.test(text)) {
    delta += 6;
  }

  if (/必须|马上|为什么不|你应该|催/.test(text)) {
    delta -= 10;
  }

  if (text.length < 14) {
    delta -= 3;
  }

  return clamp(currentScore + delta, 35, 88);
}

/**
 * 兼容旧页面或离线演示的本地回退报告。
 *
 * 正式报告仍应通过 createSimulationReport() 从后端生成。
 * 这里返回完整 SimulationReport，避免类型升级后静态构建失败。
 */
export function buildReport(
  scenario: ScenarioKey,
  score: number,
  hasUserMessages: boolean,
): SimulationReport {
  const finalScore = clamp(
    hasUserMessages ? score : 68,
  );
  const remaining = 100 - finalScore;
  const refuse = Math.max(
    4,
    Math.round(remaining * 0.35),
  );
  const noResponse = Math.max(
    3,
    Math.round(remaining * 0.2),
  );
  const hesitate = Math.max(
    0,
    remaining - refuse - noResponse,
  );

  const preset = scenarioPresets[scenario];
  const rewrite = buildRewrite(scenario);
  const nextStep = buildNextStep(scenario);

  const strengths = [
    "语气总体保持礼貌，没有使用明显威胁或攻击表达。",
    "当前表达包含可识别的沟通目标。",
  ];

  const problems: string[] = [];
  const risks: string[] = [];

  if (finalScore < 72) {
    problems.push(
      "背景、截止时间或对方成本说明不足，可能增加判断成本。",
    );
  }

  if (preset.state.authority > 70) {
    risks.push(
      "权力距离较高，直接请求或催促可能提高沟通压力。",
    );
  }

  if (scenario === "work") {
    problems.push(
      "职场诉求缺少成果数据时，容易被理解为主观感受。",
    );
  }

  if (scenario === "social") {
    risks.push(
      "拒绝边界不清晰时，可能引发反复追问或关系误解。",
    );
  }

  const factors = [
    ...strengths,
    ...problems,
    ...risks,
  ];

  const reason =
    finalScore >= 72
      ? "表达较清晰，并且主动降低了对方理解和行动成本，整体风险可控。"
      : "语气基本礼貌，但背景、截止时间或对方成本说明仍不足，可能让对方保持谨慎。";

  return {
    score: finalScore,
    scoreRange: {
      low: clamp(finalScore - 15),
      high: clamp(finalScore + 15),
    },
    confidence: "low",
    confidenceScore: hasUserMessages ? 40 : 25,
    evidenceSufficiency: "insufficient",

    reason,
    likelyOutcome:
      finalScore >= 72
        ? "目标人物可能愿意继续讨论或接受请求。"
        : "目标人物可能保持犹豫，并要求补充信息。",

    outcomes: [
      {
        label: "接受",
        value: finalScore,
        color: "#c8f47a",
      },
      {
        label: "条件接受",
        value: 0,
        color: "#d7e9a9",
      },
      {
        label: "犹豫",
        value: hesitate,
        color: "#f2d59b",
      },
      {
        label: "拒绝",
        value: refuse,
        color: "#e8b7b0",
      },
      {
        label: "暂不回应",
        value: noResponse,
        color: "#b9c4d3",
      },
    ],
    outcomeDistribution: {
      accept: finalScore,
      conditionalAccept: 0,
      hesitate,
      refuse,
      noResponse,
    },

    factors,
    influenceFactors: factors.map(
      (factor, index) => ({
        name: `本地回退因素 ${index + 1}`,
        direction:
          index < strengths.length
            ? "positive"
            : "negative",
        impact:
          index < strengths.length
            ? 2
            : -2,
        importance: 2,
        source: "semantic",
        metricName: null,
        metricValue: null,
        evidenceTurns: [],
        evidence: "",
        explanation: factor,
      }),
    ),

    strengths,
    problems,
    risks,

    conversationAnalysis: {
      methodologyNotice:
        "这是本地离线回退报告，没有调用 AnalysisAgent，因此不展示逐句状态归因。",
      coverage: {
        totalUserTurns: 0,
        analyzedUserTurns: 0,
        totalUserSentences: 0,
        analyzedUserSentences: 0,
        turnTraceCount: 0,
        complete: false,
      },
      overallAssessment: reason,
      strengths,
      problems,
      keyRisks: risks,
      primaryBottleneck:
        problems[0] ??
        "当前缺少足够的对话证据形成逐句评价。",
      evaluationScores: {
        clarity: finalScore,
        responsiveness: 50,
        respectAndBoundary: 60,
        responsibility: 55,
        emotionalSafety: 60,
        goalAlignment: finalScore,
        overall: finalScore,
      },
      stateTrajectorySummary:
        "本地回退模式没有完整的关系状态和 Dynamics 轨迹。",
      turns: [],
    },

    rewrite,
    sentenceRewrites: [],
    rewriteVariants: {
      minimalEdit: rewrite,
      warmerVersion: rewrite,
      firmerVersion: rewrite,
    },
    nextStep,
    doNotSay: [
      "避免命令、威胁、道德绑架或要求对方立即表态。",
    ],

    predictionTrace: {
      scenarioPrior: finalScore,
      dynamicsContribution: 0,
      relationshipContribution: 0,
      trendContribution: 0,
      semanticAdjustment: 0,
      preGuardrailScore: finalScore,
      guardrailAdjustment: 0,
      finalScore,
      uncertaintyWidth: 15,
      volatilityScore: 0,
    },
    calibrationVersion:
      "legacy-local-fallback-v1",
  };
}

export function buildRewrite(
  scenario: ScenarioKey,
) {
  if (scenario === "work") {
    return "您好，我想和您约 20 分钟讨论一下我近期的工作量和薪酬调整可能性。我先整理了过去几个月负责的项目、结果数据和后续可承担的范围，也想听听您对我目前表现和下一步成长目标的反馈。";
  }

  if (scenario === "social") {
    return "谢谢你想到我，也谢谢你愿意直接跟我说。不过这件事我这次确实不方便答应，不是针对你。为了不耽误你安排，我想早点说清楚。如果你愿意，我可以帮你一起想想其他办法。";
  }

  return "老师您好，打扰您了。我最近正在申请 XX 项目，材料中需要一封推荐信，截止时间是 XX 月 XX 日。我整理好了项目说明、个人材料和推荐信要求，也可以先提供一版草稿，尽量减少您的时间成本。想请问您是否方便帮忙？如果时间不合适，也完全理解。";
}

function buildNextStep(
  scenario: ScenarioKey,
) {
  if (scenario === "work") {
    return "整理可量化成果和期望方案，再预约一次明确时长的沟通。";
  }

  if (scenario === "social") {
    return "清楚表达本次边界，并给对方留出接受和消化的空间。";
  }

  return "补齐项目、截止时间、材料和预计占用时间后，再提出完整请求。";
}
