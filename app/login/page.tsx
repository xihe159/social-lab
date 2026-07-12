"use client";

import { ArrowLeft, KeyRound, Mail } from "lucide-react";
import { FormEvent, useState } from "react";
import { appPath } from "@/lib/app-path";
import { useAuth } from "@/components/social-lab/auth-provider";

export default function LoginPage() {
  const {
    isConfigured,
    sendEmailCode,
    signInWithPassword,
    signUpWithPassword,
    user,
    verifyEmailCode,
  } = useAuth();
  const [mode, setMode] = useState<"email" | "password">("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [codeSent, setCodeSent] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submitEmail = async (event: FormEvent) => {
    event.preventDefault();
    if (!email.trim() || isSubmitting) return;

    try {
      setIsSubmitting(true);
      setMessage("");
      if (!codeSent) {
        await sendEmailCode(email.trim());
        setCodeSent(true);
        setMessage("验证码已发送，请打开邮箱查看。");
      } else {
        await verifyEmailCode(code.trim());
        window.location.href = appPath("/profile/");
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "邮箱登录失败。");
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitPassword = async (event: FormEvent) => {
    event.preventDefault();
    if (!username.trim() || !password || isSubmitting) return;

    try {
      setIsSubmitting(true);
      setMessage("");
      await signInWithPassword(username.trim(), password);
      window.location.href = appPath("/profile/");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "用户名密码登录失败，请确认账号已注册。",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const registerWithPassword = async () => {
    if (!username.trim() || !password || isSubmitting) return;

    try {
      setIsSubmitting(true);
      setMessage("");
      await signUpWithPassword(username.trim(), password);
      window.location.href = appPath("/profile/");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "注册失败。");
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
          {mode === "email" ? <Mail size={16} /> : <KeyRound size={16} />}
          CloudBase 登录
        </div>
        <h1>先登录，保存你的沟通训练记录</h1>
        <p>
          登录后可以保存人物画像、模拟对话和复盘报告。你仍然可以先匿名体验，
          结束后再登录保存。
        </p>

        <div className="auth-tabs">
          <button
            className={mode === "email" ? "is-active" : ""}
            onClick={() => setMode("email")}
            type="button"
          >
            邮箱验证码
          </button>
          <button
            className={mode === "password" ? "is-active" : ""}
            onClick={() => setMode("password")}
            type="button"
          >
            用户名密码
          </button>
        </div>

        {user ? (
          <div className="auth-notice">
            当前已登录：{user.email || user.username || user.id}
            <a href={appPath("/profile/")}>进入个人中心</a>
          </div>
        ) : mode === "email" ? (
          <form className="auth-form" onSubmit={submitEmail}>
            <label>
              <span>邮箱</span>
              <input
                type="email"
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  setCodeSent(false);
                }}
                placeholder="you@example.com"
                disabled={!isConfigured || isSubmitting || codeSent}
                required
              />
            </label>
            {codeSent && (
              <label>
                <span>邮箱验证码</span>
                <input
                  value={code}
                  onChange={(event) => setCode(event.target.value)}
                  placeholder="请输入邮箱中的验证码"
                  disabled={!isConfigured || isSubmitting}
                  required
                />
              </label>
            )}
            <button
              className="primary-action"
              disabled={!isConfigured || isSubmitting || (codeSent && !code.trim())}
              type="submit"
            >
              {isSubmitting
                ? "正在处理..."
                : codeSent
                  ? "完成登录"
                  : "发送验证码"}
            </button>
            {codeSent && (
              <button
                className="secondary-action"
                onClick={() => {
                  setCode("");
                  setCodeSent(false);
                  setMessage("");
                }}
                type="button"
              >
                重新填写邮箱
              </button>
            )}
          </form>
        ) : (
          <form className="auth-form" onSubmit={submitPassword}>
            <label>
              <span>用户名</span>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="例如：sociallab_user"
                disabled={!isConfigured || isSubmitting}
                required
              />
            </label>
            <label>
              <span>密码</span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="请输入密码"
                disabled={!isConfigured || isSubmitting}
                required
              />
            </label>
            <button
              className="primary-action"
              disabled={!isConfigured || isSubmitting}
              type="submit"
            >
              {isSubmitting ? "正在登录..." : "登录"}
            </button>
            <button
              className="secondary-action"
              disabled={!isConfigured || isSubmitting}
              onClick={registerWithPassword}
              type="button"
            >
              注册并登录
            </button>
          </form>
        )}

        {!isConfigured && (
          <p className="auth-error">
            CloudBase 环境 ID 尚未配置，请先设置 NEXT_PUBLIC_CLOUDBASE_ENV_ID。
          </p>
        )}
        {message && <p className="auth-message">{message}</p>}
      </section>
    </main>
  );
}
