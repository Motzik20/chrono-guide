"use client";

import TaskList from "./TaskList";
import { Task } from "@/lib/task-types";
import { ScheduleResponseSchema, TasksResponseSchema } from "@/lib/task-types";
import { apiRequest } from "@/lib/chrono-client";
import Link from "next/link";
import { useState, useEffect, useCallback } from "react";

export default function UnscheduledTasks() {
  const [unscheduledTasks, setUnscheduledTasks] = useState<Task[]>([]);

  const scheduleTasks = useCallback(
    async (selectedIndices: Set<number>) => {
      const selectedTasks = unscheduledTasks.filter((task, index) =>
        selectedIndices.has(index)
      );
      const response = await apiRequest(
        "/schedule/generate/selected",
        ScheduleResponseSchema,
        {
          method: "POST",
          body: JSON.stringify({
            task_ids: selectedTasks.map((task) => task.id),
          }),
        }
      );
      console.log("Response:", response);
    },
    [unscheduledTasks]
  );

  const deleteSelectedTasks = useCallback(
    async (selectedIndices: Set<number>) => {
      const selectedTasks = unscheduledTasks.filter((task, index) =>
        selectedIndices.has(index)
      );
      console.log("Deleting selected tasks:", selectedTasks);
      // TODO: Implement delete API call
    },
    [unscheduledTasks]
  );

  const fetchUnscheduledTasks = useCallback(async () => {
    const tasks = await apiRequest("/tasks/unscheduled", TasksResponseSchema, {
      method: "GET",
    });
    setUnscheduledTasks(tasks);
  }, []);

  useEffect(() => {
    fetchUnscheduledTasks();
  }, [fetchUnscheduledTasks]);

  return (
    <TaskList
      tasks={unscheduledTasks}
      title="Schedulable Tasks"
      description={(taskCount) =>
        `${taskCount} ${taskCount === 1 ? "task" : "tasks"} ready to be scheduled`
      }
      emptyStateTitle="Tasks"
      emptyStateDescription={
        <>
          Tasks will appear here after saving them under{" "}
          <Link href="/tasks">Tasks</Link>
        </>
      }
      actionButtons={[
        {
          label: "Delete Selected Tasks",
          onClick: deleteSelectedTasks,
          variant: "destructive",
        },
        {
          label: "Schedule Selected Tasks",
          onClick: scheduleTasks,
        },
      ]}
    />
  );
}
