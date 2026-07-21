import { Copy, RefreshCw } from "lucide-react";
import type { CSSProperties } from "react";

import type {
  SimulationReport,
} from "@/lib/social-lab-types";

type RewriteAnalysisSectionProps = {
  report: SimulationReport;
  onCopy: () => void;
  onRetry: () => void;
};

export function RewriteAnalysisSection({
  report,
  onCopy,
  onRetry,
}: RewriteAnalysisSectionProps) {
  return (
    <section style={sectionStyle}>
      <div>
        <p style={eyebrowStyle}>REWRITE AGENT</p>
        <h3 style={titleStyle}>改写与下一步</h3>
      </div>

      {report.sentenceRewrites.length > 0 && (
        <div style={sentenceListStyle}>
          <h4 style={subTitleStyle}>逐句改写</h4>

          {report.sentenceRewrites.map((item) => (
            <article
              key={`${item.turnIndex}-${item.sentenceIndex}`}
              style={sentenceCardStyle}
            >
              <div style={sentenceMetaStyle}>
                第 {item.turnIndex} 轮 · 句{" "}
                {item.sentenceIndex}
              </div>

              <div style={compareGridStyle}>
                <div style={compareBoxStyle}>
                  <span style={labelStyle}>原句</span>
                  <p style={paragraphStyle}>
                    {item.originalText}
                  </p>
                </div>

                <div style={compareBoxStyle}>
                  <span style={labelStyle}>改写</span>
                  <p style={paragraphStyle}>
                    {item.rewrittenText}
                  </p>
                </div>
              </div>

              <p style={reasonStyle}>
                <strong>改写原因：</strong>
                {item.rewriteReason}
              </p>
              <p style={reasonStyle}>
                <strong>预期影响：</strong>
                {item.expectedEffect}
              </p>
            </article>
          ))}
        </div>
      )}

      <div style={mainRewriteStyle}>
        <span style={labelStyle}>综合推荐表达</span>
        <p style={mainRewriteTextStyle}>
          {report.rewrite}
        </p>
      </div>

      <details style={detailsStyle}>
        <summary style={summaryStyle}>
          查看三个备选版本
        </summary>

        <Variant
          title="最小修改版"
          text={report.rewriteVariants.minimalEdit}
        />
        <Variant
          title="更温和版"
          text={report.rewriteVariants.warmerVersion}
        />
        <Variant
          title="更坚定版"
          text={report.rewriteVariants.firmerVersion}
        />
      </details>

      <div style={nextStepStyle}>
        <strong>下一步</strong>
        <p style={paragraphStyle}>
          {report.nextStep}
        </p>
      </div>

      {report.doNotSay.length > 0 && (
        <div style={avoidStyle}>
          <strong>避免表达</strong>
          <ul style={listStyle}>
            {report.doNotSay.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      <div style={buttonRowStyle}>
        <button
          type="button"
          onClick={onCopy}
          style={primaryButtonStyle}
        >
          <Copy size={17} />
          复制优化表达
        </button>

        <button
          type="button"
          onClick={onRetry}
          style={secondaryButtonStyle}
        >
          <RefreshCw size={17} />
          用这个版本重新模拟
        </button>
      </div>
    </section>
  );
}

function Variant({
  title,
  text,
}: {
  title: string;
  text: string;
}) {
  return (
    <div style={variantStyle}>
      <strong>{title}</strong>
      <p style={paragraphStyle}>{text}</p>
    </div>
  );
}

const sectionStyle: CSSProperties = {
  display: "grid",
  gap: 16,
};

const eyebrowStyle: CSSProperties = {
  margin: 0,
  fontSize: 12,
  letterSpacing: "0.14em",
  opacity: 0.58,
};

const titleStyle: CSSProperties = {
  margin: "4px 0 0",
  fontSize: 22,
};

const subTitleStyle: CSSProperties = {
  margin: 0,
};

const sentenceListStyle: CSSProperties = {
  display: "grid",
  gap: 10,
};

const sentenceCardStyle: CSSProperties = {
  padding: 14,
  borderRadius: 14,
  border: "1px solid rgba(0, 0, 0, 0.09)",
  display: "grid",
  gap: 10,
};

const sentenceMetaStyle: CSSProperties = {
  fontSize: 12,
  opacity: 0.6,
};

const compareGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns:
    "repeat(auto-fit, minmax(230px, 1fr))",
  gap: 10,
};

const compareBoxStyle: CSSProperties = {
  padding: 12,
  borderRadius: 12,
  background: "rgba(0, 0, 0, 0.035)",
};

const labelStyle: CSSProperties = {
  display: "block",
  fontSize: 12,
  fontWeight: 700,
  opacity: 0.58,
};

const paragraphStyle: CSSProperties = {
  margin: "6px 0 0",
  lineHeight: 1.7,
};

const reasonStyle: CSSProperties = {
  margin: 0,
  fontSize: 13,
  lineHeight: 1.65,
};

const mainRewriteStyle: CSSProperties = {
  padding: 16,
  borderRadius: 16,
  background: "rgba(0, 0, 0, 0.04)",
};

const mainRewriteTextStyle: CSSProperties = {
  margin: "8px 0 0",
  lineHeight: 1.85,
  whiteSpace: "pre-wrap",
};

const detailsStyle: CSSProperties = {
  padding: 14,
  borderRadius: 14,
  border: "1px solid rgba(0, 0, 0, 0.09)",
};

const summaryStyle: CSSProperties = {
  cursor: "pointer",
  fontWeight: 700,
};

const variantStyle: CSSProperties = {
  paddingTop: 12,
};

const nextStepStyle: CSSProperties = {
  padding: 14,
  borderRadius: 14,
  background: "rgba(0, 0, 0, 0.035)",
};

const avoidStyle: CSSProperties = {
  padding: 14,
  borderRadius: 14,
  border: "1px solid rgba(0, 0, 0, 0.08)",
};

const listStyle: CSSProperties = {
  margin: "8px 0 0",
  paddingLeft: 20,
  lineHeight: 1.75,
};

const buttonRowStyle: CSSProperties = {
  display: "flex",
  gap: 10,
  flexWrap: "wrap",
};

const primaryButtonStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 8,
  padding: "11px 15px",
  border: 0,
  borderRadius: 12,
  cursor: "pointer",
  background: "currentColor",
  color: "Canvas",
  fontWeight: 700,
};

const secondaryButtonStyle: CSSProperties = {
  ...primaryButtonStyle,
  background: "transparent",
  color: "inherit",
  border: "1px solid rgba(0, 0, 0, 0.16)",
};
