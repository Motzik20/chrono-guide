"use client";

import { useAuth } from "@/context/auth-context";
import { LoginForm } from "@/components/auth/LoginForm";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push("/");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isAuthenticated || isLoading) {
    return null; // or a loading spinner while redirecting
  }

  return <LoginForm />;
}
