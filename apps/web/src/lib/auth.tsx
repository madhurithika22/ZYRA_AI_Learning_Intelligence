"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { fetchCurrentAuthUser, logoutUser as apiLogoutUser } from "./api";
import { AuthUser } from "./types";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated" | "error";

interface AuthContextType {
  user: AuthUser | null;
  status: AuthStatus;
  error: string | null;
  checkAuth: () => Promise<AuthUser | null>;
  setAuthUser: (user: AuthUser | null) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [error, setError] = useState<string | null>(null);

  const checkAuth = useCallback(async (): Promise<AuthUser | null> => {
    setStatus("loading");
    setError(null);
    
    // Fast-fail: If no token exists, don't bother pinging the backend
    const token = typeof window !== "undefined" ? localStorage.getItem("session_token") : null;
    if (!token) {
      setUser(null);
      setStatus("unauthenticated");
      return null;
    }

    try {
      const currentUser = await fetchCurrentAuthUser();
      if (currentUser) {
        setUser(currentUser);
        setStatus("authenticated");
        return currentUser;
      } else {
        localStorage.removeItem("session_token");
        setUser(null);
        setStatus("unauthenticated");
        return null;
      }
    } catch {
      setUser(null);
      setStatus("error");
      setError("Network connection failure. Unable to verify authentication status.");
      return null;
    }
  }, []);

  const setAuthUser = useCallback((newUser: AuthUser | null) => {
    // Automatically save the token when a user logs in or registers
    if (newUser?.access_token && typeof window !== "undefined") {
      localStorage.setItem("session_token", newUser.access_token);
    }
    
    setUser(newUser);
    setStatus(newUser ? "authenticated" : "unauthenticated");
    setError(null);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogoutUser();
    } catch {
      // Ignore network errors during logout
    } finally {
      // Always clear the local storage token on logout
      if (typeof window !== "undefined") {
        localStorage.removeItem("session_token");
      }
      setUser(null);
      setStatus("unauthenticated");
      setError(null);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function initAuth() {
      // Fast-fail on initial load if no token exists
      const token = typeof window !== "undefined" ? localStorage.getItem("session_token") : null;
      if (!token) {
        if (isMounted) {
          setUser(null);
          setStatus("unauthenticated");
        }
        return;
      }

      try {
        const currentUser = await fetchCurrentAuthUser();
        if (!isMounted) return;
        if (currentUser) {
          setUser(currentUser);
          setStatus("authenticated");
        } else {
          localStorage.removeItem("session_token");
          setUser(null);
          setStatus("unauthenticated");
        }
      } catch {
        if (!isMounted) return;
        setUser(null);
        setStatus("error");
        setError("Network connection failure. Unable to verify authentication status.");
      }
    }
    initAuth();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        status,
        error,
        checkAuth,
        setAuthUser,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
