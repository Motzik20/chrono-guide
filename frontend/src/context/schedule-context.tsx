"use client";

import React, { createContext, useContext, useCallback, useState } from "react";
import { apiRequest } from "@/lib/chrono-client";
import { z } from "zod";
import { ScheduleResponseSchema, ScheduleResponse } from "@/lib/task-types";
import { toast } from "sonner";

interface ScheduleContextType {
  deleteTasks: (taskIds: number[]) => Promise<boolean>;
  descheduleTasks: (taskIds: number[]) => Promise<boolean>;
  refreshScheduleItems: () => void;
  refreshTrigger: number;
  scheduleTasks: (taskIds: number[]) => Promise<ScheduleResponse | null>;
}

const ScheduleContext = createContext<ScheduleContextType | undefined>(
  undefined
);

export function ScheduleProvider({ children }: { children: React.ReactNode }) {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const refreshScheduleItems = useCallback(() => {
    setRefreshTrigger((prev) => prev + 1);
  }, []);

  async function deleteTasks(taskIds: number[]): Promise<boolean> {
    if (taskIds.length === 0) {
      return true;
    }

    try {
      await apiRequest("/tasks/bulk", z.object({}), {
        method: "DELETE",
        body: JSON.stringify(taskIds),
      });
      refreshScheduleItems();
      const taskWord = taskIds.length === 1 ? "task" : "tasks";
      toast.success(`Successfully deleted ${taskIds.length} ${taskWord}`);
      return true;
    } catch {
      toast.error("Failed to delete tasks. Please try again.");
      return false;
    }
  }

  async function scheduleTasks(
    taskIds: number[]
  ): Promise<ScheduleResponse | null> {
    if (taskIds.length === 0) {
      toast.warning("No tasks selected to schedule");
      return null;
    }

    try {
      const response = await apiRequest(
        "/schedule/generate/selected",
        ScheduleResponseSchema,
        {
          method: "POST",
          body: JSON.stringify({
            task_ids: taskIds,
          }),
        }
      );
      refreshScheduleItems();

      const scheduledCount = response.schedule_blocks.length;
      const warningCount = response.warnings.length;

      if (scheduledCount > 0 && warningCount === 0) {
        const taskWord = scheduledCount === 1 ? "task" : "tasks";
        toast.success(`Successfully scheduled ${scheduledCount} ${taskWord}`);
      } else if (scheduledCount > 0 && warningCount > 0) {
        toast.warning(
          `Scheduled ${scheduledCount} task(s), but ${warningCount} could not be scheduled`
        );
      } else if (scheduledCount === 0) {
        toast.error(
          "Could not schedule any tasks. Check availability settings."
        );
      }

      return response;
    } catch {
      toast.error("Failed to schedule tasks. Please try again.");
      return null;
    }
  }

  async function descheduleTasks(taskIds: number[]): Promise<boolean> {
    if (taskIds.length === 0) {
      return true;
    }

    try {
      await apiRequest("/tasks/deschedule", z.object({}), {
        method: "POST",
        body: JSON.stringify({
          task_ids: taskIds,
        }),
      });
      refreshScheduleItems();
      const taskWord = taskIds.length === 1 ? "task" : "tasks";
      toast.success(`Successfully descheduled ${taskIds.length} ${taskWord}`);
      return true;
    } catch {
      toast.error("Failed to deschedule tasks. Please try again.");
      return false;
    }
  }

  return (
    <ScheduleContext.Provider
      value={{
        deleteTasks,
        descheduleTasks,
        scheduleTasks,
        refreshScheduleItems,
        refreshTrigger,
      }}
    >
      {children}
    </ScheduleContext.Provider>
  );
}

export function useSchedule() {
  const context = useContext(ScheduleContext);
  if (context === undefined) {
    throw new Error("useSchedule must be used within a ScheduleProvider");
  }
  return context;
}
