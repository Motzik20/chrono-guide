"use client";

import TasksSplitView from "@/components/tasks/TasksSplitView";
import { TaskDraftsProvider } from "@/context/task-drafts-context";
import IngestionInput from "@/components/tasks/IngestionInput";
import TaskDrafts from "@/components/tasks/TaskDrafts";

export default function TasksPage() {
  return (
    <TaskDraftsProvider>
      <TasksSplitView
        leftContent={<IngestionInput />}
        rightContent={<TaskDrafts />}
      />
    </TaskDraftsProvider>
  );
}
