"use client";

import { ChevronDown, RefreshCw } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";

import { ConversationProcessAnalysisSection } from "@/components/social-lab/report/conversation-process-analysis";
import { RewriteAnalysisSection } from "@/components/social-lab/report/rewrite-analysis-section";
import type {
  PredictionInfluenceFactor,
  SimulationReport,
} from "@/lib/social-lab-types";

type ReportScreenProps = {
  report: SimulationReport;
  onCopy: () => void;
  onRetry: () => void;
};

export function ReportScreen({
  report,
  onCopy,
  onRetry,
}: ReportScreenProps) {
  const [showFullAnalysis, setShowFullAnalysis] =
    useState(false);
  const fullAnalysisRef = useRef<HTMLElement>(null);
  const topFactors = useMemo(
    () => selectTopFactors(report.influenceFactors),
    [report.influenceFactors],
  );
  const quickSummary = conciseText(
    report.conversationAnalysis.overallAssessment ||
      report.likelyOutcome,
    180,
  );

  const toggleFullAnalysis = () => {
    const nextValue = !showFullAnalysis;
    setShowFullAnalysis(nextValue);

    if (nextValue) {
      window.setTimeout(() => {
        fullAnalysisRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 0);
    }
  };

  return (
    <section
      className="screen report-screen is-current"
      style={pageStyle}
    >
      <section style={heroStyle}>
        <div style={scoreBlockStyle}>
          <p style={eyebrowStyle}>本轮结果</p>
          <div style={scoreRowStyle}>
            <strong style={scoreStyle}>{report.score}</strong>
            <span style={scoreUnitStyle}>/ 100</span>
          </div>
          <span style={resultBadgeStyle}>
            {getResultLabel(report)}
          </span>
        </div>

        <div style={heroContentStyle}>
          <div style={metaRowStyle}>
            <span style={confidenceBadgeStyle}>
              置信度：{confidenceText[report.confidence]}
            </span>
            <span style={rangeStyle}>
              预测波动范围：{report.scoreRange.low}–
              {report.scoreRange.high}
            </span>
          </div>
          <p style={reasonStyle}>{quickSummary}</p>
          <p style={outcomeStyle}>
            <strong>最可能结果：</strong>
            {report.likelyOutcome}
          </p>
        </div>
      </section>

      <section style={cardStyle}>
        <div style={sectionHeadingStyle}>
          <div>
            <p style={sectionEyebrowStyle}>关键判断</p>
            <h3 style={sectionTitleStyle}>
              最关键的三个影响
            </h3>
          </div>
          <span style={quietMetaStyle}>
            已按影响程度筛选
          </span>
        </div>

        <div style={quickFactorGridStyle}>
          {topFactors.map((factor) => (
            <article
              key={`${factor.name}-${factor.source}`}
              style={quickFactorStyle}
            >
              <div style={factorHeaderStyle}>
                <span
                  style={{
                    ...factorDirectionStyle,
                    ...(factor.direction === "positive"
                      ? positiveDirectionStyle
                      : factor.direction === "negative"
                        ? negativeDirectionStyle
                        : mixedDirectionStyle),
                  }}
                >
                  {getDirectionLabel(factor)}
                </span>
                <span style={impactTextStyle}>
                  {getImpactText(factor)}
                </span>
              </div>
              <strong>{toUserFacingName(factor.name)}</strong>
              <p style={factorExplanationStyle}>
                {conciseText(factor.explanation, 86)}
              </p>
            </article>
          ))}
        </div>

        <div style={actionStyle}>
          <div>
            <span style={actionLabelStyle}>推荐下一步</span>
            <p style={actionTextStyle}>
              {conciseText(report.nextStep, 120)}
            </p>
          </div>
          <div style={buttonRowStyle}>
            <button
              type="button"
              onClick={onRetry}
              className="primary-action"
            >
              <RefreshCw size={17} />
              用推荐版本重新模拟
            </button>
            <button
              type="button"
              onClick={toggleFullAnalysis}
              aria-expanded={showFullAnalysis}
              aria-controls="full-report-analysis"
              className="secondary-action"
            >
              {showFullAnalysis
                ? "收起完整分析"
                : "查看完整分析"}
              <ChevronDown
                size={17}
                style={{
                  transform: showFullAnalysis
                    ? "rotate(180deg)"
                    : "none",
                  transition: "transform 160ms ease",
                }}
              />
            </button>
          </div>
        </div>
      </section>

      <section style={recommendationCardStyle}>
        <RewriteAnalysisSection
          report={report}
          onCopy={onCopy}
        />
      </section>

      {showFullAnalysis && (
        <section
          id="full-report-analysis"
          ref={fullAnalysisRef}
          style={deepAnalysisStyle}
        >
          <div style={deepAnalysisHeaderStyle}>
            <div>
              <p style={sectionEyebrowStyle}>深度阅读</p>
              <h3 style={sectionTitleStyle}>完整分析依据</h3>
            </div>
            <span style={quietMetaStyle}>
              以下内容按需展开
            </span>
          </div>

          <ReportDetails title="查看结果分布">
            <div style={outcomeGridStyle}>
              {[...report.outcomes]
                .sort((a, b) => b.value - a.value)
                .map((outcome) => (
                  <div
                    key={outcome.label}
                    style={outcomeItemStyle}
                  >
                    <div style={outcomeHeaderStyle}>
                      <span>{outcome.label}</span>
                      <strong>{outcome.value}%</strong>
                    </div>
                    <div style={trackStyle}>
                      <div
                        style={{
                          ...fillStyle,
                          width: `${outcome.value}%`,
                          background: outcome.color,
                        }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          </ReportDetails>

          <ReportDetails title="查看全部影响因素">
            <div style={factorListStyle}>
              {report.influenceFactors.map((factor) => (
                <article
                  key={`${factor.name}-${factor.source}`}
                  style={factorCardStyle}
                >
                  <div style={factorHeaderStyle}>
                    <strong>
                      {toUserFacingName(factor.name)}
                    </strong>
                    <span style={impactTextStyle}>
                      {getImpactText(factor)}
                    </span>
                  </div>
                  <p style={smallParagraphStyle}>
                    {factor.explanation}
                  </p>
                  {factor.evidence && (
                    <blockquote style={quoteStyle}>
                      {factor.evidence}
                    </blockquote>
                  )}
                </article>
              ))}
            </div>
          </ReportDetails>

          <ReportDetails title="查看逐轮对话分析">
            <ConversationProcessAnalysisSection
              analysis={report.conversationAnalysis}
            />
          </ReportDetails>

          <ReportDetails title="查看关系状态变化">
            <RelationshipSummary report={report} />
          </ReportDetails>

          <ReportDetails title="查看评分依据">
            <ScoringBasis report={report} />
          </ReportDetails>
        </section>
      )}
    </section>
  );
}

function ReportDetails({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <details style={detailsStyle}>
      <summary style={detailsSummaryStyle}>
        <span>{title}</span>
        <ChevronDown size={17} aria-hidden="true" />
      </summary>
      <div style={detailsContentStyle}>{children}</div>
    </details>
  );
}

function RelationshipSummary({
  report,
}: {
  report: SimulationReport;
}) {
  const turns = report.conversationAnalysis.turns;
  const trust = sumRelationshipDelta(turns, "trust");
  const willingness =
    sumDynamicsDelta(turns, "responsiveness_score") +
    sumDynamicsDelta(turns, "atmosphere_score");
  const progress = sumDynamicsDelta(turns, "progress_score");

  return (
    <div style={relationshipWrapStyle}>
      <div style={relationshipGridStyle}>
        <StatusItem
          label="对方信任"
          status={getStatusText(trust, "trust")}
          tone={getTone(trust)}
        />
        <StatusItem
          label="沟通意愿"
          status={getStatusText(willingness, "willingness")}
          tone={getTone(willingness)}
        />
        <StatusItem
          label="目标推进"
          status={getStatusText(progress, "progress")}
          tone={getTone(progress)}
        />
      </div>
      <p style={trajectoryTextStyle}>
        {report.conversationAnalysis.stateTrajectorySummary}
      </p>
    </div>
  );
}

function StatusItem({
  label,
  status,
  tone,
}: {
  label: string;
  status: string;
  tone: "positive" | "neutral" | "negative";
}) {
  return (
    <div style={statusItemStyle}>
      <span style={quietMetaStyle}>{label}</span>
      <strong
        style={{
          color:
            tone === "positive"
              ? "var(--accent-ink)"
              : tone === "negative"
                ? "var(--primary)"
                : "var(--text-secondary)",
        }}
      >
        {status}
      </strong>
    </div>
  );
}

function ScoringBasis({
  report,
}: {
  report: SimulationReport;
}) {
  const showDeveloperDetails =
    process.env.NODE_ENV === "development";

  return (
    <div style={scoringBasisStyle}>
      <p style={smallParagraphStyle}>
        评分综合考虑场景难度、对话过程、关系变化和表达内容。
        当前证据{evidenceText[report.evidenceSufficiency]}，因此结果以
        {report.scoreRange.low}–{report.scoreRange.high}
        的波动范围呈现，而不是现实中的确定概率。
      </p>

      {showDeveloperDetails && (
        <details style={developerDetailsStyle}>
          <summary style={summaryCursorStyle}>
            开发信息
          </summary>
          <p style={developerTextStyle}>{report.reason}</p>
          <dl style={traceGridStyle}>
            <TraceItem
              label="场景基线"
              value={report.predictionTrace.scenarioPrior}
            />
            <TraceItem
              label="沟通过程"
              value={
                report.predictionTrace.dynamicsContribution
              }
            />
            <TraceItem
              label="关系变化"
              value={
                report.predictionTrace.relationshipContribution
              }
            />
            <TraceItem
              label="表达内容"
              value={
                report.predictionTrace.semanticAdjustment
              }
            />
          </dl>
        </details>
      )}
    </div>
  );
}

function TraceItem({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div style={traceItemStyle}>
      <dt>{label}</dt>
      <dd style={traceValueStyle}>
        {value > 0 ? "+" : ""}
        {value.toFixed(1)}
      </dd>
    </div>
  );
}

function selectTopFactors(
  factors: PredictionInfluenceFactor[],
) {
  const visible = factors.filter(
    (factor) => !isInternalFactor(factor),
  );
  const candidates = visible.length >= 3 ? visible : factors;
  const sorted = [...candidates].sort(
    (a, b) =>
      b.importance - a.importance ||
      Math.abs(b.impact) - Math.abs(a.impact),
  );
  const positive = sorted.find(
    (factor) => factor.direction === "positive",
  );
  const negative = sorted
    .filter((factor) => factor.direction === "negative")
    .slice(0, positive ? 2 : 3);
  const selected = positive
    ? [positive, ...negative]
    : negative;

  for (const factor of sorted) {
    if (selected.length >= 3) break;
    if (!selected.includes(factor)) selected.push(factor);
  }

  return selected.slice(0, 3);
}

function isInternalFactor(factor: PredictionInfluenceFactor) {
  return (
    factor.source === "guardrail" ||
    /护栏|先验|语义微调|算法|agent|dynamics/i.test(
      factor.name,
    )
  );
}

function toUserFacingName(name: string) {
  return name
    .replace(/PredictionAgent/gi, "结果预测")
    .replace(/AnalysisAgent/gi, "表达分析")
    .replace(/RewriteAgent/gi, "推荐表达")
    .replace(/StateAgent/gi, "关系变化")
    .replace(/Dynamics/gi, "沟通过程")
    .replace(/结果护栏修正/g, "结果校准")
    .replace(/场景先验/g, "场景背景")
    .replace(/语义微调/g, "表达内容");
}

function getImpactText(factor: PredictionInfluenceFactor) {
  const value = Math.abs(factor.impact);
  const level =
    value >= 6 ? "显著" : value >= 3 ? "中度" : "轻度";
  if (factor.direction === "mixed") return `${level}综合影响`;
  return `${level}${
    factor.direction === "positive" ? "正向" : "负向"
  }`;
}

function getDirectionLabel(factor: PredictionInfluenceFactor) {
  if (factor.direction === "positive") return "有利";
  if (factor.direction === "negative") return "阻碍";
  return "双向";
}

function getResultLabel(report: SimulationReport) {
  if (report.score >= 75) return "推进较顺利";
  if (report.score >= 45) return "有条件可推进";
  return "当前推进受阻";
}

function conciseText(value: string, maxLength: number) {
  const cleaned = value.replace(/\s+/g, " ").trim();
  if (cleaned.length <= maxLength) return cleaned;

  const punctuationIndex = Math.max(
    cleaned.lastIndexOf("。", maxLength),
    cleaned.lastIndexOf("！", maxLength),
    cleaned.lastIndexOf("？", maxLength),
  );
  if (punctuationIndex >= Math.floor(maxLength * 0.58)) {
    return cleaned.slice(0, punctuationIndex + 1);
  }
  return `${cleaned.slice(0, maxLength - 1)}…`;
}

function sumRelationshipDelta(
  turns: SimulationReport["conversationAnalysis"]["turns"],
  key: keyof NonNullable<
    SimulationReport["conversationAnalysis"]["turns"][number]["relationshipDelta"]
  >,
) {
  return turns.reduce((sum, turn) => {
    const delta = turn.relationshipDelta;
    return sum + (delta ? Number(delta[key]) : 0);
  }, 0);
}

function sumDynamicsDelta(
  turns: SimulationReport["conversationAnalysis"]["turns"],
  key: keyof NonNullable<
    SimulationReport["conversationAnalysis"]["turns"][number]["dynamicsDelta"]
  >,
) {
  return turns.reduce((sum, turn) => {
    const delta = turn.dynamicsDelta;
    return sum + (delta ? Number(delta[key]) : 0);
  }, 0);
}

function getTone(value: number) {
  if (value > 0) return "positive" as const;
  if (value < 0) return "negative" as const;
  return "neutral" as const;
}

function getStatusText(
  value: number,
  type: "trust" | "willingness" | "progress",
) {
  if (value >= 3) return "明显上升";
  if (value > 0) return "小幅上升";
  if (value === 0) return "基本稳定";
  if (value <= -3) {
    return type === "progress" ? "暂时受阻" : "明显下降";
  }
  return "小幅下降";
}

const confidenceText = {
  low: "低",
  medium: "中",
  high: "高",
} as const;

const evidenceText = {
  insufficient: "较少",
  partial: "部分充分",
  sufficient: "较充分",
} as const;

const pageStyle: CSSProperties = {
  display: "grid",
  gap: 18,
};

const heroStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns:
    "repeat(auto-fit, minmax(min(100%, 270px), 1fr))",
  gap: 26,
  padding: 24,
  borderRadius: 12,
  background:
    "linear-gradient(135deg, var(--lavender), var(--accent-soft))",
  border: "1px solid var(--border-soft)",
  boxShadow: "var(--shadow-card)",
};

const scoreBlockStyle: CSSProperties = {
  display: "grid",
  alignContent: "center",
  justifyItems: "start",
};

const eyebrowStyle: CSSProperties = {
  margin: 0,
  fontSize: 13,
  fontWeight: 700,
  color: "var(--text-secondary)",
};

const scoreRowStyle: CSSProperties = {
  display: "flex",
  alignItems: "baseline",
  gap: 5,
  marginTop: 8,
};

const scoreStyle: CSSProperties = {
  color: "var(--primary)",
  fontSize: "clamp(52px, 9vw, 72px)",
  lineHeight: 0.95,
};

const scoreUnitStyle: CSSProperties = {
  fontSize: 13,
  color: "var(--text-secondary)",
};

const resultBadgeStyle: CSSProperties = {
  marginTop: 12,
  padding: "6px 10px",
  borderRadius: 999,
  color: "var(--primary)",
  background: "rgba(255, 255, 255, 0.72)",
  border: "1px solid rgba(47, 47, 99, 0.12)",
  fontSize: 13,
  fontWeight: 800,
};

const heroContentStyle: CSSProperties = {
  display: "grid",
  alignContent: "center",
  gap: 10,
};

const metaRowStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 9,
  flexWrap: "wrap",
};

const confidenceBadgeStyle: CSSProperties = {
  padding: "5px 9px",
  borderRadius: 999,
  background: "rgba(47, 47, 99, 0.1)",
  color: "var(--primary)",
  fontSize: 12,
  fontWeight: 700,
};

const rangeStyle: CSSProperties = {
  fontSize: 12,
  color: "var(--text-secondary)",
};

const reasonStyle: CSSProperties = {
  margin: 0,
  fontSize: 16,
  lineHeight: 1.75,
};

const outcomeStyle: CSSProperties = {
  margin: 0,
  lineHeight: 1.65,
  color: "var(--text-secondary)",
};

const cardStyle: CSSProperties = {
  padding: 22,
  borderRadius: 12,
  border: "1px solid var(--border)",
  background: "var(--surface)",
  boxShadow: "var(--shadow-soft)",
};

const sectionHeadingStyle: CSSProperties = {
  display: "flex",
  alignItems: "flex-end",
  justifyContent: "space-between",
  gap: 12,
  marginBottom: 16,
};

const sectionEyebrowStyle: CSSProperties = {
  margin: 0,
  color: "var(--primary-muted)",
  fontSize: 12,
  fontWeight: 800,
  letterSpacing: "0.08em",
};

const sectionTitleStyle: CSSProperties = {
  margin: "4px 0 0",
  fontSize: 21,
};

const quietMetaStyle: CSSProperties = {
  color: "var(--text-secondary)",
  fontSize: 12,
};

const quickFactorGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
  gap: 10,
};

const quickFactorStyle: CSSProperties = {
  display: "grid",
  alignContent: "start",
  gap: 8,
  minHeight: 128,
  padding: 16,
  borderRadius: 12,
  background: "var(--bg-soft)",
  border: "1px solid var(--border-soft)",
};

const factorHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 10,
};

const factorDirectionStyle: CSSProperties = {
  padding: "3px 7px",
  borderRadius: 999,
  fontSize: 11,
  fontWeight: 800,
};

const positiveDirectionStyle: CSSProperties = {
  color: "var(--accent-ink)",
  background: "var(--accent-soft)",
};

const negativeDirectionStyle: CSSProperties = {
  color: "var(--text-main)",
  background: "var(--peach)",
};

const mixedDirectionStyle: CSSProperties = {
  color: "var(--text-main)",
  background: "var(--amber)",
};

const impactTextStyle: CSSProperties = {
  color: "var(--text-secondary)",
  fontSize: 12,
};

const factorExplanationStyle: CSSProperties = {
  display: "-webkit-box",
  margin: 0,
  overflow: "hidden",
  WebkitBoxOrient: "vertical",
  WebkitLineClamp: 2,
  color: "var(--text-secondary)",
  fontSize: 13,
  lineHeight: 1.65,
};

const actionStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns:
    "repeat(auto-fit, minmax(min(100%, 280px), 1fr))",
  alignItems: "center",
  gap: 18,
  marginTop: 14,
  padding: 18,
  borderRadius: 12,
  background: "var(--accent-soft)",
};

const actionLabelStyle: CSSProperties = {
  color: "var(--accent-ink)",
  fontSize: 12,
  fontWeight: 800,
};

const actionTextStyle: CSSProperties = {
  margin: "5px 0 0",
  lineHeight: 1.65,
};

const buttonRowStyle: CSSProperties = {
  display: "flex",
  gap: 9,
  flexWrap: "wrap",
};

const recommendationCardStyle: CSSProperties = {
  ...cardStyle,
  background: "var(--lavender)",
  borderColor: "#dfd9f4",
};

const deepAnalysisStyle: CSSProperties = {
  display: "grid",
  gap: 10,
  scrollMarginTop: 18,
};

const deepAnalysisHeaderStyle: CSSProperties = {
  ...sectionHeadingStyle,
  marginBottom: 2,
  padding: "4px 2px",
};

const detailsStyle: CSSProperties = {
  borderRadius: 12,
  border: "1px solid var(--border)",
  background: "var(--surface)",
  overflow: "hidden",
};

const detailsSummaryStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  padding: "15px 17px",
  cursor: "pointer",
  color: "var(--primary)",
  fontWeight: 800,
  listStyle: "none",
};

const detailsContentStyle: CSSProperties = {
  padding: "2px 17px 17px",
};

const outcomeGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
  gap: 10,
};

const outcomeItemStyle: CSSProperties = {
  padding: 14,
  borderRadius: 12,
  background: "var(--bg-soft)",
};

const outcomeHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 10,
};

const trackStyle: CSSProperties = {
  height: 6,
  borderRadius: 999,
  background: "var(--line)",
  overflow: "hidden",
  marginTop: 9,
};

const fillStyle: CSSProperties = {
  height: "100%",
  borderRadius: 999,
};

const factorListStyle: CSSProperties = {
  display: "grid",
  gap: 10,
};

const factorCardStyle: CSSProperties = {
  padding: 16,
  borderRadius: 12,
  background: "var(--bg-soft)",
};

const smallParagraphStyle: CSSProperties = {
  margin: "6px 0 0",
  fontSize: 13,
  lineHeight: 1.65,
};

const quoteStyle: CSSProperties = {
  margin: "8px 0 0",
  paddingLeft: 10,
  borderLeft: "2px solid var(--primary-muted)",
  fontSize: 12,
  lineHeight: 1.6,
  color: "var(--text-secondary)",
};

const relationshipWrapStyle: CSSProperties = {
  display: "grid",
  gap: 12,
};

const relationshipGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
  gap: 10,
};

const statusItemStyle: CSSProperties = {
  display: "grid",
  gap: 5,
  padding: 16,
  borderRadius: 12,
  background: "var(--bg-soft)",
};

const trajectoryTextStyle: CSSProperties = {
  margin: 0,
  padding: 16,
  borderRadius: 12,
  background: "var(--primary-soft)",
  fontSize: 13,
  lineHeight: 1.65,
};

const scoringBasisStyle: CSSProperties = {
  display: "grid",
  gap: 12,
};

const developerDetailsStyle: CSSProperties = {
  padding: 14,
  borderRadius: 12,
  border: "1px dashed var(--border)",
};

const summaryCursorStyle: CSSProperties = {
  cursor: "pointer",
  fontSize: 12,
  fontWeight: 700,
};

const developerTextStyle: CSSProperties = {
  margin: "10px 0 0",
  color: "var(--text-secondary)",
  fontSize: 12,
  lineHeight: 1.65,
};

const traceGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
  gap: 8,
  margin: "10px 0 0",
};

const traceItemStyle: CSSProperties = {
  padding: 12,
  borderRadius: 12,
  background: "var(--bg-soft)",
  fontSize: 12,
};

const traceValueStyle: CSSProperties = {
  margin: "3px 0 0",
  fontWeight: 800,
};
