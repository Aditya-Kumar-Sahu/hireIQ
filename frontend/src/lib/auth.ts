export const TOKEN_STORAGE_KEY = "hireiq_token";
export const TOKEN_COOKIE_NAME = "hireiq_token";

export function readToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function persistToken(token: string) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  document.cookie = `${TOKEN_COOKIE_NAME}=${encodeURIComponent(token)}; path=/; max-age=${60 * 60 * 24 * 30}; SameSite=Lax`;
}

export function clearToken() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  document.cookie = `${TOKEN_COOKIE_NAME}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`;
}
