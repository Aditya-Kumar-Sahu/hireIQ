"use client";

import { createContext, useContext, useEffect, useState } from "react";

import { getMe, isApiError } from "@/lib/api";
import { clearToken, readToken } from "@/lib/auth";
import type { User } from "@/lib/types";

type SessionContextValue = {
  token: string | null;
  user: User | null;
  loading: boolean;
  refresh: () => Promise<void>;
  logout: () => void;
};

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadUser(explicitToken?: string | null) {
    const activeToken = explicitToken ?? readToken();
    setToken(activeToken);
    if (!activeToken) {
      setUser(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const nextUser = await getMe(activeToken);
      setUser(nextUser);
    } catch (error) {
      if (isApiError(error) && [401, 403].includes(error.status)) {
        clearToken();
        setToken(null);
        setUser(null);
      } else {
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadUser();
  }, []);

  return (
    <SessionContext.Provider
      value={{
        token,
        user,
        loading,
        refresh: async () => loadUser(token),
        logout: () => {
          clearToken();
          setToken(null);
          setUser(null);
          setLoading(false);
        },
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used inside SessionProvider");
  }
  return context;
}
