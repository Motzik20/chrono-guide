import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import UnscheduledTasks from "./UnscheduledTasks";
import ScheduledTasks from "./ScheduledTasks";
import CompletedTasks from "./CompletedTasks";

interface TaskLifecycleTabsProps {
  onScheduleItemsChange?: () => void;
}

export default function TaskLifecycleTabs({}: TaskLifecycleTabsProps) {
  return (
    <Tabs defaultValue="unscheduled" className="w-full h-full flex flex-col">
      <TabsList className="grid w-full grid-cols-3 h-12 flex-shrink-0">
        <TabsTrigger value="unscheduled" className="text-lg">
          Unscheduled
        </TabsTrigger>
        <TabsTrigger value="scheduled" className="text-lg">
          Scheduled
        </TabsTrigger>
        <TabsTrigger value="completed" className="text-lg">
          Completed
        </TabsTrigger>
      </TabsList>
      <div className="flex-1 min-h-0 relative mt-2">
        <TabsContent value="unscheduled" className="absolute inset-0">
          <UnscheduledTasks />
        </TabsContent>
        <TabsContent value="scheduled" className="absolute inset-0">
          <ScheduledTasks />
        </TabsContent>
        <TabsContent value="completed" className="absolute inset-0">
          <CompletedTasks />
        </TabsContent>
      </div>
    </Tabs>
  );
}
