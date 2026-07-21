export type ScenarioKey = "advisor" | "work" | "social";

export type RelationshipState = {
  trust: number;
  respect: number;
  familiarity: number;
  affinity: number;
  authority: number;
  emotional: number;
};

export type StateDelta = {
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

export type RhythmLabel =
  | "too_fast"
  | "slightly_fast"
  | "balanced"
  | "slightly_slow"
  | "stalled";

export type AtmosphereLabel =
  | "safe"
  | "warm"
  | "neutral"
  | "tense"
  | "defensive"
  | "blocked";

export type RecommendedNextMove =
  | "advance"
  | "clarify"
  | "slow_down"
  | "repair"
  | "set_boundary"
  | "pause";

export type ConversationDynamics = {
  atmosphere_score: number;
  pace_score: number;
  pressure_level: number;
  clarity_score: number;
  responsiveness_score: number;
  progress_score: number;
  repairability_score: number;
  boundary_score: number;

  rhythm_label: RhythmLabel;
  atmosphere_label: AtmosphereLabel;
  recommended_next_move: RecommendedNextMove;
  dynamics_reason: string;
};

export type ConversationDynamicsDelta = {
  atmosphere_score: number;
  pace_score: number;
  pressure_level: number;
  clarity_score: number;
  responsiveness_score: number;
  progress_score: number;
  repairability_score: number;
  boundary_score: number;
};

export type ConversationDynamicsSnapshot = {
  turn_index: number;

  atmosphere_score: number;
  pace_score: number;
  pressure_level: number;
  clarity_score: number;
  responsiveness_score: number;
  progress_score: number;
  repairability_score: number;
  boundary_score: number;

  rhythm_label: RhythmLabel;
  atmosphere_label: AtmosphereLabel;
  recommended_next_move: RecommendedNextMove;
  reason: string;
};

export type ConversationTurnTrace = {
  turnIndex: number;
  userMessage: string;
  targetReply: string;

  relationshipBefore: RelationshipState;
  relationshipDelta: StateDelta;
  relationshipAfter: RelationshipState;

  dynamicsBefore: ConversationDynamics | null;
  dynamicsDelta: ConversationDynamicsDelta | null;
  dynamicsAfter: ConversationDynamics | null;

  riskFlags: string[];
};

export type CommunicativeFunction =
  | "context"
  | "request"
  | "question"
  | "explanation"
  | "apology"
  | "commitment"
  | "boundary"
  | "emotion"
  | "pressure"
  | "response"
  | "other";

export type SentenceEvaluationLabel =
  | "strong"
  | "effective"
  | "neutral"
  | "risky"
  | "damaging";

export type GoalEffect =
  | "supports"
  | "neutral"
  | "obstructs";

export type TargetFeeling =
  | "reassured"
  | "respected"
  | "understood"
  | "neutral"
  | "uncertain"
  | "burdened"
  | "pressured"
  | "defensive"
  | "hurt"
  | "withdrawn";

export type DynamicsMetricState = {
  atmosphere_score: number;
  pace_score: number;
  pressure_level: number;
  clarity_score: number;
  responsiveness_score: number;
  progress_score: number;
  repairability_score: number;
  boundary_score: number;
};

export type ConversationEvaluationScores = {
  clarity: number;
  responsiveness: number;
  respectAndBoundary: number;
  responsibility: number;
  emotionalSafety: number;
  goalAlignment: number;
  overall: number;
};

export type AnalysisCoverage = {
  totalUserTurns: number;
  analyzedUserTurns: number;
  totalUserSentences: number;
  analyzedUserSentences: number;
  turnTraceCount: number;
  complete: boolean;
};

export type SentenceProcessAnalysis = {
  turnIndex: number;
  sentenceIndex: number;
  sentenceText: string;

  communicativeFunction: CommunicativeFunction;
  intentSummary: string;
  targetLikelyInterpretation: string;
  targetLikelyFeeling: TargetFeeling;

  evaluationLabel: SentenceEvaluationLabel;
  evaluationScore: number;
  goalEffect: GoalEffect;
  evaluationReason: string;

  stateChangeSource:
    | "turn_delta_attribution"
    | "unavailable";
  stateChangeNote: string;

  relationshipBefore: RelationshipState | null;
  relationshipDelta: StateDelta | null;
  relationshipAfter: RelationshipState | null;

  dynamicsBefore: DynamicsMetricState | null;
  dynamicsDelta: ConversationDynamicsDelta | null;
  dynamicsAfter: DynamicsMetricState | null;
};

export type TurnProcessAnalysis = {
  turnIndex: number;
  userMessage: string;
  targetReply: string;
  turnSummary: string;
  targetReplyInterpretation: string;
  turnEvaluationScore: number;

  relationshipBefore: RelationshipState | null;
  relationshipDelta: StateDelta | null;
  relationshipAfter: RelationshipState | null;

  dynamicsBefore: DynamicsMetricState | null;
  dynamicsDelta: ConversationDynamicsDelta | null;
  dynamicsAfter: DynamicsMetricState | null;

  riskFlags: string[];
  sentences: SentenceProcessAnalysis[];
};

export type ConversationProcessAnalysis = {
  methodologyNotice: string;
  coverage: AnalysisCoverage;

  overallAssessment: string;
  strengths: string[];
  problems: string[];
  keyRisks: string[];
  primaryBottleneck: string;

  evaluationScores: ConversationEvaluationScores;
  stateTrajectorySummary: string;
  turns: TurnProcessAnalysis[];
};

export type SentenceRewrite = {
  turnIndex: number;
  sentenceIndex: number;
  originalText: string;
  rewrittenText: string;
  rewriteReason: string;
  expectedEffect: string;
};

export type RewriteVariants = {
  minimalEdit: string;
  warmerVersion: string;
  firmerVersion: string;
};

export type SimulationReport = {
  /**
   * 模拟成功评分，不应解释为现实统计概率。
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

  reason: string;
  likelyOutcome: string;

  outcomes: ReportOutcome[];
  outcomeDistribution: PredictionOutcomeDistribution;

  /**
   * 兼容旧页面。
   */
  factors: string[];
  influenceFactors: PredictionInfluenceFactor[];

  strengths: string[];
  problems: string[];
  risks: string[];

  /**
   * AnalysisAgent 报告区域。
   * 此处没有改进建议或下一步内容。
   */
  conversationAnalysis: ConversationProcessAnalysis;

  /**
   * RewriteAgent 报告区域。
   */
  rewrite: string;
  sentenceRewrites: SentenceRewrite[];
  rewriteVariants: RewriteVariants;
  nextStep: string;
  doNotSay: string[];

  predictionTrace: PredictionTrace;
  calibrationVersion: string;
};
