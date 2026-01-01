"use client";

import TaskList from "./TaskList";
import Link from "next/link";
import { useCallback } from "react";
import { useSchedule } from "@/context/schedule-context";
import { useTaskList } from "@/hooks/useTaskLists";

export default function CompletedTasks() {
  const { tasks: completedTasks, fetchTasks } = useTaskList("/tasks/completed");
  const { deleteTasks } = useSchedule();

  const deleteSelectedTasks = useCallback(
    async (selectedIndices: Set<number>) => {
      const selectedTasks = completedTasks.filter((task, index) =>
        selectedIndices.has(index)
      );
      const success = await deleteTasks(selectedTasks.map((task) => task.id));
      if (success) {
        await fetchTasks();
      }
    },
    [completedTasks, fetchTasks, deleteTasks]
  );

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
