"use client";

import { ArrowLeft, FileText, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { appPath } from "@/lib/app-path";
import {
  deleteSavedSession,
  getSavedReport,
  listSavedSessions,
  type SavedSessionRecord,
} from "@/lib/social-lab-api";

export default function HistoryPage() {
  const [records, setRecords] = useState<SavedSessionRecord[]>([]);
  const [reportPreview, setReportPreview] = useState("");
  const [message, setMessage] = useState("正在加载...");

  useEffect(() => {
    listSavedSessions()
      .then((items) => {
        setRecords(items);
        setMessage(items.length ? "" : "还没有历史模拟。");
      })
      .catch((error) =>
        setMessage(error instanceof Error ? error.message : "历史加载失败。"),
      );
  }, []);

  useEffect(() => {
    const reportId = new URLSearchParams(window.location.search).get("report");
    if (!reportId) return;

    getSavedReport(reportId)
      .then((item) => setReportPreview(JSON.stringify(item.report, null, 2)))
      .catch(() => setReportPreview("报告加载失败。"));
  }, []);

  const remove = async (id: string) => {
    await deleteSavedSession(id);
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

        {reportPreview && (
          <article className="report-preview">
            <h2>历史报告</h2>
            <pre>{reportPreview}</pre>
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
