"use client";

import IngestionInput from "./IngestionInput";
import { Separator } from "@/components/ui/separator";
import TaskDrafts from "./TaskDrafts";

export default function TasksSplitView() {
  return (
    <div className="flex w-full h-full flex-row">
      <div className="w-1/2 flex justify-center items-center p-4">
        <IngestionInput />
      </div>
      <Separator orientation="vertical" className="" />
      <div className="w-1/2 flex justify-center items-center p-4">
        <TaskDrafts />
      </div>
    </div>
  );
}
