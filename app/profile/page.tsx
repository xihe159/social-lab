"use client";

import { ArrowLeft, History, RefreshCw, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { appPath } from "@/lib/app-path";
import {
  formatAnonymousUserLabel,
  getAnonymousUserId,
  resetAnonymousUserId,
} from "@/lib/anonymous-user";

export default function ProfilePage() {
  const [anonymousUserId, setAnonymousUserId] = useState("");

  useEffect(() => {
    setAnonymousUserId(getAnonymousUserId());
  }, []);

  const resetIdentity = () => {
    const ok = window.confirm(
      "确定要重置本机身份吗？重置后，这个浏览器将使用新的记录身份，旧记录不会自动删除。",
    );
    if (!ok) return;

    setAnonymousUserId(resetAnonymousUserId());
  };

  return (
    <main className="account-page">
      <a className="back-link" href={appPath("/")}>
        <ArrowLeft size={18} /> 返回首页
      </a>

      <section className="account-card">
        <div className="account-avatar">
          <UserRound size={28} />
        </div>
        <h1>本机记录</h1>
        <p>当前本机身份：{formatAnonymousUserLabel(anonymousUserId)}</p>
        <p className="muted-copy">
          Social Lab 会用这个匿名身份保存人物、模拟记录和复盘报告。
        </p>

        <div className="account-actions">
          <a className="secondary-action" href={appPath("/history/")}>
            <History size={17} /> 历史模拟
          </a>
          <a className="secondary-action" href={appPath("/personas/")}>
            我的人物
          </a>
          <button className="dark-action" onClick={resetIdentity} type="button">
            <RefreshCw size={17} /> 重置本机身份
          </button>
        </div>
      </section>
    </main>
  );
}
