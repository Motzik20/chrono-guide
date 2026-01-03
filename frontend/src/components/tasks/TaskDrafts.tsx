"use client";

import { useEffect } from "react";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { DraftEditDialog } from "./DraftEditDialog";
import { apiRequest, ApiError } from "@/lib/chrono-client";
import { toast } from "sonner";
import { Pencil } from "lucide-react";
import TaskList from "./TaskList";
import { useTaskList } from "@/hooks/useTaskLists";
import { useJobManager } from "@/context/job-context";

const commitResponseSchema = z.object({
  task_ids: z.array(z.number()),
  created_count: z.number(),
});

export default function TaskDrafts() {
  const { tasks: drafts, fetchTasks } = useTaskList("/tasks/drafts");

  async function commitDrafts() {
    if (drafts.length === 0) {
      toast.error("No drafts to commit");
      return;
    }

    const draftIds = drafts
      .filter((draft) => draft.committed_at === null)
      .map((draft) => draft.id);

    if (draftIds.length === 0) {
      toast.info("All drafts are already committed");
      return;
    }

    try {
      const response = await apiRequest(
        "/tasks/drafts/commit",
        commitResponseSchema,
        {
          method: "POST",
          body: JSON.stringify(draftIds),
        }
      );

      toast.success(
        response.created_count === 1
          ? "Task committed successfully"
          : `${response.created_count} tasks committed successfully`
      );
      await fetchTasks();
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        toast.error("Failed to commit drafts", {
          description:
            error.message || "An error occurred while committing drafts.",
        });
      } else {
        toast.error("Failed to commit drafts", {
          description:
            "An unexpected error occurred while committing drafts. Please try again.",
        });
      }
    }
  }

  const deleteSelectedTasks = async (selectedIndices: Set<number>) => {
    const selectedTasks = drafts.filter((draft, index) =>
      selectedIndices.has(index)
    );
    const taskIds = selectedTasks.map((task) => task.id);

    try {
      await apiRequest("/tasks/bulk", z.object({}), {
        method: "DELETE",
        body: JSON.stringify(taskIds),
      });
      toast.success("Drafts deleted successfully");
      await fetchTasks();
    } catch (error) {
      toast.error("Failed to delete drafts");
    }
  };

  return (
    <TaskList
      tasks={drafts}
      title="Task Drafts"
      description={`${drafts.length} ${drafts.length === 1 ? "task draft" : "task drafts"} found`}
      emptyStateTitle="No task drafts"
      emptyStateDescription="Task drafts will appear here after ingestion"
      actionButtons={[
        {
          label: "Commit All Drafts",
          onClick: commitDrafts,
        },
        {
          label: "Delete Selected Tasks",
          onClick: deleteSelectedTasks,
          variant: "destructive",
        },
      ]}
      renderEditDialog={(draft, index) => (
        <DraftEditDialog
          tasks={drafts}
          selectedIndices={new Set([index])}
          isSingleEdit={true}
          onUpdate={fetchTasks}
          trigger={
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <Pencil className="h-4 w-4" />
            </Button>
          }
        />
      )}
      renderBulkEditDialog={(selectedIndices) => (
        <DraftEditDialog
          tasks={drafts}
          selectedIndices={selectedIndices}
          isSingleEdit={false}
          onUpdate={fetchTasks}
          trigger={
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <Pencil className="h-4 w-4" />
            </Button>
          }
        />
      )}
    />
  );
}
