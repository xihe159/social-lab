"use client";

import { ArrowLeft, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { appPath } from "@/lib/app-path";
import {
  deleteCloudBasePersona,
  listCloudBasePersonas,
} from "@/lib/cloudbase-data";
import {
  type SavedPersonaRecord,
} from "@/lib/social-lab-api";
import { useAuth } from "@/components/social-lab/auth-provider";

export default function PersonasPage() {
  const { user } = useAuth();
  const [records, setRecords] = useState<SavedPersonaRecord[]>([]);
  const [message, setMessage] = useState("正在加载...");

  useEffect(() => {
    if (!user) {
      setMessage("登录后可以查看保存的人物。");
      return;
    }

    listCloudBasePersonas(user)
      .then((items) => {
        setRecords(items);
        setMessage(items.length ? "" : "还没有保存的人物。");
      })
      .catch((error) =>
        setMessage(error instanceof Error ? error.message : "人物加载失败。"),
      );
  }, [user]);

  const remove = async (id: string) => {
    if (!user) return;
    await deleteCloudBasePersona(id);
    setRecords((current) => current.filter((item) => item.id !== id));
  };

  return (
    <main className="account-page">
      <a className="back-link" href={appPath("/")}>
        <ArrowLeft size={18} /> 返回首页
      </a>

      <section className="account-card wide">
        <h1>我的人物</h1>
        <p>查看已经保存的沟通对象画像。</p>

        {message && <p className="auth-message">{message}</p>}

        <div className="record-list">
          {records.map((record) => (
            <article className="record-card" key={record.id}>
              <div>
                <span className="record-kicker">{record.scenario}</span>
                <h2>{record.persona.title}</h2>
                <p>{record.role || record.goal}</p>
              </div>
              <button
                className="secondary-action"
                onClick={() => remove(record.id)}
                type="button"
                aria-label="删除人物"
              >
                <Trash2 size={16} />
              </button>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
