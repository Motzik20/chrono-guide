"use client";

import { useCallback } from "react";
import TaskList from "./TaskList";
import { TasksResponseSchema } from "@/lib/task-types";
import { apiRequest } from "@/lib/chrono-client";
import Link from "next/link";
import { useSchedule } from "@/context/schedule-context";
import { useTaskList } from "@/hooks/useTaskLists";
import { toast } from "sonner";
import { Trash } from "lucide-react";

export default function ScheduledTasks() {
  const { tasks: scheduledTasks, fetchTasks } = useTaskList("/tasks/scheduled");
  const { deleteTasks, refreshScheduleItems } = useSchedule();

  const markAsCompleted = useCallback(
    async (selectedIndices: Set<number>) => {
      const selectedTasks = scheduledTasks.filter((task, index) =>
        selectedIndices.has(index)
      );

      if (selectedTasks.length === 0) {
        toast.warning("No tasks selected");
        return;
      }

      try {
        await apiRequest("/tasks/mark-as-completed", TasksResponseSchema, {
          method: "POST",
          body: JSON.stringify({
            task_ids: selectedTasks.map((task) => task.id),
          }),
        });

        const taskWord = selectedTasks.length === 1 ? "task" : "tasks";
        toast.success(
          `Marked ${selectedTasks.length} ${taskWord} as completed`
        );
        await fetchTasks();
        refreshScheduleItems();
      } catch {
        toast.error("Failed to mark tasks as completed. Please try again.");
      }
    },
    [scheduledTasks, fetchTasks, refreshScheduleItems]
  );

  const deleteSelectedTasks = useCallback(
    async (selectedIndices: Set<number>) => {
      const selectedTasks = scheduledTasks.filter((task, index) =>
        selectedIndices.has(index)
      );
      const taskIds = selectedTasks.map((task) => task.id);
      const success = await deleteTasks(taskIds);
      if (success) {
        await fetchTasks();
      }
    },
    [scheduledTasks, fetchTasks, deleteTasks]
  );

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
          label: "Mark as Completed",
          onClick: markAsCompleted,
        },
        {
          label: "Delete Selected Tasks",
          onClick: deleteSelectedTasks,
          variant: "destructive",
          icon: <Trash className="h-4 w-4" />,
        },
      ]}
    />
  );
}
