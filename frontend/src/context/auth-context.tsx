"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { isTokenExpired } from "@/lib/utils";

interface AuthContextType {
   token: string | null;
   login: (token: string) => void;
   logout: () => void;
   isLoading: boolean;
   isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        const token = localStorage.getItem("chrono_token");
        if (token) {
            if (isTokenExpired(token)) {
                logout();
                return;
            }
            setToken(token);
        }
        setIsLoading(false);
    }, []);

    const login = (token: string) => {
        localStorage.setItem("chrono_token", token);
        setToken(token);
        router.push("/");
    }

    const logout = () => {
        localStorage.removeItem("chrono_token");
        setToken(null);
        router.push("/login");
    }

    return (
        <AuthContext.Provider value={{ token, login, logout, isLoading, isAuthenticated: !!token }}>
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