"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  getCloudBaseAuth,
  isCloudBaseConfigured,
} from "@/lib/cloudbase-client";

export type CloudBaseUser = {
  id: string;
  email?: string;
  username?: string;
};

type AuthContextValue = {
  user: CloudBaseUser | null;
  isLoading: boolean;
  isConfigured: boolean;
  sendEmailCode: (email: string) => Promise<void>;
  verifyEmailCode: (code: string) => Promise<void>;
  signInWithPassword: (username: string, password: string) => Promise<void>;
  signUpWithPassword: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CloudBaseUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [emailVerifier, setEmailVerifier] = useState<{
    verifyOtp: (params: { token: string }) => Promise<unknown>;
  } | null>(null);

  const syncUser = useCallback(async () => {
    const auth = await getCloudBaseAuth();
    if (!auth) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const result = await auth.getUser();
      const data = normalizeResponse(result);
      const nextUser = data?.user || data;
      setUser(normalizeUser(nextUser));
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    syncUser();

    let unsubscribe: (() => void) | undefined;
    getCloudBaseAuth().then((auth) => {
      if (!auth?.onAuthStateChange) return;
      const subscription = auth.onAuthStateChange(() => {
        syncUser();
      });
      unsubscribe = () => subscription.data.subscription.unsubscribe();
    });

    return () => unsubscribe?.();
  }, [syncUser]);

  const sendEmailCode = useCallback(async (email: string) => {
    const auth = await getCloudBaseAuth();
    if (!auth) {
      throw new Error("CloudBase 尚未配置，暂时无法登录。");
    }

    const response = await auth.signInWithOtp({ email });
    const data = normalizeResponse(response);
    const verifier = data?.verifyOtp ? data : data?.data;

    if (!verifier?.verifyOtp) {
      throw new Error("验证码发送成功，但登录校验器初始化失败。");
    }

    setEmailVerifier(verifier);
  }, []);

  const verifyEmailCode = useCallback(
    async (code: string) => {
      if (!emailVerifier) {
        throw new Error("请先发送邮箱验证码。");
      }

      await emailVerifier.verifyOtp({ token: code });
      setEmailVerifier(null);
      await syncUser();
    },
    [emailVerifier, syncUser],
  );

  const signInWithPassword = useCallback(
    async (username: string, password: string) => {
      const auth = await getCloudBaseAuth();
      if (!auth) {
        throw new Error("CloudBase 尚未配置，暂时无法登录。");
      }

      await auth.signInWithPassword({ username, password });
      await syncUser();
    },
    [syncUser],
  );

  const signUpWithPassword = useCallback(
    async (username: string, password: string) => {
      const auth = await getCloudBaseAuth();
      if (!auth) {
        throw new Error("CloudBase 尚未配置，暂时无法注册。");
      }

      await auth.signUp({ username, password });
      await auth.signInWithPassword({ username, password });
      await syncUser();
    },
    [syncUser],
  );

  const signOut = useCallback(async () => {
    const auth = await getCloudBaseAuth();
    if (!auth) return;
    await auth.signOut();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isConfigured: isCloudBaseConfigured,
      sendEmailCode,
      verifyEmailCode,
      signInWithPassword,
      signUpWithPassword,
      signOut,
    }),
    [
      isLoading,
      sendEmailCode,
      signInWithPassword,
      signOut,
      signUpWithPassword,
      user,
      verifyEmailCode,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function normalizeResponse(value: unknown) {
  const payload = value as {
    data?: unknown;
    error?: { message?: string };
    message?: string;
  };

  if (payload?.error) {
    throw new Error(payload.error.message || "CloudBase 登录失败。");
  }

  return (payload?.data ?? value) as Record<string, any> | null;
}

function normalizeUser(value: any): CloudBaseUser | null {
  if (!value) return null;

  const id =
    value.uid ||
    value.id ||
    value.uuid ||
    value.user_id ||
    value.customUserId ||
    value.username ||
    value.email;

  if (!id) return null;

  return {
    id,
    email: value.email,
    username: value.username || value.name || value.displayName,
  };
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return value;
}
