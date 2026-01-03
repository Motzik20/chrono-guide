"use client";

import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { JobProvider } from "@/context/job-context";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <JobProvider>
      <SidebarProvider>
        <AppSidebar />
        <main className="w-full h-screen">{children}</main>
      </SidebarProvider>
    </JobProvider>
  );
}
