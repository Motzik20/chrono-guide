"use client";

import TaskList from "./TaskList";
import Link from "next/link";
import { useCallback } from "react";
import { useSchedule } from "@/context/schedule-context";
import { useTaskList } from "@/hooks/useTaskLists";

export default function UnscheduledTasks() {
  const { tasks: unscheduledTasks, fetchTasks } =
    useTaskList("/tasks/unscheduled");
  const { deleteTasks, scheduleTasks } = useSchedule();

  const handleScheduleTasks = useCallback(
    async (selectedIndices: Set<number>) => {
      const selectedTasks = unscheduledTasks.filter((task, index) =>
        selectedIndices.has(index)
      );
      const taskIds = selectedTasks.map((task) => task.id);
      await scheduleTasks(taskIds);
      await fetchTasks();
    },
    [unscheduledTasks, scheduleTasks]
  );

  const deleteSelectedTasks = useCallback(
    async (selectedIndices: Set<number>) => {
      const selectedTasks = unscheduledTasks.filter((task, index) =>
        selectedIndices.has(index)
      );
      const taskIds = selectedTasks.map((task) => task.id);
      await deleteTasks(taskIds);
      await fetchTasks();
    },
    [unscheduledTasks, fetchTasks]
  );

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
          onClick: handleScheduleTasks,
        },
      ]}
    />
  );
}
