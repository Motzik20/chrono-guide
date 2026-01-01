"use client";

import TaskList from "./TaskList";
import { Task, TasksResponseSchema } from "@/lib/task-types";
import { apiRequest } from "@/lib/chrono-client";
import Link from "next/link";
import { useState, useEffect, useCallback } from "react";
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
      await deleteTasks(selectedTasks.map((task) => task.id));
    },
    [completedTasks, fetchTasks]
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
