import { useState, useCallback, useEffect } from "react";
import { apiRequest } from "@/lib/chrono-client";
import { TasksResponseSchema, Task } from "@/lib/task-types";
import { useSchedule } from "@/context/schedule-context";

export function useTaskList(endpoint: string) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchTasks = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await apiRequest(endpoint, TasksResponseSchema, {
        method: "GET",
      });
      setTasks(data);
    } finally {
      setIsLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  return { tasks, fetchTasks, isLoading };
}
