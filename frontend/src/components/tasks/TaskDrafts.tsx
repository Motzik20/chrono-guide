"use client";

import { useState } from "react";
import { z } from "zod";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useTaskDrafts } from "@/context/task-drafts-context";
import { DraftEditDialog } from "./DraftEditDialog";
import { TaskCard } from "./TaskCard";
import { apiRequest, ApiError } from "@/lib/chrono-client";
import { toast } from "sonner";
import { Pencil } from "lucide-react";
import TaskList from "./TaskList";
import { TaskDraft } from "@/lib/task-types";

const tasksCreateSchema = z.object({
  task_ids: z.array(z.number()),
  created_count: z.number(),
});

export default function TaskDrafts() {
  const { drafts, deleteDrafts, clearDrafts } = useTaskDrafts();
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
    try {
      const response = await apiRequest("/tasks/bulk", tasksCreateSchema, {
        method: "POST",
        body: JSON.stringify(drafts),
      });
      const { task_ids, created_count } = response;

      if (created_count === 0) {
        toast.error("Failed to save tasks", {
          description: "No tasks were saved. Please try again.",
        });
        return;
      }

      if (created_count !== drafts.length) {
        const failedCount = drafts.length - created_count;
        toast.warning("Failed to save tasks", {
          description: `${failedCount} tasks were not saved. ${created_count} tasks saved.`,
        });
        clearDrafts();
        return;
      }

      clearDrafts();
      toast.success(
        created_count === 1
          ? "Task saved successfully"
          : `${created_count} tasks saved successfully`
      );
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        toast.error("Failed to save tasks", {
          description: error.message || "An error occurred while saving tasks.",
        });
      } else {
        toast.error("Failed to save tasks", {
          description:
            "An unexpected error occurred while saving tasks. Please try again.",
        });
      }
    }
  }

  const deleteSelectedTasks = (selectedIndices: Set<number>) => {
    const selectedTasks = drafts.filter((draft, index) =>
      selectedIndices.has(index)
    );
    console.log("Deleting selected tasks:", selectedTasks);
    deleteDrafts(selectedTasks);
  };

  return (
    <div className="mx-auto max-w-2xl w-full space-y-4 flex flex-col items-center justify-center">
      <TaskList
        tasks={drafts}
        title="Task Drafts"
        description={`${drafts.length} ${drafts.length === 1 ? "task draft" : "task drafts"} found`}
        emptyStateTitle="No task drafts"
        emptyStateDescription="Task drafts will appear here after ingestion"
        actionButtons={[
          {
            label: "Save All Tasks",
            onClick: saveAllTasks,
          },
          {
            label: "Delete Selected Tasks",
            onClick: deleteSelectedTasks,
            variant: "destructive",
          },
        ]}
        renderEditDialog={(draft, index) => (
          <DraftEditDialog
            selectedIndices={new Set([index])}
            isSingleEdit={true}
            trigger={
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Pencil className="h-4 w-4" />
              </Button>
            }
          />
        )}
        renderBulkEditDialog={(selectedIndices) => (
          <DraftEditDialog
            selectedIndices={selectedIndices}
            isSingleEdit={false}
            trigger={
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Pencil className="h-4 w-4" />
              </Button>
            }
          />
        )}
      />
    </div>
  );

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
            EditDialog={
              <DraftEditDialog
                selectedIndices={new Set([index])}
                isSingleEdit={true}
                trigger={
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Pencil className="h-4 w-4" />
                  </Button>
                }
              />
            }
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
          onClick={() => deleteSelectedTasks(selectedIndices)}
        >
          Delete Selected Tasks
        </Button>
        <DraftEditDialog
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
