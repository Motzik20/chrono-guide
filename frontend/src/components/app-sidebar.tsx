"use client";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarTrigger,
  SidebarGroupContent,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarHeader,
  SidebarFooter,
  useSidebar,
} from "@/components/ui/sidebar";
import { Home, List, Settings, Calendar, LogOut } from "lucide-react";

const sidebar_items = [
  {
    label: "Dashboard",
    href: "/",
    icon: <Home />,
  },
  {
    label: "Tasks",
    href: "/tasks",
    icon: <List />,
  },
  {
    label: "Calendar",
    href: "/calendar",
    icon: <Calendar />,
  },
  {
    label: "Settings",
    href: "/settings",
    icon: <Settings />,
  },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";
  return (
    <Sidebar collapsible="icon">
      <SidebarContent>
        <SidebarHeader className="border-b border-sidebar-border pb-4">
          <div className="flex items-center">
            <SidebarTrigger />
            {!isCollapsed && (
              <div className="flex flex-col">
                Chrono Guide
                <span className="text-xs text-muted-foreground">
                  Task Scheduler
                </span>
              </div>
            )}
          </div>
        </SidebarHeader>
        <SidebarGroup>
          <SidebarGroupContent>
            {sidebar_items.map((item) => (
              <SidebarMenuItem key={item.href}>
                <SidebarMenuButton asChild>
                  <a href={item.href}>
                    {item.icon}
                    {item.label}
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenuButton asChild>
          <a href="/logout">
            <LogOut />
            Logout
          </a>
        </SidebarMenuButton>
      </SidebarFooter>
    </Sidebar>
  );
}
