"use client";

import { toast } from "sonner";
import {
  createContext,
  useState,
  useEffect,
  useContext,
  useCallback,
  useRef,
} from "react";
import { z } from "zod";
import { apiRequest, ApiError } from "@/lib/chrono-client";
import { useAuth } from "./auth-context";

const jobResponseSchema = z.object({
  job_id: z.string(),
  status: z.string().optional(),
});

const jobStatusSchema = z.object({
  id: z.string(),
  status: z.enum(["pending", "running", "success", "failed"]),
  result: z
    .object({
      draft_ids: z.array(z.number()),
      created_count: z.number(),
    })
    .nullable()
    .optional(),
  error: z.string().nullable().optional(),
});

type TrackedJob = {
  id: string;
  filename: string;
  status: "pending" | "running" | "success" | "failed";
  result?: {
    draft_ids: number[];
    created_count: number;
  } | null;
  error?: string | null;
  created_at?: number;
};

interface JobContextType {
  jobs: TrackedJob[];
  addJob: (file: File) => Promise<void>;
  addTextJob: (text: string) => Promise<void>;
  dismissJob: (jobId: string) => void;
}
export const JobContext = createContext<JobContextType | undefined>(undefined);

export function JobProvider({ children }: { children: React.ReactNode }) {
  const [jobs, setJobs] = useState<TrackedJob[]>([]);
  const [isHydrated, setIsHydrated] = useState(false);
  const toastShownRef = useRef<Set<string>>(new Set());
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) {
      setJobs([]);
      localStorage.removeItem("background-jobs");
      toastShownRef.current.clear();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      const storedJobs = localStorage.getItem("background-jobs");
      if (storedJobs) {
        setJobs(JSON.parse(storedJobs));
      }
    }
    setIsHydrated(true);
  }, [isAuthenticated]);

  useEffect(() => {
    if (isHydrated) {
      localStorage.setItem("background-jobs", JSON.stringify(jobs));
    }
  }, [jobs, isHydrated]);

  const dismissJob = useCallback((jobId: string) => {
    setJobs((prevJobs) => prevJobs.filter((job) => job.id !== jobId));
    // Clean up toast tracking when job is dismissed
    toastShownRef.current.delete(jobId);
  }, []);

  const updateJobStatus = useCallback(
    (job: TrackedJob, jobStatus: z.infer<typeof jobStatusSchema>) => {
      if (jobStatus.status !== job.status) {
        const toastKey = `${job.id}-${jobStatus.status}`;
        const hasShownToast = toastShownRef.current.has(toastKey);

        setJobs((prevJobs) => {
          return prevJobs.map((j) =>
            j.id === job.id
              ? {
                  ...j,
                  status: jobStatus.status,
                  result: jobStatus.result,
                  error: jobStatus.error,
                }
              : j
          );
        });

        // Show toast only once per status transition
        if (!hasShownToast) {
          toastShownRef.current.add(toastKey);

          if (jobStatus.status === "success" && jobStatus.result) {
            if (jobStatus.result.created_count > 0) {
              toast.success(
                `Successfully created ${jobStatus.result.created_count} draft task${jobStatus.result.created_count === 1 ? "" : "s"}`
              );
            } else {
              toast.info("No drafts created");
            }
          } else if (jobStatus.status === "failed") {
            toast.error(jobStatus.error || "Job failed");
          }
        }
      }
    },
    []
  );

  useEffect(() => {
    const activeJobs = jobs.filter(
      (job) => job.status === "pending" || job.status === "running"
    );

    if (activeJobs.length === 0) {
      return;
    }

    const intervalCheck = setInterval(async () => {
      await Promise.all(
        activeJobs.map(async (job) => {
          try {
            const jobStatus = await apiRequest(
              `/tasks/jobs/${job.id}`,
              jobStatusSchema,
              {
                method: "GET",
              }
            );
            if (jobStatus.status !== job.status) {
              updateJobStatus(job, jobStatus);
            }
          } catch (error) {
            // If job doesn't belong to current user (403) or doesn't exist (404), remove it
            if (
              error instanceof ApiError &&
              (error.status === 403 || error.status === 404)
            ) {
              setJobs((prevJobs) => prevJobs.filter((j) => j.id !== job.id));
            } else {
              console.error("Failed to fetch job status:", error);
            }
          }
        })
      );
    }, 2000);

    return () => clearInterval(intervalCheck);
  }, [jobs, updateJobStatus]);

  const addJob = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const jobResponse = await apiRequest(
        "/tasks/ingest/file",
        jobResponseSchema,
        {
          method: "POST",
          body: formData,
        }
      );

      const newJob: TrackedJob = {
        id: jobResponse.job_id,
        filename: file.name,
        status: "pending",
        created_at: Date.now(),
      };
      // No toast - the persistent notification bar will show the job status
      setJobs([...jobs, newJob]);
    } catch (error) {
      console.error("Failed to add job:", error);
      throw error;
    }
  };

  const addTextJob = async (text: string) => {
    try {
      const jobResponse = await apiRequest(
        "/tasks/ingest/text",
        jobResponseSchema,
        {
          method: "POST",
          body: JSON.stringify({ text }),
        }
      );

      const newJob: TrackedJob = {
        id: jobResponse.job_id,
        filename: "Text Input",
        status: "pending",
        created_at: Date.now(),
      };
      // No toast - the persistent notification bar will show the job status
      setJobs([...jobs, newJob]);
    } catch (error) {
      console.error("Failed to add text job:", error);
      throw error;
    }
  };

  return (
    <JobContext.Provider value={{ jobs, addJob, addTextJob, dismissJob }}>
      {children}
    </JobContext.Provider>
  );
}

export const useJobManager = () => {
  const context = useContext(JobContext);
  if (context === undefined) {
    throw new Error("useJobManager must be used within a JobProvider");
  }
  return context;
};
