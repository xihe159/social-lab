import { Copy, RefreshCw } from "lucide-react";
import type { CSSProperties } from "react";
import type { SimulationReport } from "@/lib/social-lab-types";

type ReportScreenProps = {
  report: SimulationReport;
  onCopy: () => void;
  onRetry: () => void;
  isSignedIn: boolean;
  onLoginToSave: () => void;
};

export function ReportScreen({
  report,
  onCopy,
  onRetry,
  isSignedIn,
  onLoginToSave,
}: ReportScreenProps) {
  return (
    <section className="screen report-screen is-current">
      <div className="screen-heading">
        <h2>本轮复盘报告</h2>
      </div>

      <div className="report-grid">
        <article className="score-card">
          <span>本轮沟通成功率</span>
          <strong>{report.score}%</strong>
          <p>{report.reason}</p>
        </article>

        <article className="card-block">
          <div className="card-header">
            <span>可能结果</span>
            <small>模拟分布</small>
          </div>
          <div className="outcome-list">
            {report.outcomes.map((outcome) => (
              <div className="outcome-row" key={outcome.label}>
                <span>{outcome.label}</span>
                <div className="outcome-bar">
                  <span
                    style={
                      {
                        "--value": `${outcome.value}%`,
                        "--color": outcome.color,
                      } as CSSProperties
                    }
                  />
                </div>
                <b>{outcome.value}%</b>
              </div>
            ))}
          </div>
        </article>

        <article className="card-block yellow-note">
          <h3>主要影响因素</h3>
          <ul>
            {report.factors.map((factor) => (
              <li key={factor}>{factor}</li>
            ))}
          </ul>
        </article>

        <article className="card-block rewrite-card">
          <h3>推荐改写</h3>
          <p>{report.rewrite}</p>
          <button className="secondary-action" onClick={onCopy} type="button">
            <Copy size={17} /> 复制优化表达
          </button>
        </article>
      </div>

      {!isSignedIn && (
        <div className="save-prompt">
          <div>
            <b>登录后保存本次记录</b>
            <p>保存人物、聊天和报告，下次可以继续查看。</p>
          </div>
          <button className="secondary-action" onClick={onLoginToSave} type="button">
            去登录
          </button>
        </div>
      )}

      <div className="footer-actions">
        <button className="primary-action" onClick={onRetry} type="button">
          用这个版本重新模拟 <RefreshCw size={18} />
        </button>
      </div>
    </section>
  );
}
