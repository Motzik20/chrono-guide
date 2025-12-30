"use client";

import TasksSplitView from "@/components/tasks/TasksSplitView";
import ScheduleTasks from "@/components/tasks/ScheduleTasks";

export default function SchedulePage() {
  return (
    <TasksSplitView
      leftContent={<ScheduleTasks />}
      rightContent={<div>Right Content</div>}
    />
  );
}
