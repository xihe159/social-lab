import type { CSSProperties } from "react";

import type {
  ConversationProcessAnalysis,
  SentenceProcessAnalysis,
  StateDelta,
  ConversationDynamicsDelta,
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
  return (
    <section style={sectionStyle}>
      <div style={sectionHeaderStyle}>
        <div>
          <p style={eyebrowStyle}>ANALYSIS AGENT</p>
          <h3 style={titleStyle}>逐句对话过程分析</h3>
        </div>
        <div style={coverageStyle}>
          已分析 {analysis.coverage.analyzedUserSentences}/
          {analysis.coverage.totalUserSentences} 句
        </div>
      </div>

      <p style={summaryStyle}>
        {analysis.overallAssessment}
      </p>

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

      <div style={trajectoryStyle}>
        <strong>状态轨迹</strong>
        <p style={paragraphStyle}>
          {analysis.stateTrajectorySummary}
        </p>
      </div>

      <div style={methodStyle}>
        {analysis.methodologyNotice}
      </div>

      <div style={turnListStyle}>
        {analysis.turns.map((turn) => (
          <article
            key={turn.turnIndex}
            style={turnCardStyle}
          >
            <div style={turnHeaderStyle}>
              <div>
                <span style={turnIndexStyle}>
                  第 {turn.turnIndex} 轮
                </span>
                <span style={turnScoreStyle}>
                  本轮评价 {turn.turnEvaluationScore}
                </span>
              </div>
              <div style={deltaGroupStyle}>
                <DeltaSummary
                  title="关系"
                  delta={turn.relationshipDelta}
                  names={relationshipNames}
                />
                <DeltaSummary
                  title="动态"
                  delta={turn.dynamicsDelta}
                  names={dynamicsNames}
                />
              </div>
            </div>

            <div style={messageGridStyle}>
              <div style={messageBoxStyle}>
                <span style={messageLabelStyle}>
                  用户表达
                </span>
                <p style={paragraphStyle}>
                  {turn.userMessage}
                </p>
              </div>

              <div style={messageBoxStyle}>
                <span style={messageLabelStyle}>
                  目标人物回复
                </span>
                <p style={paragraphStyle}>
                  {turn.targetReply || "本轮没有目标人物回复。"}
                </p>
              </div>
            </div>

            <p style={turnSummaryStyle}>
              {turn.turnSummary}
            </p>
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
    </section>
  );
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
          {sentence.evaluationScore}
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
          title="关系变化归因"
          delta={sentence.relationshipDelta}
          names={relationshipNames}
        />
        <DeltaSummary
          title="动态变化归因"
          delta={sentence.dynamicsDelta}
          names={dynamicsNames}
        />
      </div>

      <p style={stateNoteStyle}>
        {sentence.stateChangeNote}
      </p>
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
      <strong style={scoreValueStyle}>{value}</strong>
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
    return (
      <span style={emptyDeltaStyle}>
        {title}：无轨迹
      </span>
    );
  }

  const entries = (
    Object.entries(delta) as Array<
      [keyof T, number]
    >
  ).filter(([, value]) => value !== 0);

  if (entries.length === 0) {
    return (
      <span style={emptyDeltaStyle}>
        {title}：稳定
      </span>
    );
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
  gap: 18,
};

const sectionHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 16,
  alignItems: "flex-start",
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

const coverageStyle: CSSProperties = {
  padding: "7px 10px",
  borderRadius: 999,
  background: "rgba(0, 0, 0, 0.06)",
  fontSize: 12,
  whiteSpace: "nowrap",
};

const summaryStyle: CSSProperties = {
  margin: 0,
  fontSize: 15,
  lineHeight: 1.75,
};

const scoreGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns:
    "repeat(auto-fit, minmax(150px, 1fr))",
  gap: 10,
};

const scoreItemStyle: CSSProperties = {
  padding: 12,
  border: "1px solid rgba(0, 0, 0, 0.08)",
  borderRadius: 14,
};

const scoreLabelStyle: CSSProperties = {
  fontSize: 12,
  opacity: 0.64,
};

const scoreValueStyle: CSSProperties = {
  display: "block",
  marginTop: 4,
  fontSize: 22,
};

const scoreTrackStyle: CSSProperties = {
  height: 5,
  marginTop: 8,
  borderRadius: 99,
  background: "rgba(0, 0, 0, 0.08)",
  overflow: "hidden",
};

const scoreFillStyle: CSSProperties = {
  height: "100%",
  borderRadius: 99,
  background: "currentColor",
};

const trajectoryStyle: CSSProperties = {
  padding: 14,
  borderRadius: 14,
  background: "rgba(0, 0, 0, 0.035)",
};

const methodStyle: CSSProperties = {
  padding: 12,
  borderRadius: 12,
  border: "1px dashed rgba(0, 0, 0, 0.16)",
  fontSize: 12,
  lineHeight: 1.65,
  opacity: 0.72,
};

const turnListStyle: CSSProperties = {
  display: "grid",
  gap: 16,
};

const turnCardStyle: CSSProperties = {
  padding: 16,
  borderRadius: 18,
  border: "1px solid rgba(0, 0, 0, 0.1)",
  display: "grid",
  gap: 14,
};

const turnHeaderStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 12,
  flexWrap: "wrap",
};

const turnIndexStyle: CSSProperties = {
  fontWeight: 700,
};

const turnScoreStyle: CSSProperties = {
  marginLeft: 10,
  fontSize: 12,
  opacity: 0.62,
};

const deltaGroupStyle: CSSProperties = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
};

const messageGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns:
    "repeat(auto-fit, minmax(240px, 1fr))",
  gap: 10,
};

const messageBoxStyle: CSSProperties = {
  padding: 12,
  borderRadius: 12,
  background: "rgba(0, 0, 0, 0.035)",
};

const messageLabelStyle: CSSProperties = {
  fontSize: 12,
  fontWeight: 700,
  opacity: 0.58,
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
  padding: 14,
  borderRadius: 14,
  background: "rgba(0, 0, 0, 0.025)",
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
  background: "rgba(0, 0, 0, 0.06)",
  fontSize: 11,
};

const quoteStyle: CSSProperties = {
  margin: 0,
  padding: "10px 12px",
  borderLeft: "3px solid currentColor",
  background: "rgba(255, 255, 255, 0.55)",
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
  fontWeight: 700,
  opacity: 0.62,
};

const sentenceDeltaStyle: CSSProperties = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
};

const deltaStyle: CSSProperties = {
  padding: "5px 8px",
  borderRadius: 8,
  background: "rgba(0, 0, 0, 0.055)",
  fontSize: 11,
};

const emptyDeltaStyle: CSSProperties = {
  ...deltaStyle,
  opacity: 0.58,
};

const stateNoteStyle: CSSProperties = {
  margin: 0,
  fontSize: 11,
  lineHeight: 1.55,
  opacity: 0.58,
};
