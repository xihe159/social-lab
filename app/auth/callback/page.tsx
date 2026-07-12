"use client";

import { useEffect, useState } from "react";
import { appPath } from "@/lib/app-path";
import { importGuestRun } from "@/lib/social-lab-api";
import { supabase } from "@/lib/supabase-client";

export default function AuthCallbackPage() {
  const [message, setMessage] = useState("正在完成登录...");

  useEffect(() => {
    const completeLogin = async () => {
      if (!supabase) {
        setMessage("Supabase 尚未配置，无法完成登录。");
        return;
      }

      const code = new URL(window.location.href).searchParams.get("code");
      if (!code) {
        setMessage("登录链接缺少验证码，请重新发送登录链接。");
        return;
      }

      const { data, error } = await supabase.auth.exchangeCodeForSession(code);

      if (error) {
        setMessage(error.message);
        return;
      }

      const token = data.session?.access_token;
      const guestRun = window.localStorage.getItem("social_lab_guest_run");
      if (token && guestRun) {
        try {
          await importGuestRun(JSON.parse(guestRun), { accessToken: token });
          window.localStorage.removeItem("social_lab_guest_run");
        } catch {
          // 登录不应该因为导入失败而卡住，用户仍可继续使用账号。
        }
      }

      const nextPath =
        window.localStorage.getItem("social_lab_post_login_path") || appPath("/");
      window.localStorage.removeItem("social_lab_post_login_path");
      window.location.replace(nextPath);
    };

    completeLogin();
  }, []);

  return (
    <main className="auth-page">
      <section className="auth-card">
        <h1>Social Lab</h1>
        <p>{message}</p>
      </section>
    </main>
  );
}
