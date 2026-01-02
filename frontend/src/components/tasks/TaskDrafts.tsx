"use client";

import { z } from "zod";
import { Button } from "@/components/ui/button";
import { useTaskDrafts } from "@/context/task-drafts-context";
import { DraftEditDialog } from "./DraftEditDialog";
import { apiRequest, ApiError } from "@/lib/chrono-client";
import { toast } from "sonner";
import { Pencil } from "lucide-react";
import TaskList from "./TaskList";

const tasksCreateSchema = z.object({
  task_ids: z.array(z.number()),
  created_count: z.number(),
});

export default function TaskDrafts() {
  const { drafts, deleteDrafts, clearDrafts } = useTaskDrafts();

  async function saveAllTasks() {
    try {
      const response = await apiRequest("/tasks/bulk", tasksCreateSchema, {
        method: "POST",
        body: JSON.stringify(drafts),
      });
      const { created_count } = response;

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
}
