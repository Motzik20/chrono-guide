"use client";

import TasksSplitView from "@/components/tasks/TasksSplitView";
import IngestionInput from "@/components/tasks/IngestionInput";
import { JobList } from "@/components/jobs/JobList";

export default function TasksPage() {
  return (
    <TasksSplitView
      leftContent={<IngestionInput />}
      rightContent={<JobList />}
    />
  );
}
