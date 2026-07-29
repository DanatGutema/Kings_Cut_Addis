import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, type Staff } from "../api/client";

type AuthState = {
  staff: Staff | null;
  loading: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [staff, setStaff] = useState<Staff | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Clear legacy localStorage tokens from the old Bearer auth approach.
    localStorage.removeItem("kca_access_token");
    localStorage.removeItem("kca_refresh_token");

    api
      .me()
      .then(setStaff)
      .catch(() => setStaff(null))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (identifier: string, password: string) => {
    const me = await api.login(identifier, password);
    setStaff(me);
  }, []);

  const logout = useCallback(() => {
    void api.logout().finally(() => {
      setStaff(null);
    });
  }, []);

  const value = useMemo(
    () => ({ staff, loading, login, logout }),
    [staff, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
