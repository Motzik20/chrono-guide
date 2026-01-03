"use client";

import { useJobManager } from "@/context/job-context";
import { Loader2, Clock, CheckCircle2, XCircle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function JobList() {
  const { jobs, dismissJob } = useJobManager();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pending":
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case "running":
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
      case "success":
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "pending":
        return "Queued";
      case "running":
        return "Processing";
      case "success":
        return "Completed";
      case "failed":
        return "Failed";
      default:
        return status;
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-4 w-full h-full">
      <Card className="mx-auto max-w-2xl w-full h-full">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold tracking-tight">
            Active Jobs
          </CardTitle>
          <CardDescription>
            {jobs.length === 0
              ? "No jobs running"
              : `${jobs.length} ${jobs.length === 1 ? "job" : "jobs"} in progress`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {jobs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
              <p className="text-sm">No active jobs</p>
              <p className="text-xs mt-1">Upload a file to see jobs here</p>
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className="flex items-center gap-3 p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="shrink-0">{getStatusIcon(job.status)}</div>
                  <div className="flex-1 min-w-0">
                    <p
                      className="text-sm font-medium text-ellipsis"
                      title={job.filename}
                    >
                      {job.filename}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {getStatusText(job.status)}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 shrink-0"
                    onClick={() => dismissJob(job.id)}
                  >
                    <X className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
