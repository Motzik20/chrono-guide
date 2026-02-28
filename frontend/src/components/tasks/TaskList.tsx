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
import { TaskCard } from "./TaskCard";
import { TaskBase } from "@/lib/task-types";

interface TaskListProps {
  tasks: TaskBase[];
  title: string;
  description: string | ((taskCount: number) => string);
  emptyStateTitle: string;
  emptyStateDescription: React.ReactNode;
  actionButtons: Array<{
    label: string;
    onClick: (selectedIndices: Set<number>) => void | Promise<void>;
    variant?:
      | "default"
      | "destructive"
      | "outline"
      | "secondary"
      | "ghost"
      | "link";
    className?: string;
    icon?: React.ReactNode;
  }>;
  renderEditDialog?: (task: TaskBase, index: number) => React.ReactNode;
  renderBulkEditDialog?: (selectedIndices: Set<number>) => React.ReactNode;
}

export default function TaskList({
  tasks,
  title,
  description,
  emptyStateTitle,
  emptyStateDescription,
  actionButtons,
  renderEditDialog,
  renderBulkEditDialog,
}: TaskListProps) {
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(
    new Set()
  );
  const allSelected = tasks.length > 0 && selectedIndices.size === tasks.length;

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIndices(new Set(tasks.map((_, index) => index)));
    } else {
      setSelectedIndices(new Set());
    }
  };

  const handleTaskSelect = (index: number, checked: boolean) => {
    setSelectedIndices((prev) => {
      const newSet = new Set(prev);
      if (checked) {
        newSet.add(index);
      } else {
        newSet.delete(index);
      }
      return newSet;
    });
  };

  const handleButtonClick = async (
    onClick: (selectedIndices: Set<number>) => void | Promise<void>
  ) => {
    await onClick(selectedIndices);
    setSelectedIndices(new Set());
  };

  if (tasks.length === 0) {
    return (
      <Card className="mx-auto w-1/2">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold tracking-tight">
            {emptyStateTitle}
          </CardTitle>
          <CardDescription>{emptyStateDescription}</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="flex flex-col h-full mx-auto w-full">
      <Card className="flex-shrink-0 mb-4">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="flex justify-between">
            <p className="text-2xl font-bold tracking-tight">{title}</p>
            <p className="text-sm text-muted-foreground">Select all</p>
          </CardTitle>
          <CardDescription className="flex justify-between">
            {typeof description === "function"
              ? description(tasks.length)
              : description}
            <Checkbox
              checked={allSelected}
              onCheckedChange={handleSelectAll}
              className="h-6 w-6 border border-slate-500"
            />
          </CardDescription>
        </CardHeader>
      </Card>
      <div className="space-y-4 overflow-y-auto flex-1 min-h-0">
        {tasks.map((task, index) => (
          <TaskCard
            key={index}
            index={index}
            task={task}
            isSelected={selectedIndices.has(index)}
            onSelect={handleTaskSelect}
            EditDialog={
              renderEditDialog ? renderEditDialog(task, index) : undefined
            }
          />
        ))}
      </div>
      {actionButtons.length > 0 && (
        <div className="bg-background border-t pt-2 pb-2 flex justify-end gap-2 flex-shrink-0">
          {actionButtons.map((button, index) => (
            <Button
              key={index}
              variant={button.variant || "default"}
              className={button.className || "flex-1"}
              onClick={() => handleButtonClick(button.onClick)}
            >
              {button.icon}
              {button.label}
            </Button>
          ))}
          {renderBulkEditDialog
            ? renderBulkEditDialog(selectedIndices)
            : undefined}
        </div>
      )}
    </div>
  );
}
