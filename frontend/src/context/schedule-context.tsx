"use client";

import React, { createContext, useContext, useCallback, useState } from "react";
import { apiRequest } from "@/lib/chrono-client";
import { z } from "zod";
import { ScheduleResponseSchema, ScheduleResponse } from "@/lib/task-types";

interface ScheduleContextType {
  deleteTasks: (taskIds: number[]) => Promise<void>;
  refreshScheduleItems: () => void;
  refreshTrigger: number;
  scheduleTasks: (taskIds: number[]) => Promise<ScheduleResponse>;
}

const ScheduleContext = createContext<ScheduleContextType | undefined>(
  undefined
);

export function ScheduleProvider({ children }: { children: React.ReactNode }) {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const refreshScheduleItems = useCallback(() => {
    setRefreshTrigger((prev) => prev + 1);
  }, []);

  async function deleteTasks(taskIds: number[]): Promise<void> {
    if (taskIds.length === 0) {
      return;
    }

    await apiRequest("/tasks/bulk", z.object({}), {
      method: "DELETE",
      body: JSON.stringify(taskIds),
    });
    refreshScheduleItems();
  }

  async function scheduleTasks(taskIds: number[]): Promise<ScheduleResponse> {
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
    return response;
  }

  return (
    <ScheduleContext.Provider
      value={{
        deleteTasks,
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
