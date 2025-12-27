"use client";

import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { Toaster } from "@/components/ui/sonner";

import { useAuth } from "@/context/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated && !isLoading) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (!isAuthenticated || isLoading) {
    return null; // or a loading spinner while redirecting
  }
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="w-full h-screen">{children}</main>
      <Toaster position="top-center" />
    </SidebarProvider>
  );
}
