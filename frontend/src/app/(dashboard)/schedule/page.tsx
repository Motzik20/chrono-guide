"use client";

import TasksSplitView from "@/components/tasks/TasksSplitView";
import TaskLifecycleTabs from "@/components/tasks/TaskLifecycleTabs";

export default function SchedulePage() {
  return (
    <TasksSplitView
      leftContent={<TaskLifecycleTabs />}
      rightContent={<div>Right Content</div>}
    />
  );
}
