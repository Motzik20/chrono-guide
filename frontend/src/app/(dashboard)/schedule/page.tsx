"use client";

import TasksSplitView from "@/components/tasks/TasksSplitView";
import TaskLifecycleTabs from "@/components/tasks/TaskLifecycleTabs";
import ScheduleItemsList from "@/components/schedule/ScheduleItemsList";

export default function SchedulePage() {
  return (
    <TasksSplitView
      leftContent={<TaskLifecycleTabs />}
      rightContent={<ScheduleItemsList />}
    />
  );
}
