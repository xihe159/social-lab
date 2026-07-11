const ANONYMOUS_USER_KEY = "social_lab_anonymous_user_id";

function createAnonymousUserId() {
  return `sl_anon_${crypto.randomUUID()}`;
}

export function getAnonymousUserId() {
  if (typeof window === "undefined") return "";

  const existing = window.localStorage.getItem(ANONYMOUS_USER_KEY);
  if (existing?.startsWith("sl_anon_")) return existing;

  const nextId = createAnonymousUserId();
  window.localStorage.setItem(ANONYMOUS_USER_KEY, nextId);
  return nextId;
}

export function resetAnonymousUserId() {
  if (typeof window === "undefined") return "";

  const nextId = createAnonymousUserId();
  window.localStorage.setItem(ANONYMOUS_USER_KEY, nextId);
  return nextId;
}

export function formatAnonymousUserLabel(userId: string) {
  return userId ? userId.slice(-8).toUpperCase() : "本机";
}
