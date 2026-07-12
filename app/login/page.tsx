"use client";

import { ArrowLeft, Mail } from "lucide-react";
import { FormEvent, useState } from "react";
import { appPath } from "@/lib/app-path";
import { useAuth } from "@/components/social-lab/auth-provider";

export default function LoginPage() {
  const { isConfigured, signInWithEmail, user } = useAuth();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!email.trim() || isSubmitting) return;

    try {
      setIsSubmitting(true);
      setMessage("");
      await signInWithEmail(email.trim());
      setMessage("登录链接已发送，请打开邮箱完成登录。");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "发送登录链接失败。");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="auth-page">
      <a className="back-link" href={appPath("/")}>
        <ArrowLeft size={18} /> 返回 Social Lab
      </a>

      <section className="auth-card">
        <div className="mini-badge">
          <Mail size={16} /> Email Magic Link
        </div>
        <h1>先登录，保存你的沟通训练记录</h1>
        <p>
          登录后可以保存人物画像、模拟对话和复盘报告。你仍然可以先匿名体验，
          结束后再登录保存。
        </p>

        {user ? (
          <div className="auth-notice">
            当前已登录：{user.email}
            <a href={appPath("/profile/")}>进入个人中心</a>
          </div>
        ) : (
          <form className="auth-form" onSubmit={submit}>
            <label>
              <span>邮箱</span>
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                disabled={!isConfigured || isSubmitting}
                required
              />
            </label>
            <button
              className="primary-action"
              disabled={!isConfigured || isSubmitting}
              type="submit"
            >
              {isSubmitting ? "正在发送..." : "发送登录链接"}
            </button>
          </form>
        )}

        {!isConfigured && (
          <p className="auth-error">
            Supabase 前端环境变量尚未配置，请先设置
            NEXT_PUBLIC_SUPABASE_URL 和 NEXT_PUBLIC_SUPABASE_ANON_KEY。
          </p>
        )}
        {message && <p className="auth-message">{message}</p>}
      </section>
    </main>
  );
}
