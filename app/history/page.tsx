"use client";

import { ArrowLeft, FileText, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { appPath } from "@/lib/app-path";
import {
  deleteCloudBaseSession,
  getCloudBaseReport,
  listCloudBaseSessions,
} from "@/lib/cloudbase-data";
import {
  type SavedSessionRecord,
} from "@/lib/social-lab-api";
import { useAuth } from "@/components/social-lab/auth-provider";

export default function HistoryPage() {
  const { user } = useAuth();
  const [records, setRecords] = useState<SavedSessionRecord[]>([]);
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [message, setMessage] = useState("正在加载...");

  useEffect(() => {
    if (!user) {
      setMessage("登录后可以查看历史模拟。");
      return;
    }

    listCloudBaseSessions(user)
      .then((items) => {
        setRecords(items);
        setMessage(items.length ? "" : "还没有历史模拟。");
      })
      .catch((error) =>
        setMessage(error instanceof Error ? error.message : "历史加载失败。"),
      );
  }, [user]);

  useEffect(() => {
    if (!user) return;
    const reportId = new URLSearchParams(window.location.search).get("report");
    if (!reportId) return;

    getCloudBaseReport(reportId)
      .then((item) => setReport(item.report))
      .catch(() => setReport({ error: "报告加载失败。" }));
  }, [user]);

  const remove = async (id: string) => {
    if (!user) return;
    await deleteCloudBaseSession(id);
    setRecords((current) => current.filter((item) => item.id !== id));
  };

  return (
    <main className="account-page">
      <a className="back-link" href={appPath("/")}>
        <ArrowLeft size={18} /> 返回首页
      </a>

      <section className="account-card wide">
        <h1>历史模拟</h1>
        <p>回顾之前的沟通训练记录和报告。</p>

        {message && <p className="auth-message">{message}</p>}

        {report && (
          <article className="report-preview">
            <h2>历史报告</h2>
            <pre>{JSON.stringify(report, null, 2)}</pre>
          </article>
        )}

        <div className="record-list">
          {records.map((record) => (
            <article className="record-card" key={record.id}>
              <div>
                <span className="record-kicker">{record.scenario}</span>
                <h2>{record.persona_title || record.goal || "未命名模拟"}</h2>
                <p>{new Date(record.created_at).toLocaleDateString("zh-CN")}</p>
              </div>
              <div className="record-actions">
                {record.latest_report_id && (
                  <a
                    className="secondary-action"
                    href={appPath(`/history/?report=${record.latest_report_id}`)}
                  >
                    <FileText size={16} /> 报告
                  </a>
                )}
                <button
                  className="secondary-action"
                  onClick={() => remove(record.id)}
                  type="button"
                  aria-label="删除历史"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
