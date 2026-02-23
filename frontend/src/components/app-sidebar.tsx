"use client";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarHeader,
  SidebarFooter,
  SidebarMenu,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  Home,
  List,
  Settings,
  Calendar,
  LogOut,
  Clock,
  PanelLeft,
} from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";

const sidebar_items = [
  {
    label: "Dashboard",
    href: "/",
    icon: Home,
  },
  {
    label: "Tasks",
    href: "/tasks",
    icon: List,
  },
  {
    label: "Schedule",
    href: "/schedule",
    icon: Calendar,
  },
  {
    label: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export function AppSidebar() {
  const { logout } = useAuth();
  const pathname = usePathname();

  const handleLogout = async () => {
    await logout();
  };

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname.startsWith(href);
  };

  const { toggleSidebar } = useSidebar();

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 ml-0.5 shrink-0 items-center justify-center rounded-lg bg-foreground text-background">
            <Clock className="h-5 w-5" />
          </div>
          <span className="text-xl font-semibold truncate group-data-[collapsible=icon]:hidden">
            Chrono Guide
          </span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup className="px-4 py-4">
          <SidebarMenu className="space-y-1">
            {sidebar_items.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);

              return (
                <SidebarMenuItem key={item.href} className="relative">
                  {active && (
                    <div className="absolute left-[-16px] top-1/2 -translate-y-1/2 w-1 h-7 bg-foreground rounded-r-full" />
                  )}
                  <SidebarMenuButton
                    asChild
                    isActive={active}
                    className={cn("py-3 text-base", active && "font-medium")}
                  >
                    <Link href={item.href}>
                      <Icon className="!h-5 !w-5 shrink-0" />
                      <span>{item.label}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              );
            })}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="px-4 py-3">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              onClick={toggleSidebar}
              className="py-3 text-base text-muted-foreground"
            >
              <PanelLeft className="!h-5 !w-5 shrink-0" />
              <span>Collapse</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton
              onClick={handleLogout}
              className="py-3 text-base text-muted-foreground hover:text-destructive hover:bg-destructive/10"
            >
              <LogOut className="!h-5 !w-5 shrink-0" />
              <span>Logout</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
