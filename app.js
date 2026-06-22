const scenarioPresets = {
  advisor: {
    label: "导师沟通",
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
    strategy: "先说明申请背景和截止时间，再提出请求；主动提供材料、草稿和时间安排，降低对方时间成本。",
    state: { trust: 65, respect: 80, familiarity: 45, affinity: 35, authority: 90, emotional: 10 },
  },
  work: {
    label: "职场沟通",
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
    strategy: "先用具体成果建立讨论基础，再提出诉求和可衡量方案，避免只强调个人感受。",
    state: { trust: 58, respect: 72, familiarity: 52, affinity: 38, authority: 82, emotional: 5 },
  },
  social: {
    label: "社交沟通",
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
    strategy: "先肯定关系，再清楚说明边界；不用过度解释，但可以给出一个可接受的替代方案。",
    state: { trust: 72, respect: 68, familiarity: 78, affinity: 70, authority: 18, emotional: -8 },
  },
};

const stateLabels = [
  ["trust", "信任", "有合作基础"],
  ["respect", "尊重", "互动中保持礼貌"],
  ["familiarity", "熟悉", "接触频率与了解程度"],
  ["affinity", "亲近", "情感距离"],
  ["authority", "权力距离", "需要更克制和完整"],
  ["emotional", "情绪影响", "过往互动带来的情绪余量"],
];

const appState = {
  step: 0,
  scenario: "advisor",
  messages: [],
  score: 68,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function setStep(nextStep) {
  const clamped = Math.max(0, Math.min(5, nextStep));
  appState.step = clamped;
  $$(".screen").forEach((screen, index) => screen.classList.toggle("is-current", index === clamped));
  $$(".step-item").forEach((item, index) => item.classList.toggle("is-active", index === clamped));
  $("#progressFill").style.width = `${((clamped + 1) / 6) * 100}%`;
  const labels = ["开始", "场景", "人物", "画像", "模拟", "报告"];
  $("#mobileStepLabel").textContent = `Step ${clamped + 1} / 6 - ${labels[clamped]}`;
  $(".sidebar").classList.remove("is-open");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function applyPreset(name) {
  const preset = scenarioPresets[name];
  appState.scenario = name;
  $$(`input[name="scenario"]`).forEach((input) => {
    input.checked = input.value === name;
  });
  $("#goalInput").value = preset.goal;
  $("#outcomeInput").value = preset.outcome;
  $("#roleInput").value = preset.role;
  $("#relationInput").value = preset.relation;
  $("#habitInput").value = preset.habit;
}

function currentPreset() {
  return scenarioPresets[appState.scenario];
}

function generatePersona() {
  const preset = currentPreset();
  const role = $("#roleInput").value.trim() || preset.role;
  const habit = $("#habitInput").value.trim();
  const relation = $("#relationInput").value.trim();
  const goal = $("#goalInput").value.trim();

  $("#personaTitle").textContent = `${role.replace(/^我的/, "")}画像`;
  $("#styleTrait").textContent = inferStyle(habit, preset.style);
  $("#speedTrait").textContent = habit.includes("慢") ? "偏慢" : preset.speed;
  $("#focusTrait").textContent = inferFocus(goal, habit, preset.focus);
  $("#riskTrait").textContent = inferRisk(habit, preset.risk);
  $("#strategyText").textContent = buildStrategy(goal, relation, preset.strategy);
  renderStateList(adjustState(preset.state, relation, habit));
  setStep(3);
}

function inferStyle(text, fallback) {
  if (text.includes("严格") || text.includes("逻辑") || text.includes("数据")) return "理性型";
  if (text.includes("敏感") || text.includes("情绪")) return "情绪敏感型";
  if (text.includes("直接") || text.includes("结果")) return "结果导向";
  return fallback;
}

function inferFocus(goal, habit, fallback) {
  if (goal.includes("推荐信")) return "截止时间、材料完整度";
  if (goal.includes("加薪")) return "绩效证据、业务贡献";
  if (goal.includes("拒绝")) return "边界表达、关系维护";
  if (habit.includes("逻辑")) return "逻辑、背景说明";
  return fallback;
}

function inferRisk(habit, fallback) {
  if (habit.includes("催")) return "不喜欢被催促";
  if (habit.includes("敏感")) return "容易误解语气";
  if (habit.includes("直接")) return "不喜欢模糊表达";
  return fallback;
}

function buildStrategy(goal, relation, fallback) {
  if (!goal || goal.length < 8) return fallback;
  const context = relation ? "先用你们已有关系做轻量铺垫，" : "";
  return `${context}把“${goal}”拆成背景、具体请求、对方成本和可选退出空间四部分表达，避免一上来直接施压。`;
}

function adjustState(base, relation, habit) {
  const state = { ...base };
  if (relation.includes("项目") || relation.includes("合作")) state.trust += 4;
  if (relation.includes("不熟") || relation.includes("很少")) state.familiarity -= 12;
  if (habit.includes("严格") || habit.includes("领导") || habit.includes("导师")) state.authority += 4;
  if (habit.includes("敏感")) state.emotional -= 8;
  Object.keys(state).forEach((key) => {
    const min = key === "emotional" ? -100 : 0;
    state[key] = Math.max(min, Math.min(100, state[key]));
  });
  appState.relationshipState = state;
  return state;
}

function renderStateList(state = currentPreset().state) {
  $("#stateList").innerHTML = stateLabels
    .map(([key, label, desc]) => {
      const value = state[key];
      const normalized = key === "emotional" ? Math.max(0, value + 50) : value;
      const readable = key === "emotional" ? (value >= 0 ? `+${value}` : value) : value;
      return `
        <div class="state-row">
          <div class="state-row-header">
            <span>${label}</span>
            <span>${readable}</span>
          </div>
          <small>${desc}</small>
          <div class="meter"><span style="--value:${normalized}%"></span></div>
        </div>
      `;
    })
    .join("");
}

function startChat() {
  const preset = currentPreset();
  $("#chatTitle").textContent = preset.chatTitle;
  $("#chatSubline").textContent = "当前态度：谨慎";
  $("#focusChip").textContent = `对方目前关注：${$("#focusTrait").textContent}`;
  appState.messages = [
    {
      role: "target",
      text: firstTargetMessage(),
    },
  ];
  renderChat();
  setStep(4);
}

function firstTargetMessage() {
  const scenario = appState.scenario;
  if (scenario === "work") return "你可以先说一下想讨论的具体事项，以及你认为目前工作量或薪酬需要调整的依据。";
  if (scenario === "social") return "你可以直接说，我会听。但我也希望知道你为什么不方便。";
  return "你可以先把申请项目、截止时间和推荐信要求发给我，我看一下是否来得及安排。";
}

function renderChat() {
  $("#chatWindow").innerHTML = appState.messages
    .map((message) => `<p class="bubble ${message.role === "user" ? "user" : "target"}">${escapeHtml(message.text)}</p>`)
    .join("");
  $("#chatWindow").scrollTop = $("#chatWindow").scrollHeight;
}

function sendMessage() {
  const input = $("#messageInput");
  const text = input.value.trim();
  if (!text) {
    showToast("先输入一句想演练的话。");
    return;
  }
  appState.messages.push({ role: "user", text });
  appState.messages.push({ role: "target", text: buildReply(text) });
  input.value = "";
  updateScoreFromText(text);
  renderChat();
}

function buildReply(text) {
  const scenario = appState.scenario;
  const polite = /老师|您好|请问|谢谢|麻烦|方便/.test(text);
  const hasDetail = /截止|时间|材料|项目|背景|原因|数据|成果|安排|草稿|要求/.test(text);
  const pushy = /必须|马上|尽快|为什么不|你应该|催/.test(text);

  if (pushy) {
    if (scenario === "social") return "我理解你着急，但这个说法会让我有点压力。你可以更直接说你的边界。";
    return "我现在不一定能马上处理。如果事情比较急，你需要把具体截止时间和材料先说明清楚。";
  }

  if (scenario === "work") {
    if (hasDetail) return "如果你能把过去一段时间的成果、影响和你希望调整的方案整理一下，我们可以约个时间具体谈。";
    return "这个话题可以讨论，但我需要看到更具体的依据。你先整理一下目标、贡献和期望方案。";
  }

  if (scenario === "social") {
    if (polite && hasDetail) return "谢谢你直接说清楚。虽然我可能会有点失落，但我能理解你的安排。";
    return "我听到了，不过我还是想知道你是不方便这一次，还是以后都不太想帮这个忙？";
  }

  if (polite && hasDetail) return "可以。你先把申请项目、截止时间、推荐信要求和个人材料发给我，我看一下时间是否来得及。";
  if (polite) return "可以先说说具体是哪类项目、什么时候截止，以及需要我提供什么内容吗？";
  return "你这个请求我需要更多背景。请先说明申请项目、截止时间和你希望我如何配合。";
}

function updateScoreFromText(text) {
  let delta = 0;
  if (/您好|请问|谢谢|麻烦|方便/.test(text)) delta += 4;
  if (/截止|时间|材料|项目|背景|原因|数据|成果|安排|草稿|要求/.test(text)) delta += 6;
  if (/必须|马上|为什么不|你应该|催/.test(text)) delta -= 10;
  if (text.length < 14) delta -= 3;
  appState.score = Math.max(35, Math.min(88, appState.score + delta));
}

function finishSimulation() {
  renderReport();
  setStep(5);
}

function renderReport() {
  const score = appState.messages.filter((m) => m.role === "user").length ? appState.score : 68;
  const hesitate = Math.max(8, Math.min(34, 88 - score));
  const reject = Math.max(4, Math.round((100 - score) * 0.22));
  const ignore = Math.max(3, 100 - score - hesitate - reject);
  const adjustedHesitate = 100 - score - reject - ignore;
  const outcomes = [
    ["接受", score, "#4563f4"],
    ["犹豫", adjustedHesitate, "#f0b84f"],
    ["拒绝", reject, "#de6b64"],
    ["冷处理", ignore, "#8fa0b8"],
  ];

  $("#successScore").textContent = `${score}%`;
  $("#scoreReason").textContent = score >= 72
    ? "表达较清晰，并且主动降低了对方理解和行动成本，整体风险可控。"
    : "语气基本礼貌，但背景、截止时间或对方成本说明仍不足，可能让对方保持谨慎。";
  $("#outcomeList").innerHTML = outcomes
    .map(([label, value, color]) => `
      <div class="outcome-row">
        <span>${label}</span>
        <div class="outcome-bar"><span style="--value:${value}%; --color:${color}"></span></div>
        <b>${value}%</b>
      </div>
    `)
    .join("");

  $("#factorList").innerHTML = buildFactors(score).map((factor) => `<li>${factor}</li>`).join("");
  $("#rewriteText").textContent = buildRewrite();
}

function buildFactors(score) {
  const preset = currentPreset();
  const factors = ["语气礼貌，没有直接施压", "已有关系基础让请求更容易被理解"];
  if (score < 72) factors.push("背景和截止时间说明不足，可能增加对方判断成本");
  if (preset.state.authority > 70) factors.push("权力距离较高，直接请求容易造成压力");
  if (appState.scenario === "work") factors.push("需要用成果数据支撑诉求，而不是只表达感受");
  if (appState.scenario === "social") factors.push("需要在清楚拒绝和维护关系之间保持平衡");
  return factors;
}

function buildRewrite() {
  if (appState.scenario === "work") {
    return "您好，我想和您约 20 分钟讨论一下我近期的工作量和薪酬调整可能性。我先整理了过去几个月负责的项目、结果数据和后续可承担的范围，也想听听您对我目前表现和下一步成长目标的反馈。";
  }
  if (appState.scenario === "social") {
    return "谢谢你想到我，也谢谢你愿意直接跟我说。不过这件事我这次确实不方便答应，不是针对你。为了不耽误你安排，我想早点说清楚。如果你愿意，我可以帮你一起想想其他办法。";
  }
  return "老师您好，打扰您了。我最近正在申请 XX 项目，材料中需要一封推荐信，截止时间是 XX 月 XX 日。我整理好了项目说明、个人材料和推荐信要求，也可以先提供一版草稿，尽量减少您的时间成本。想请问您是否方便帮忙？如果时间不合适，也完全理解。";
}

function resetChat() {
  appState.score = 68;
  startChat();
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.setTimeout(() => toast.classList.remove("is-visible"), 1800);
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

function bindEvents() {
  $$("[data-next]").forEach((button) => button.addEventListener("click", () => {
    if (appState.step === 1 && !$("#goalInput").value.trim()) {
      showToast("请至少填写沟通目标。");
      return;
    }
    setStep(appState.step + 1);
  }));

  $$(".step-item").forEach((button) => button.addEventListener("click", () => setStep(Number(button.dataset.stepJump))));
  $$(".scenario-card").forEach((card) => card.addEventListener("click", () => {
    applyPreset(card.dataset.preset);
    setStep(1);
  }));
  $$(`input[name="scenario"]`).forEach((input) => input.addEventListener("change", () => applyPreset(input.value)));

  $("#loadAdvisorDemo").addEventListener("click", () => {
    applyPreset("advisor");
    setStep(1);
  });
  $("#generatePersona").addEventListener("click", generatePersona);
  $("#startChat").addEventListener("click", startChat);
  $("#sendMessage").addEventListener("click", sendMessage);
  $("#messageInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") sendMessage();
  });
  $("#finishSimulation").addEventListener("click", finishSimulation);
  $("#resetChat").addEventListener("click", resetChat);
  $("#backButton").addEventListener("click", () => setStep(appState.step - 1));
  $("#menuButton").addEventListener("click", () => $(".sidebar").classList.toggle("is-open"));
  $("#tunePersona").addEventListener("click", () => showToast("初版已预留编辑入口，后续可接 Persona 更新接口。"));
  $("#copyRewrite").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText($("#rewriteText").textContent);
      showToast("已复制优化表达。");
    } catch {
      showToast("复制失败，可以直接选中文本复制。");
    }
  });
  $("#retryWithRewrite").addEventListener("click", () => {
    startChat();
    $("#messageInput").value = $("#rewriteText").textContent;
  });
}

bindEvents();
renderStateList();
