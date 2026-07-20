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

export type PredictionFactorDirection =
  | "positive"
  | "negative"
  | "mixed";

export type PredictionFactorSource =
  | "scenario_prior"
  | "dynamic"
  | "relationship"
  | "trend"
  | "semantic"
  | "guardrail";

export type PredictionInfluenceFactor = {
  name: string;
  direction: PredictionFactorDirection;
  impact: number;
  importance: number;
  source: PredictionFactorSource;
  metricName?: string | null;
  metricValue?: number | null;
  evidenceTurns: number[];
  evidence: string;
  explanation: string;
};

export type PredictionOutcomeDistribution = {
  accept: number;
  conditionalAccept: number;
  hesitate: number;
  refuse: number;
  noResponse: number;
};

export type PredictionTrace = {
  scenarioPrior: number;
  dynamicsContribution: number;
  relationshipContribution: number;
  trendContribution: number;
  semanticAdjustment: number;
  preGuardrailScore: number;
  guardrailAdjustment: number;
  finalScore: number;
  uncertaintyWidth: number;
  volatilityScore: number;
};

export type SimulationReport = {
  /**
   * 模拟成功评分，不应解释为经过现实样本校准的真实概率。
   */
  score: number;

  scoreRange: {
    low: number;
    high: number;
  };

  confidence: "low" | "medium" | "high";
  confidenceScore: number;
  evidenceSufficiency:
    | "insufficient"
    | "partial"
    | "sufficient";

  /**
   * 当前保留 reason 以兼容旧报告页面。
   * 其内容为 Prediction V2 的 probability_reasoning。
   */
  reason: string;
  likelyOutcome: string;

  outcomes: ReportOutcome[];
  outcomeDistribution: PredictionOutcomeDistribution;

  /**
   * 兼容旧页面的字符串因素列表。
   * 新页面优先使用 influenceFactors。
   */
  factors: string[];
  influenceFactors: PredictionInfluenceFactor[];

  strengths: string[];
  problems: string[];
  risks: string[];

  rewrite: string;
  nextStep: string;

  predictionTrace: PredictionTrace;
  calibrationVersion: string;
};
