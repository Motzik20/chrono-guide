"use client";

import { useState } from "react";
import IngestionInput, { type TaskDraft } from "./IngestionInput";
import { Separator } from "@/components/ui/separator";
import TaskDrafts from "./TaskDrafts";
import { TaskDraftsProvider } from "@/context/task-drafts-context";

export default function TasksSplitView() {
  return (
    <TaskDraftsProvider>
      <div className="flex w-full h-full flex-row">
        <div className="w-1/2 flex justify-center items-center p-4">
          <IngestionInput />
        </div>
        <Separator orientation="vertical" className="" />
        <div className="w-1/2 flex justify-center items-center p-4">
          <TaskDrafts />
        </div>
      </div>
    </TaskDraftsProvider>
  );
}
