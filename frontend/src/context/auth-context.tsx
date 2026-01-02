"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { useRouter } from "next/navigation";
import { apiRequest, ApiError } from "@/lib/chrono-client";
import { z } from "zod";
import { toast } from "sonner";

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Check auth status on mount by making a lightweight API call
  const checkAuth = useCallback(async () => {
    try {
      setIsLoading(true);
      // Call any protected endpoint to verify cookie is valid
      await apiRequest("/users/me", z.object({ id: z.number() }));
      setIsAuthenticated(true);
    } catch {
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial auth check
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = useCallback(
    async (email: string, password: string): Promise<boolean> => {
      try {
        // Backend sets the cookie on successful login
        await apiRequest("/users/login", undefined, {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });

        setIsAuthenticated(true);
        toast.success("Login successful!");
        router.push("/");
        return true;
      } catch (error) {
        const message =
          error instanceof ApiError
            ? error.message
            : "Login failed. Please try again.";
        toast.error(message);
        return false;
      }
    },
    [router]
  );

  const logout = useCallback(async () => {
    try {
      // Backend clears the cookie
      await apiRequest("/users/logout", undefined, {
        method: "POST",
      });
    } catch {
      // Ignore errors - we're logging out anyway
    } finally {
      setIsAuthenticated(false);
      router.push("/login");
    }
  }, [router]);

  // Handle 401 unauthorized events from API client
  useEffect(() => {
    const handleUnauthorized = () => {
      setIsAuthenticated(false);
      logout();
      toast.error("Session expired. Please login again.");
    };

    window.addEventListener("auth:unauthorized", handleUnauthorized);
    return () => {
      window.removeEventListener("auth:unauthorized", handleUnauthorized);
    };
  }, [router]);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
