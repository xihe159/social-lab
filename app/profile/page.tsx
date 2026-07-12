"use client";

import { ArrowLeft, History, LogOut, UserRound } from "lucide-react";
import { useState } from "react";
import { appPath } from "@/lib/app-path";
import { useAuth } from "@/components/social-lab/auth-provider";

export default function ProfilePage() {
  const { user, signOut, isConfigured, isLoading } = useAuth();
  const [message, setMessage] = useState("");

  const logout = async () => {
    try {
      await signOut();
      window.location.href = appPath("/");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "退出登录失败。");
    }
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
        <h1>个人中心</h1>
        {isLoading ? (
          <p>正在确认登录状态...</p>
        ) : user ? (
          <>
            <p>当前账号：{user.email || user.username || user.id}</p>
            <div className="account-actions">
              <a className="secondary-action" href={appPath("/history/")}>
                <History size={17} /> 历史模拟
              </a>
              <a className="secondary-action" href={appPath("/personas/")}>
                我的人物
              </a>
              <button className="dark-action" onClick={logout} type="button">
                <LogOut size={17} /> 退出登录
              </button>
            </div>
          </>
        ) : (
          <>
            <p>登录后可以保存人物、模拟记录和复盘报告。</p>
            <a className="primary-action" href={appPath("/login/")}>
              去登录
            </a>
          </>
        )}
        {!isConfigured && (
          <p className="auth-error">CloudBase 环境 ID 尚未配置，线上登录会暂不可用。</p>
        )}
        {message && <p className="auth-error">{message}</p>}
      </section>
    </main>
  );
}
