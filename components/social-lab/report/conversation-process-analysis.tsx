import type { CSSProperties } from "react";

import type {
  ConversationDynamicsDelta,
  ConversationProcessAnalysis,
  SentenceProcessAnalysis,
  StateDelta,
} from "@/lib/social-lab-types";

type ConversationProcessAnalysisProps = {
  analysis: ConversationProcessAnalysis;
};

const evaluationLabelText = {
  strong: "明显有效",
  effective: "总体有效",
  neutral: "作用有限",
  risky: "存在风险",
  damaging: "明显受损",
} as const;

const goalEffectText = {
  supports: "推动目标",
  neutral: "影响有限",
  obstructs: "阻碍目标",
} as const;

const functionText = {
  context: "补充背景",
  request: "提出请求",
  question: "提出问题",
  explanation: "解释说明",
  apology: "道歉承担",
  commitment: "作出承诺",
  boundary: "表达边界",
  emotion: "表达感受",
  pressure: "施压要求",
  response: "回应对方",
  other: "其他表达",
} as const;

const feelingText = {
  reassured: "更安心",
  respected: "被尊重",
  understood: "被理解",
  neutral: "中性",
  uncertain: "不确定",
  burdened: "感到负担",
  pressured: "感到压力",
  defensive: "产生防御",
  hurt: "感到受伤",
  withdrawn: "倾向退出",
} as const;

const relationshipNames: Record<keyof StateDelta, string> = {
  trust: "信任",
  respect: "尊重",
  familiarity: "熟悉度",
  affinity: "亲近度",
  authority: "权力距离",
  emotional: "情绪稳定",
};

const dynamicsNames: Record<
  keyof ConversationDynamicsDelta,
  string
> = {
  atmosphere_score: "氛围",
  pace_score: "节奏健康",
  pressure_level: "压力",
  clarity_score: "清晰度",
  responsiveness_score: "回应度",
  progress_score: "推进度",
  repairability_score: "可修复性",
  boundary_score: "边界健康",
};

export function ConversationProcessAnalysisSection({
  analysis,
}: ConversationProcessAnalysisProps) {
  const criticalSentence = getCriticalSentence(analysis);

  return (
    <section style={sectionStyle}>
      <div style={sectionHeaderStyle}>
        <div>
          <p style={eyebrowStyle}>表达分析</p>
          <h3 style={titleStyle}>对话过程分析</h3>
        </div>
        <div style={coverageStyle}>
          已分析 {analysis.coverage.analyzedUserSentences}/
          {analysis.coverage.totalUserSentences} 句
        </div>
      </div>

      <p style={summaryStyle}>{analysis.overallAssessment}</p>

      {criticalSentence && (
        <div style={criticalStyle}>
          <div style={criticalHeaderStyle}>
            <div>
              <span style={criticalEyebrowStyle}>
                最需要注意的一句
              </span>
              <span style={turnMetaStyle}>
                第 {criticalSentence.turnIndex} 轮
              </span>
            </div>
            <span style={riskBadgeStyle}>
              {evaluationLabelText[
                criticalSentence.evaluationLabel
              ]}
            </span>
          </div>
          <blockquote style={criticalQuoteStyle}>
            “{criticalSentence.sentenceText}”
          </blockquote>
          <p style={criticalReasonStyle}>
            <strong>为什么需要调整：</strong>
            {criticalSentence.evaluationReason}
          </p>
          <p style={criticalInterpretationStyle}>
            对方可能理解为：
            {criticalSentence.targetLikelyInterpretation}
          </p>
        </div>
      )}

      <details style={detailsStyle}>
        <summary style={summaryCursorStyle}>
          查看完整六维评分
        </summary>
        <div style={scoreGridStyle}>
          <ScoreItem
            label="表达清晰度"
            value={analysis.evaluationScores.clarity}
          />
          <ScoreItem
            label="回应对方"
            value={analysis.evaluationScores.responsiveness}
          />
          <ScoreItem
            label="尊重与边界"
            value={
              analysis.evaluationScores.respectAndBoundary
            }
          />
          <ScoreItem
            label="责任承担"
            value={analysis.evaluationScores.responsibility}
          />
          <ScoreItem
            label="情绪安全"
            value={analysis.evaluationScores.emotionalSafety}
          />
          <ScoreItem
            label="目标一致性"
            value={analysis.evaluationScores.goalAlignment}
          />
        </div>
      </details>

      <details style={detailsStyle}>
        <summary style={summaryCursorStyle}>
          查看全部逐轮分析
        </summary>
        <div style={turnListStyle}>
          {analysis.turns.map((turn) => (
            <article key={turn.turnIndex} style={turnCardStyle}>
              <div style={turnHeaderStyle}>
                <div>
                  <span style={turnIndexStyle}>
                    第 {turn.turnIndex} 轮
                  </span>
                  <span style={turnScoreStyle}>
                    本轮评价 {turn.turnEvaluationScore}/100
                  </span>
                </div>
                <div style={deltaGroupStyle}>
                  <DeltaSummary
                    title="关系变化"
                    delta={turn.relationshipDelta}
                    names={relationshipNames}
                  />
                  <DeltaSummary
                    title="沟通变化"
                    delta={turn.dynamicsDelta}
                    names={dynamicsNames}
                  />
                </div>
              </div>

              <div style={messageGridStyle}>
                <div style={messageBoxStyle}>
                  <span style={messageLabelStyle}>
                    你的表达
                  </span>
                  <p style={paragraphStyle}>{turn.userMessage}</p>
                </div>
                <div style={messageBoxStyle}>
                  <span style={messageLabelStyle}>
                    对方回复
                  </span>
                  <p style={paragraphStyle}>
                    {turn.targetReply || "本轮没有对方回复。"}
                  </p>
                </div>
              </div>

              <p style={turnSummaryStyle}>{turn.turnSummary}</p>
              <p style={targetInterpretationStyle}>
                <strong>回复含义：</strong>
                {turn.targetReplyInterpretation}
              </p>

              <div style={sentenceListStyle}>
                {turn.sentences.map((sentence) => (
                  <SentenceAnalysisCard
                    key={`${sentence.turnIndex}-${sentence.sentenceIndex}`}
                    sentence={sentence}
                  />
                ))}
              </div>
            </article>
          ))}
        </div>
      </details>
    </section>
  );
}

function getCriticalSentence(
  analysis: ConversationProcessAnalysis,
) {
  const sentences = analysis.turns.flatMap(
    (turn) => turn.sentences,
  );
  if (sentences.length === 0) return null;

  return [...sentences].sort((a, b) => {
    const aRisk =
      a.evaluationLabel === "damaging"
        ? 2
        : a.evaluationLabel === "risky"
          ? 1
          : 0;
    const bRisk =
      b.evaluationLabel === "damaging"
        ? 2
        : b.evaluationLabel === "risky"
          ? 1
          : 0;
    return bRisk - aRisk || a.evaluationScore - b.evaluationScore;
  })[0];
}

function SentenceAnalysisCard({
  sentence,
}: {
  sentence: SentenceProcessAnalysis;
}) {
  return (
    <div style={sentenceCardStyle}>
      <div style={sentenceHeaderStyle}>
        <span style={sentenceIndexStyle}>
          句 {sentence.sentenceIndex}
        </span>
        <span style={tagStyle}>
          {functionText[sentence.communicativeFunction]}
        </span>
        <span style={tagStyle}>
          {evaluationLabelText[sentence.evaluationLabel]}
          {" · "}
          {sentence.evaluationScore}/100
        </span>
        <span style={tagStyle}>
          {goalEffectText[sentence.goalEffect]}
        </span>
      </div>

      <blockquote style={quoteStyle}>
        {sentence.sentenceText}
      </blockquote>

      <div style={analysisGridStyle}>
        <AnalysisRow
          label="表达意图"
          value={sentence.intentSummary}
        />
        <AnalysisRow
          label="对方可能理解"
          value={sentence.targetLikelyInterpretation}
        />
        <AnalysisRow
          label="对方可能感受"
          value={feelingText[sentence.targetLikelyFeeling]}
        />
        <AnalysisRow
          label="评价"
          value={sentence.evaluationReason}
        />
      </div>

      <div style={sentenceDeltaStyle}>
        <DeltaSummary
          title="关系变化"
          delta={sentence.relationshipDelta}
          names={relationshipNames}
        />
        <DeltaSummary
          title="沟通变化"
          delta={sentence.dynamicsDelta}
          names={dynamicsNames}
        />
      </div>
    </div>
  );
}

function ScoreItem({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div style={scoreItemStyle}>
      <span style={scoreLabelStyle}>{label}</span>
      <strong style={scoreValueStyle}>{value}/100</strong>
      <div style={scoreTrackStyle}>
        <div
          style={{
            ...scoreFillStyle,
            width: `${Math.max(0, Math.min(100, value))}%`,
          }}
        />
      </div>
    </div>
  );
}

function AnalysisRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div style={analysisRowStyle}>
      <span style={analysisLabelStyle}>{label}</span>
      <span>{value}</span>
    </div>
  );
}

function DeltaSummary<T extends object>({
  title,
  delta,
  names,
}: {
  title: string;
  delta: T | null;
  names: Record<keyof T, string>;
}) {
  if (!delta) {
    return <span style={emptyDeltaStyle}>{title}：无轨迹</span>;
  }

  const entries = (
    Object.entries(delta) as Array<[keyof T, number]>
  ).filter(([, value]) => value !== 0);

  if (entries.length === 0) {
    return <span style={emptyDeltaStyle}>{title}：稳定</span>;
  }

  return (
    <span style={deltaStyle}>
      {title}：
      {entries.map(([key, value], index) => (
        <span key={String(key)}>
          {index > 0 ? "，" : ""}
          {names[key]}
          {value > 0 ? "+" : ""}
          {value}
        </span>
      ))}
    </span>
  );
}

const sectionStyle: CSSProperties = {
  display: "grid",
  gap: 14,
};

const sectionHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 16,
  alignItems: "flex-start",
};

const eyebrowStyle: CSSProperties = {
  margin: 0,
  color: "var(--primary-muted)",
  fontSize: 12,
  fontWeight: 800,
  letterSpacing: "0.08em",
};

const titleStyle: CSSProperties = {
  margin: "4px 0 0",
  fontSize: 20,
};

const coverageStyle: CSSProperties = {
  padding: "6px 9px",
  borderRadius: 999,
  background: "var(--primary-soft)",
  color: "var(--primary)",
  fontSize: 12,
  whiteSpace: "nowrap",
};

const summaryStyle: CSSProperties = {
  margin: 0,
  fontSize: 14,
  lineHeight: 1.7,
};

const criticalStyle: CSSProperties = {
  display: "grid",
  gap: 10,
  padding: 16,
  borderRadius: 12,
  background: "var(--amber)",
  border: "1px solid #f0dfb8",
};

const criticalHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 10,
  alignItems: "center",
};

const criticalEyebrowStyle: CSSProperties = {
  fontSize: 13,
  fontWeight: 800,
};

const turnMetaStyle: CSSProperties = {
  marginLeft: 8,
  color: "var(--text-secondary)",
  fontSize: 11,
};

const riskBadgeStyle: CSSProperties = {
  padding: "4px 8px",
  borderRadius: 999,
  background: "var(--surface)",
  color: "var(--text-main)",
  fontSize: 11,
  fontWeight: 800,
};

const criticalQuoteStyle: CSSProperties = {
  margin: 0,
  paddingLeft: 11,
  borderLeft: "3px solid var(--primary-muted)",
  fontSize: 15,
  lineHeight: 1.7,
};

const criticalReasonStyle: CSSProperties = {
  margin: 0,
  fontSize: 13,
  lineHeight: 1.65,
};

const criticalInterpretationStyle: CSSProperties = {
  margin: 0,
  color: "var(--text-secondary)",
  fontSize: 12,
  lineHeight: 1.6,
};

const detailsStyle: CSSProperties = {
  padding: "14px 16px",
  borderRadius: 12,
  border: "1px solid var(--border)",
};

const summaryCursorStyle: CSSProperties = {
  cursor: "pointer",
  color: "var(--primary)",
  fontWeight: 800,
};

const scoreGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
  gap: 10,
  paddingTop: 12,
};

const scoreItemStyle: CSSProperties = {
  padding: 14,
  border: "1px solid var(--border-soft)",
  borderRadius: 12,
  background: "var(--surface)",
};

const scoreLabelStyle: CSSProperties = {
  color: "var(--text-secondary)",
  fontSize: 12,
};

const scoreValueStyle: CSSProperties = {
  display: "block",
  marginTop: 4,
  fontSize: 17,
};

const scoreTrackStyle: CSSProperties = {
  height: 5,
  marginTop: 8,
  borderRadius: 99,
  background: "var(--line)",
  overflow: "hidden",
};

const scoreFillStyle: CSSProperties = {
  height: "100%",
  borderRadius: 99,
  background: "var(--primary)",
};

const turnListStyle: CSSProperties = {
  display: "grid",
  gap: 14,
  paddingTop: 12,
};

const turnCardStyle: CSSProperties = {
  padding: 18,
  borderRadius: 12,
  border: "1px solid var(--border)",
  display: "grid",
  gap: 13,
};

const turnHeaderStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 12,
  flexWrap: "wrap",
};

const turnIndexStyle: CSSProperties = {
  fontWeight: 800,
};

const turnScoreStyle: CSSProperties = {
  marginLeft: 10,
  color: "var(--text-secondary)",
  fontSize: 12,
};

const deltaGroupStyle: CSSProperties = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
};

const messageGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
  gap: 10,
};

const messageBoxStyle: CSSProperties = {
  padding: 14,
  borderRadius: 12,
  background: "var(--bg-soft)",
};

const messageLabelStyle: CSSProperties = {
  color: "var(--text-secondary)",
  fontSize: 12,
  fontWeight: 700,
};

const paragraphStyle: CSSProperties = {
  margin: "6px 0 0",
  lineHeight: 1.7,
};

const turnSummaryStyle: CSSProperties = {
  margin: 0,
  lineHeight: 1.7,
};

const targetInterpretationStyle: CSSProperties = {
  margin: 0,
  lineHeight: 1.7,
};

const sentenceListStyle: CSSProperties = {
  display: "grid",
  gap: 10,
};

const sentenceCardStyle: CSSProperties = {
  padding: 16,
  borderRadius: 12,
  background: "var(--bg-soft)",
  display: "grid",
  gap: 11,
};

const sentenceHeaderStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 7,
  flexWrap: "wrap",
};

const sentenceIndexStyle: CSSProperties = {
  fontWeight: 700,
  fontSize: 12,
};

const tagStyle: CSSProperties = {
  padding: "4px 8px",
  borderRadius: 999,
  background: "var(--primary-soft)",
  fontSize: 11,
};

const quoteStyle: CSSProperties = {
  margin: 0,
  padding: "10px 12px",
  borderLeft: "3px solid var(--primary-muted)",
  background: "var(--surface)",
  lineHeight: 1.7,
};

const analysisGridStyle: CSSProperties = {
  display: "grid",
  gap: 7,
};

const analysisRowStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "110px minmax(0, 1fr)",
  gap: 10,
  fontSize: 13,
  lineHeight: 1.6,
};

const analysisLabelStyle: CSSProperties = {
  color: "var(--text-secondary)",
  fontWeight: 700,
};

const sentenceDeltaStyle: CSSProperties = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
};

const deltaStyle: CSSProperties = {
  padding: "5px 8px",
  borderRadius: 12,
  background: "var(--primary-soft)",
  fontSize: 11,
};

const emptyDeltaStyle: CSSProperties = {
  ...deltaStyle,
  color: "var(--text-secondary)",
};
