"use client";

import TasksSplitView from "@/components/tasks/TasksSplitView";
import IngestionInput from "@/components/tasks/IngestionInput";
import TaskDrafts from "@/components/tasks/TaskDrafts";

export default function TasksPage() {
  return (
    <TasksSplitView
      leftContent={<IngestionInput />}
      rightContent={<TaskDrafts />}
    />
  );
}
