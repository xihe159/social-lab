"use client";

import { ArrowLeft, UserRound } from "lucide-react";
import { appPath } from "@/lib/app-path";

export default function LoginPage() {
  return (
    <main className="auth-page">
      <a className="back-link" href={appPath("/")}>
        <ArrowLeft size={18} /> 返回 Social Lab
      </a>

      <section className="auth-card">
        <div className="mini-badge">
          <UserRound size={16} />
          匿名体验
        </div>
        <h1>Social Lab 已改为本机匿名记录</h1>
        <p>
          现在不需要邮箱验证码或用户名密码。系统会自动为当前浏览器生成匿名身份，
          并保存人物、模拟和报告。
        </p>
        <a className="primary-action" href={appPath("/profile/")}>
          查看本机记录
        </a>
      </section>
    </main>
  );
}
