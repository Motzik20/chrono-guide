"use client";

import { useState } from "react";
import IngestionInput, { type TaskDraft } from "./IngestionInput";
import { Separator } from "@/components/ui/separator";
import TaskDrafts from "./TaskDrafts";

export default function TasksSplitView() {
  const [drafts, setDrafts] = useState<TaskDraft[]>([]);

  const handleDraftsReceived = (newDrafts: TaskDraft[]) => {
    setDrafts(newDrafts);
  };

  const handleDraftUpdate = (index: number, updatedDraft: TaskDraft) => {
    setDrafts((prev) => {
      const newDrafts = [...prev];
      newDrafts[index] = updatedDraft;
      return newDrafts;
    });
  };

  return (
    <div className="flex w-full h-full flex-row">
      <div className="w-1/2 flex justify-center items-center p-4">
        <IngestionInput onDraftsReceived={handleDraftsReceived} />
      </div>
      <Separator orientation="vertical" className="" />
      <div className="w-1/2 flex justify-center items-center p-4">
        <TaskDrafts drafts={drafts} onDraftUpdate={handleDraftUpdate} />
      </div>
    </div>
  );
}
