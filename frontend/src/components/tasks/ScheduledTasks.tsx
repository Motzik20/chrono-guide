"use client";

import { useEffect, useState, useCallback } from "react";
import TaskList from "./TaskList";
import { Task, TasksResponseSchema } from "@/lib/task-types";
import { apiRequest } from "@/lib/chrono-client";
import Link from "next/link";

export default function ScheduledTasks() {
  const [scheduledTasks, setScheduledTasks] = useState<Task[]>([]);

  const markAsCompleted = useCallback(
    async (selectedIndices: Set<number>) => {
      const selectedTasks = scheduledTasks.filter((task, index) =>
        selectedIndices.has(index)
      );
      const response = await apiRequest(
        "/tasks/mark-as-completed",
        TasksResponseSchema,
        {
          method: "POST",
          body: JSON.stringify({
            task_ids: selectedTasks.map((task) => task.id),
          }),
        }
      );
      console.log("Response:", response);
    },
    [scheduledTasks]
  );

  const deleteSelectedTasks = useCallback(
    async (selectedIndices: Set<number>) => {
      const selectedTasks = scheduledTasks.filter((task, index) =>
        selectedIndices.has(index)
      );
      console.log("Deleting selected tasks:", selectedTasks);
      // TODO: Implement delete API call
    },
    [scheduledTasks]
  );

  const fetchScheduledTasks = useCallback(async () => {
    const tasks = await apiRequest("/tasks/scheduled", TasksResponseSchema, {
      method: "GET",
    });
    setScheduledTasks(tasks);
  }, []);

  useEffect(() => {
    fetchScheduledTasks();
  }, [fetchScheduledTasks]);

  return (
    <TaskList
      tasks={scheduledTasks}
      title="Scheduled Tasks"
      description={(taskCount) =>
        `${taskCount} ${taskCount === 1 ? "task" : "tasks"} scheduled`
      }
      emptyStateTitle="Scheduled Tasks"
      emptyStateDescription={
        <>
          No scheduled tasks. Schedule tasks from the{" "}
          <Link href="/schedule">Unscheduled</Link> tab.
        </>
      }
      actionButtons={[
        {
          label: "Delete Selected Tasks",
          onClick: deleteSelectedTasks,
          variant: "destructive",
        },
        {
          label: "Mark as Completed",
          onClick: markAsCompleted,
        },
      ]}
    />
  );
}
