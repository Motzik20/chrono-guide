import { useState, useCallback, useEffect } from "react";
import { apiRequest, ApiError } from "@/lib/chrono-client";
import { TasksResponseSchema, Task } from "@/lib/task-types";
import { toast } from "sonner";

export function useTaskList(endpoint: string) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiRequest(endpoint, TasksResponseSchema, {
        method: "GET",
      });
      setTasks(data);
    } catch (err) {
      const errorMessage =
        err instanceof ApiError ? err.message : "Failed to load tasks";
      setError(errorMessage);
      toast.error(errorMessage);
      setTasks([]);
    } finally {
      setIsLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  return { tasks, fetchTasks, isLoading, error };
}
