import type { CSSProperties } from "react";

import type {
  SimulationReport,
} from "@/lib/social-lab-types";
import {
  ConversationProcessAnalysisSection,
} from "@/components/social-lab/report/conversation-process-analysis";
import {
  RewriteAnalysisSection,
} from "@/components/social-lab/report/rewrite-analysis-section";

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
  return (
    <div style={pageStyle}>
      <section style={heroStyle}>
        <div>
          <p style={eyebrowStyle}>本轮复盘报告</p>
          <h2 style={scoreStyle}>
            {report.score}
          </h2>
          <p style={scoreCaptionStyle}>
            模拟成功评分
          </p>
        </div>

        <div style={heroContentStyle}>
          <p style={rangeStyle}>
            合理区间 {report.scoreRange.low}–
            {report.scoreRange.high}
          </p>
          <p style={metaStyle}>
            置信度：{confidenceText[report.confidence]}
            {" · "}
            证据：
            {evidenceText[
              report.evidenceSufficiency
            ]}
          </p>
          <p style={reasonStyle}>{report.reason}</p>
          <p style={outcomeStyle}>
            <strong>可能结果：</strong>
            {report.likelyOutcome}
          </p>
        </div>
      </section>

      <section style={cardStyle}>
        <h3 style={sectionTitleStyle}>可能结果分布</h3>
        <div style={outcomeGridStyle}>
          {report.outcomes.map((outcome) => (
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
      </section>

      <section style={cardStyle}>
        <h3 style={sectionTitleStyle}>
          主要影响因素
        </h3>
        <div style={factorListStyle}>
          {report.influenceFactors.map((factor) => (
            <article
              key={`${factor.name}-${factor.source}`}
              style={factorCardStyle}
            >
              <div style={factorHeaderStyle}>
                <strong>{factor.name}</strong>
                <span>
                  {factor.impact >= 0 ? "+" : ""}
                  {factor.impact.toFixed(1)}
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
      </section>

      <section style={cardStyle}>
        <ConversationProcessAnalysisSection
          analysis={report.conversationAnalysis}
        />
      </section>

      <section style={cardStyle}>
        <RewriteAnalysisSection
          report={report}
          onCopy={onCopy}
          onRetry={onRetry}
        />
      </section>
    </div>
  );
}

const confidenceText = {
  low: "低",
  medium: "中",
  high: "高",
} as const;

const evidenceText = {
  insufficient: "不足",
  partial: "部分充分",
  sufficient: "充分",
} as const;

const pageStyle: CSSProperties = {
  display: "grid",
  gap: 18,
};

const heroStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "150px minmax(0, 1fr)",
  gap: 24,
  padding: 22,
  borderRadius: 22,
  background: "rgba(0, 0, 0, 0.045)",
};

const eyebrowStyle: CSSProperties = {
  margin: 0,
  fontSize: 13,
  opacity: 0.62,
};

const scoreStyle: CSSProperties = {
  margin: "8px 0 0",
  fontSize: 58,
  lineHeight: 1,
};

const scoreCaptionStyle: CSSProperties = {
  margin: "6px 0 0",
  opacity: 0.65,
};

const heroContentStyle: CSSProperties = {
  display: "grid",
  alignContent: "center",
  gap: 7,
};

const rangeStyle: CSSProperties = {
  margin: 0,
  fontWeight: 700,
};

const metaStyle: CSSProperties = {
  margin: 0,
  fontSize: 13,
  opacity: 0.65,
};

const reasonStyle: CSSProperties = {
  margin: "5px 0 0",
  lineHeight: 1.75,
};

const outcomeStyle: CSSProperties = {
  margin: 0,
  lineHeight: 1.7,
};

const cardStyle: CSSProperties = {
  padding: 20,
  borderRadius: 20,
  border: "1px solid rgba(0, 0, 0, 0.09)",
};

const sectionTitleStyle: CSSProperties = {
  margin: "0 0 14px",
  fontSize: 20,
};

const outcomeGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns:
    "repeat(auto-fit, minmax(160px, 1fr))",
  gap: 10,
};

const outcomeItemStyle: CSSProperties = {
  padding: 12,
  borderRadius: 12,
  background: "rgba(0, 0, 0, 0.03)",
};

const outcomeHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 10,
};

const trackStyle: CSSProperties = {
  height: 6,
  borderRadius: 999,
  background: "rgba(0, 0, 0, 0.08)",
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
  padding: 13,
  borderRadius: 13,
  background: "rgba(0, 0, 0, 0.03)",
};

const factorHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
};

const smallParagraphStyle: CSSProperties = {
  margin: "6px 0 0",
  fontSize: 13,
  lineHeight: 1.65,
};

const quoteStyle: CSSProperties = {
  margin: "8px 0 0",
  paddingLeft: 10,
  borderLeft: "2px solid currentColor",
  fontSize: 12,
  lineHeight: 1.6,
  opacity: 0.7,
};
