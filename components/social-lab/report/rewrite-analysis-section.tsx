import { Copy, Sparkles } from "lucide-react";
import type { CSSProperties } from "react";

import type { SimulationReport } from "@/lib/social-lab-types";

type RewriteAnalysisSectionProps = {
  report: SimulationReport;
  onCopy: () => void;
};

export function RewriteAnalysisSection({
  report,
  onCopy,
}: RewriteAnalysisSectionProps) {
  const firstRewrite = report.sentenceRewrites[0];
  const rewriteFocus =
    firstRewrite?.rewriteReason ||
    report.conversationAnalysis.primaryBottleneck;
  const expectedEffect =
    firstRewrite?.expectedEffect ||
    "让对方更容易理解你的实际诉求，并提高继续讨论解决方案的意愿。";

  return (
    <section style={sectionStyle}>
      <div style={headingStyle}>
        <div style={iconStyle}>
          <Sparkles size={19} aria-hidden="true" />
        </div>
        <div>
          <p style={eyebrowStyle}>怎么改</p>
          <h3 style={titleStyle}>最推荐的表达</h3>
        </div>
      </div>

      <div style={mainRewriteStyle}>
        <p style={mainRewriteTextStyle}>{report.rewrite}</p>
      </div>

      <div style={explanationGridStyle}>
        <div style={explanationStyle}>
          <strong style={explanationLabelStyle}>
            改写重点
          </strong>
          <p style={paragraphStyle}>{rewriteFocus}</p>
        </div>
        <div style={explanationStyle}>
          <strong style={explanationLabelStyle}>
            预期变化
          </strong>
          <p style={paragraphStyle}>{expectedEffect}</p>
        </div>
      </div>

      <button
        type="button"
        onClick={onCopy}
        className="secondary-action"
        style={copyButtonStyle}
      >
        <Copy size={17} />
        复制推荐表达
      </button>

      <details style={detailsStyle}>
        <summary style={summaryStyle}>
          查看其他表达方式
        </summary>
        <div style={variantGridStyle}>
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
        </div>
      </details>

      {report.sentenceRewrites.length > 0 && (
        <details style={detailsStyle}>
          <summary style={summaryStyle}>
            查看逐句修改说明
          </summary>
          <div style={sentenceListStyle}>
            {report.sentenceRewrites.map((item) => (
              <article
                key={`${item.turnIndex}-${item.sentenceIndex}`}
                style={sentenceCardStyle}
              >
                <div style={sentenceMetaStyle}>
                  第 {item.turnIndex} 轮 · 句 {item.sentenceIndex}
                </div>
                <div style={compareGridStyle}>
                  <div style={compareBoxStyle}>
                    <span style={labelStyle}>原句</span>
                    <p style={paragraphStyle}>
                      {item.originalText}
                    </p>
                  </div>
                  <div style={compareBoxStyle}>
                    <span style={labelStyle}>建议改为</span>
                    <p style={paragraphStyle}>
                      {item.rewrittenText}
                    </p>
                  </div>
                </div>
                <p style={reasonStyle}>
                  <strong>原因：</strong>
                  {item.rewriteReason}
                </p>
              </article>
            ))}
          </div>
        </details>
      )}

      {report.doNotSay.length > 0 && (
        <details style={detailsStyle}>
          <summary style={summaryStyle}>
            查看需要避免的表达
          </summary>
          <ul style={listStyle}>
            {report.doNotSay.slice(0, 2).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </details>
      )}
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
  gap: 14,
};

const headingStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 11,
};

const iconStyle: CSSProperties = {
  display: "grid",
  placeItems: "center",
  width: 40,
  height: 40,
  borderRadius: 12,
  color: "var(--primary)",
  background: "var(--surface)",
  border: "1px solid var(--line)",
};

const eyebrowStyle: CSSProperties = {
  margin: 0,
  color: "var(--primary-muted)",
  fontSize: 12,
  fontWeight: 800,
  letterSpacing: "0.08em",
};

const titleStyle: CSSProperties = {
  margin: "3px 0 0",
  fontSize: 22,
};

const mainRewriteStyle: CSSProperties = {
  padding: 18,
  borderRadius: 12,
  background: "var(--surface)",
  border: "1px solid var(--border)",
};

const mainRewriteTextStyle: CSSProperties = {
  margin: 0,
  fontSize: 15,
  lineHeight: 1.85,
  whiteSpace: "pre-wrap",
};

const explanationGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
  gap: 10,
};

const explanationStyle: CSSProperties = {
  padding: 16,
  borderRadius: 12,
  background: "rgba(255, 255, 255, 0.64)",
};

const explanationLabelStyle: CSSProperties = {
  color: "var(--primary)",
  fontSize: 13,
};

const paragraphStyle: CSSProperties = {
  margin: "6px 0 0",
  lineHeight: 1.7,
};

const copyButtonStyle: CSSProperties = {
  justifySelf: "start",
};

const detailsStyle: CSSProperties = {
  padding: "14px 16px",
  borderRadius: 12,
  border: "1px solid var(--line)",
  background: "rgba(255, 255, 255, 0.58)",
};

const summaryStyle: CSSProperties = {
  cursor: "pointer",
  color: "var(--primary)",
  fontWeight: 800,
};

const variantGridStyle: CSSProperties = {
  display: "grid",
  gap: 10,
  paddingTop: 11,
};

const variantStyle: CSSProperties = {
  padding: 16,
  borderRadius: 12,
  background: "var(--surface)",
  border: "1px solid var(--border-soft)",
};

const sentenceListStyle: CSSProperties = {
  display: "grid",
  gap: 10,
  paddingTop: 11,
};

const sentenceCardStyle: CSSProperties = {
  padding: 16,
  borderRadius: 12,
  background: "var(--surface)",
  border: "1px solid var(--border-soft)",
  display: "grid",
  gap: 10,
};

const sentenceMetaStyle: CSSProperties = {
  color: "var(--text-secondary)",
  fontSize: 12,
};

const compareGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
  gap: 10,
};

const compareBoxStyle: CSSProperties = {
  padding: 14,
  borderRadius: 12,
  background: "var(--bg-soft)",
};

const labelStyle: CSSProperties = {
  display: "block",
  color: "var(--text-secondary)",
  fontSize: 12,
  fontWeight: 700,
};

const reasonStyle: CSSProperties = {
  margin: 0,
  fontSize: 13,
  lineHeight: 1.65,
};

const listStyle: CSSProperties = {
  margin: "9px 0 0",
  paddingLeft: 20,
  lineHeight: 1.75,
};
