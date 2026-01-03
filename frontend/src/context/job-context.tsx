"use client";

import { toast } from "sonner";
import {
  createContext,
  useState,
  useEffect,
  useContext,
  useCallback,
} from "react";
import { z } from "zod";
import { apiRequest } from "@/lib/chrono-client";

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

const trackedJobSchema = z.object({
  id: z.string(),
  filename: z.string(),
  status: z.enum(["pending", "running", "success", "failed"]),
  result: z
    .object({
      draft_ids: z.array(z.number()),
      created_count: z.number(),
    })
    .nullable()
    .optional(),
  error: z.string().nullable().optional(),
  created_at: z.number(),
});

type TrackedJob = z.infer<typeof trackedJobSchema>;

interface JobContextType {
  jobs: TrackedJob[];
  addJob: (file: File) => Promise<void>;
  dismissJob: (jobId: string) => void;
}
export const JobContext = createContext<JobContextType | undefined>(undefined);

export function JobProvider({ children }: { children: React.ReactNode }) {
  const [jobs, setJobs] = useState<TrackedJob[]>(() => {
    try {
      const storedJobs = localStorage.getItem("background-jobs");
      return storedJobs ? JSON.parse(storedJobs) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem("background-jobs", JSON.stringify(jobs));
  }, [jobs]);

  const dismissJob = useCallback((jobId: string) => {
    setJobs((prevJobs) => prevJobs.filter((job) => job.id !== jobId));
  }, []);

  const updateJobStatus = (
    job: TrackedJob,
    jobStatus: z.infer<typeof jobStatusSchema>
  ) => {
    if (jobStatus.status !== job.status) {
      setJobs((prevJobs) => {
        let updatedJobs = prevJobs.map((j) =>
          j.id === job.id
            ? {
                ...j,
                status: jobStatus.status,
                result: jobStatus.result,
                error: jobStatus.error,
              }
            : j
        );

        if (jobStatus.status === "success" && jobStatus.result) {
          toast.success(
            `Successfully created ${jobStatus.result.created_count} draft task${jobStatus.result.created_count === 1 ? "" : "s"}`
          );
        } else if (jobStatus.status === "failed") {
          toast.error(jobStatus.error || "Job failed");
        }

        return updatedJobs;
      });
    }
  };

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
            console.error("Failed to fetch job status:", error);
            // Don't throw - just log the error
          }
        })
      );
    }, 2000);

    return () => clearInterval(intervalCheck);
  }, [jobs]);

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

  return (
    <JobContext.Provider value={{ jobs, addJob, dismissJob }}>
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
