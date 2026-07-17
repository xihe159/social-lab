export type ScenarioKey = "advisor" | "work" | "social";

export type RelationshipState = {
  trust: number;
  respect: number;
  familiarity: number;
  affinity: number;
  authority: number;
  emotional: number;
};

export type ScenarioPreset = {
  label: string;
  summary: string;
  role: string;
  goal: string;
  outcome: string;
  relation: string;
  habit: string;
  title: string;
  chatTitle: string;
  style: string;
  speed: string;
  focus: string;
  risk: string;
  strategy: string;
  state: RelationshipState;
};

export type Persona = {
  title: string;
  style: string;
  speed: string;
  focus: string;
  risk: string;
  strategy: string;
  state: RelationshipState;
};

export type FormData = {
  goal: string;
  outcome: string;
  role: string;
  relation: string;
  habit: string;
  chatLog: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "target" | "system";
  text: string;
};

export type ReportOutcome = {
  label: string;
  value: number;
  color: string;
};

export type SimulationReport = {
  score: number;
  reason: string;
  outcomes: ReportOutcome[];

  /**
   * AnalysisAgent 生成的主要影响因素。
   * 这里只放事实、问题、优势和风险，不放行动建议。
   */
  factors: string[];

  /**
   * AnalysisAgent 生成的下一步行动。
   */
  nextStepAdvice: string;

  /**
   * RewriteAgent 生成的推荐话术。
   */
  rewrite: string;
};
