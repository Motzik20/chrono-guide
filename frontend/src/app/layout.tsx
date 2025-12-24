"use client";

import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/auth-context";
import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";
import { usePathname } from "next/navigation";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const isAuthPage =
    pathname.startsWith("/login") || pathname.startsWith("/signup");
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {!isAuthPage && (
            <SidebarProvider>
              <AppSidebar />
              <main className="w-full h-screen">{children}</main>
            </SidebarProvider>
          )}
          {isAuthPage && <>{children}</>}
        </AuthProvider>
      </body>
    </html>
  );
}
