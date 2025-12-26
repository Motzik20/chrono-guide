"use client";

import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Clock, Lightbulb, ChevronsUpDown, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { TaskDraft } from "./IngestionInput";
import { useTaskDrafts } from "@/context/task-drafts-context";
import { EditDialog } from "./EditDialog";

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

  const saveSelectedTasks = () => {};

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
          <TaskDraft
            key={index}
            index={index}
            draft={draft}
            isSelected={selectedIndices.has(index)}
            onSelect={handleDraftSelect}
          />
        ))}
      </div>
      <div className="flex justify-end gap-2">
        <Button className="flex-1" onClick={() => saveSelectedTasks()}>
          Save Selected Tasks
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

export function TaskDraft({
  draft,
  index,
  isSelected,
  onSelect,
}: {
  draft: TaskDraft;
  index: number;
  isSelected: boolean;
  onSelect: (index: number, checked: boolean) => void;
}) {
  const priorityLabels: Record<string, string> = {
    "0": "Highest (0)",
    "1": "High (1)",
    "2": "Medium (2)",
    "3": "Low (3)",
    "4": "Lowest (4)",
  };

  const formatDeadline = () => {
    if (!draft.deadline) return "Not set";
    const deadlineDate = new Date(draft.deadline);
    return deadlineDate.toLocaleString();
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <CardTitle className="text-lg">{draft.title}</CardTitle>
            <CardDescription className="whitespace-pre-wrap mt-1">
              {draft.description}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <EditDialog
              selectedIndices={new Set([index])}
              isSingleEdit={true}
              trigger={
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Pencil className="h-4 w-4" />
                </Button>
              }
            />
            <Checkbox
              checked={isSelected}
              className="h-6 w-6 border border-slate-500"
              onCheckedChange={(checked) => onSelect(index, checked === true)}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-4 w-4" />
          <span>
            {draft.expected_duration_minutes}{" "}
            {draft.expected_duration_minutes === 1 ? "minute" : "minutes"}
          </span>
        </div>

        <div className="space-y-3">
          <div className="flex flex-col gap-2">
            <Label>Priority</Label>
            <div className="text-sm font-medium">
              {priorityLabels[(draft.priority ?? 2).toString()]}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Label>Deadline</Label>
            <div className="text-sm text-muted-foreground">
              {formatDeadline()}
            </div>
          </div>
        </div>
        {draft.tips && draft.tips.length > 0 && (
          <Collapsible>
            <div className="space-y-2">
              <CollapsibleTrigger asChild className="w-20">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Lightbulb className="h-4 w-4" />
                  <span>Tips</span>
                  <ChevronsUpDown className="h-4 w-4" />
                </div>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground ml-6">
                  {draft.tips.map((tip, tipIndex) => (
                    <li key={tipIndex}>{tip}</li>
                  ))}
                </ul>
              </CollapsibleContent>
            </div>
          </Collapsible>
        )}
      </CardContent>
    </Card>
  );
}
