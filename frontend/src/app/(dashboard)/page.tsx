"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Calendar,
  CheckCircle2,
  Clock,
  FileText,
  Settings,
  Sparkles,
  Target,
  Zap,
} from "lucide-react";

export default function Home() {
  return (
    <main className="flex flex-col h-full w-full overflow-y-auto bg-linear-to-b from-background to-muted/20">
      <div className="flex-1 flex items-center justify-center p-6 md:p-8 lg:p-12">
        <div className="max-w-6xl mx-auto w-full space-y-12">
          {/* Hero Section */}
          <div className="text-center space-y-4">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-4">
              <Zap className="h-4 w-4" />
              <span>AI-Powered Task Management</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-bold tracking-tight bg-linear-to-br from-foreground to-foreground/70 bg-clip-text text-transparent">
              Welcome to Chrono Guide
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Transform your content into actionable tasks with intelligent
              scheduling and time management
            </p>
          </div>

          {/* Quick Actions */}
          <div className="grid gap-6 md:grid-cols-3">
            <Card className="group hover:shadow-xl hover:scale-[1.02] transition-all duration-300 border-2 hover:border-primary/50 cursor-pointer overflow-hidden bg-linear-to-br from-background to-background hover:from-primary/5 hover:to-primary/0">
              <Link href="/tasks" className="block h-full">
                <div className="relative h-full flex flex-col">
                  <CardHeader className="relative">
                    <div className="flex items-start gap-4">
                      <div className="p-3 rounded-xl bg-primary/10 group-hover:bg-primary/20 transition-colors">
                        <FileText className="h-6 w-6 text-primary" />
                      </div>
                      <div className="flex-1 space-y-1">
                        <CardTitle className="text-xl">Create Tasks</CardTitle>
                        <CardDescription className="text-base">
                          Upload files or enter text to extract tasks
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="relative flex-1 flex flex-col justify-end">
                    <Button
                      variant="ghost"
                      className="w-full group-hover:bg-primary group-hover:text-primary-foreground transition-colors justify-between"
                    >
                      <span>Get Started</span>
                      <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </CardContent>
                </div>
              </Link>
            </Card>

            <Card className="group hover:shadow-xl hover:scale-[1.02] transition-all duration-300 border-2 hover:border-blue-500/50 cursor-pointer overflow-hidden bg-linear-to-br from-background to-background hover:from-blue-500/5 hover:to-blue-500/0">
              <Link href="/schedule" className="block h-full">
                <div className="relative h-full flex flex-col">
                  <CardHeader className="relative">
                    <div className="flex items-start gap-4">
                      <div className="p-3 rounded-xl bg-blue-500/10 group-hover:bg-blue-500/20 transition-colors">
                        <Calendar className="h-6 w-6 text-blue-500" />
                      </div>
                      <div className="flex-1 space-y-1">
                        <CardTitle className="text-xl">View Schedule</CardTitle>
                        <CardDescription className="text-base">
                          See your scheduled tasks and availability
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="relative flex-1 flex flex-col justify-end">
                    <Button
                      variant="ghost"
                      className="w-full group-hover:bg-blue-500 group-hover:text-white transition-colors justify-between"
                    >
                      <span>Open Schedule</span>
                      <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </CardContent>
                </div>
              </Link>
            </Card>

            <Card className="group hover:shadow-xl hover:scale-[1.02] transition-all duration-300 border-2 hover:border-purple-500/50 cursor-pointer overflow-hidden bg-linear-to-br from-background to-background hover:from-purple-500/5 hover:to-purple-500/0">
              <Link href="/settings" className="block h-full">
                <div className="relative h-full flex flex-col">
                  <CardHeader className="relative">
                    <div className="flex items-start gap-4">
                      <div className="p-3 rounded-xl bg-purple-500/10 group-hover:bg-purple-500/20 transition-colors">
                        <Settings className="h-6 w-6 text-purple-500" />
                      </div>
                      <div className="flex-1 space-y-1">
                        <CardTitle className="text-xl">Settings</CardTitle>
                        <CardDescription className="text-base">
                          Configure your preferences and availability
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="relative flex-1 flex flex-col justify-end">
                    <Button
                      variant="ghost"
                      className="w-full group-hover:bg-purple-500 group-hover:text-white transition-colors justify-between"
                    >
                      <span>Open Settings</span>
                      <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </CardContent>
                </div>
              </Link>
            </Card>
          </div>

          {/* Features Section */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Sparkles className="h-5 w-5 text-primary" />
                  </div>
                  <CardTitle className="text-base">AI-Powered</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Automatically extract tasks from your content using advanced
                  AI
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-500/10">
                    <Target className="h-5 w-5 text-blue-500" />
                  </div>
                  <CardTitle className="text-base">Smart Scheduling</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Intelligent task scheduling based on your availability and
                  priorities
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-orange-500/10">
                    <Clock className="h-5 w-5 text-orange-500" />
                  </div>
                  <CardTitle className="text-base">Time Management</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Track time estimates and deadlines for better planning
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-green-500/10">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  </div>
                  <CardTitle className="text-base">Stay Organized</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Keep track of drafts, scheduled, and completed tasks
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </main>
  );
}
