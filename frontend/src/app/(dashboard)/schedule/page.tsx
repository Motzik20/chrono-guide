"use client";

import TasksSplitView from "@/components/tasks/TasksSplitView";
import TaskLifecycleTabs from "@/components/tasks/TaskLifecycleTabs";
import ScheduleItemsList from "@/components/schedule/ScheduleItemsList";
import { ScheduleProvider } from "@/context/schedule-context";

export default function SchedulePage() {
  return (
    <ScheduleProvider>
      <TasksSplitView
        leftContent={<TaskLifecycleTabs />}
        rightContent={<ScheduleItemsList />}
      />
    </ScheduleProvider>
  );
}
