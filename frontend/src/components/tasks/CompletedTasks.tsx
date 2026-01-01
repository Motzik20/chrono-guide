"use client";

import TaskList from "./TaskList";
import { Task, TasksResponseSchema } from "@/lib/task-types";
import { apiRequest } from "@/lib/chrono-client";
import Link from "next/link";
import { useState, useEffect, useCallback } from "react";

export default function CompletedTasks() {
  const [completedTasks, setCompletedTasks] = useState<Task[]>([]);

  const deleteSelectedTasks = useCallback(
    async (selectedIndices: Set<number>) => {
      const selectedTasks = completedTasks.filter((task, index) =>
        selectedIndices.has(index)
      );
      console.log("Deleting selected tasks:", selectedTasks);
      // TODO: Implement delete API call
    },
    [completedTasks]
  );

  const fetchCompletedTasks = useCallback(async () => {
    const tasks = await apiRequest("/tasks/completed", TasksResponseSchema, {
      method: "GET",
    });
    setCompletedTasks(tasks);
  }, []);

  useEffect(() => {
    fetchCompletedTasks();
  }, [fetchCompletedTasks]);

  return (
    <TaskList
      tasks={completedTasks}
      title="Completed Tasks"
      description={(taskCount) =>
        `${taskCount} ${taskCount === 1 ? "task" : "tasks"} completed`
      }
      emptyStateTitle="Completed Tasks"
      emptyStateDescription={
        <>
          No completed tasks yet. Complete tasks from the{" "}
          <Link href="/schedule">Scheduled</Link> tab.
        </>
      }
      actionButtons={[
        {
          label: "Delete Selected Tasks",
          onClick: deleteSelectedTasks,
          variant: "destructive",
        },
      ]}
    />
  );
}
