"use client";

import TasksSplitView from "@/components/tasks/TasksSplitView";
import { TaskDraftsProvider } from "@/context/task-drafts-context";

export default function TasksPage() {
  return (
    <TaskDraftsProvider>
      <TasksSplitView />
    </TaskDraftsProvider>
  );
}
