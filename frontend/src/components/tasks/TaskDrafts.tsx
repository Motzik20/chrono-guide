"use client";

import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useTaskDrafts } from "@/context/task-drafts-context";
import { EditDialog } from "./EditDialog";
import { TaskCard } from "./TaskCard";
import { apiRequest } from "@/lib/chrono-client";

export default function TaskDrafts() {
  const { drafts, deleteDrafts } = useTaskDrafts();
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(
    new Set()
  );

  const allSelected =
    drafts.length > 0 && selectedIndices.size === drafts.length;
  const someSelected =
    drafts.length > 0 &&
    selectedIndices.size > 0 &&
    selectedIndices.size < drafts.length;

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIndices(new Set(drafts.map((_, index) => index)));
      console.log("Selected all tasks:", selectedIndices);
    } else {
      setSelectedIndices(new Set());
      console.log("Unselected all tasks:", selectedIndices);
    }
  };

  const handleDraftSelect = (index: number, checked: boolean) => {
    setSelectedIndices((prev) => {
      const newSet = new Set(selectedIndices);
      if (checked) {
        newSet.add(index);
      } else {
        newSet.delete(index);
      }
      return newSet;
    });
  };

  async function saveAllTasks() {
    // TODO: Implement save all tasks
  }

  const deleteSelectedTasks = () => {
    console.log("Deleting selected tasks:", selectedIndices);
    deleteDrafts(selectedIndices);
    setSelectedIndices(new Set());
  };

  if (drafts.length === 0) {
    return (
      <Card className="mx-auto w-1/2 max-w-2xl">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold tracking-tight">
            Task Drafts
          </CardTitle>
          <CardDescription>
            Task drafts will appear here after ingestion
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="mx-auto max-w-2xl w-full space-y-4">
      <Card>
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="flex justify-between">
            <p className="text-2xl font-bold tracking-tight">Task Drafts</p>
            <p className="text-sm text-muted-foreground">Select all</p>
          </CardTitle>
          <CardDescription className="flex justify-between">
            {drafts.length} {drafts.length === 1 ? "draft" : "drafts"} found
            <Checkbox
              checked={allSelected}
              onCheckedChange={handleSelectAll}
              className="h-6 w-6 border border-slate-500"
            />
          </CardDescription>
        </CardHeader>
      </Card>
      <div className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto">
        {drafts.map((draft, index) => (
          <TaskCard
            key={index}
            index={index}
            task={draft}
            isSelected={selectedIndices.has(index)}
            onSelect={handleDraftSelect}
          />
        ))}
      </div>
      <div className="flex justify-end gap-2">
        <Button className="flex-1" onClick={() => saveAllTasks()}>
          Save All Tasks
        </Button>
        <Button
          variant="destructive"
          className="flex-1"
          onClick={() => deleteSelectedTasks()}
        >
          Delete Selected Tasks
        </Button>
        <EditDialog
          selectedIndices={selectedIndices}
          trigger={
            <Button
              variant="outline"
              className="flex-1"
              disabled={selectedIndices.size === 0}
            >
              Edit Selected ({selectedIndices.size})
            </Button>
          }
        />
      </div>
    </div>
  );
}
