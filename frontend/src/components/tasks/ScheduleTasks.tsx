"use client";

import { useState, useEffect } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TaskCard } from "./TaskCard";
import {
  Task,
  TasksResponseSchema,
  ScheduleResponseSchema,
} from "@/lib/task-types";
import Link from "next/link";
import { apiRequest } from "@/lib/chrono-client";

export default function ScheduleTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(
    new Set()
  );

  useEffect(() => {
    const fetchTasks = async () => {
      const tasks = await apiRequest(
        "/tasks/unscheduled",
        TasksResponseSchema,
        {
          method: "GET",
        }
      );
      return tasks;
    };
    fetchTasks().then((tasks) => {
      setTasks(tasks);
    });
  }, []);

  const scheduleTasks = async () => {
    const selectedTasks = tasks.filter((task, index) =>
      selectedIndices.has(index)
    );
    const response = await apiRequest(
      "/schedule/generate/selected",
      ScheduleResponseSchema,
      {
        method: "POST",
        body: JSON.stringify({
          task_ids: selectedTasks.map((task) => task.id),
        }),
      }
    );
    console.log("Response:", response);
  };

  const allSelected = tasks.length > 0 && selectedIndices.size === tasks.length;
  const someSelected =
    tasks.length > 0 &&
    selectedIndices.size > 0 &&
    selectedIndices.size < tasks.length;

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIndices(new Set(tasks.map((_, index) => index)));
      console.log("Selected all tasks:", selectedIndices);
    } else {
      setSelectedIndices(new Set());
      console.log("Unselected all tasks:", selectedIndices);
    }
  };

  const handleTaskSelect = (index: number, checked: boolean) => {
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

  const deleteSelectedTasks = () => {
    console.log("Deleting selected tasks:", selectedIndices);
    setSelectedIndices(new Set());
  };

  if (tasks.length === 0) {
    return (
      <Card className="mx-auto w-1/2 max-w-2xl">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold tracking-tight">
            Tasks
          </CardTitle>
          <CardDescription>
            Tasks will appear here after saving them under{" "}
            <Link href="/tasks">Tasks</Link>
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
            <p className="text-2xl font-bold tracking-tight">
              Schedulable Tasks
            </p>
            <p className="text-sm text-muted-foreground">Select all</p>
          </CardTitle>
          <CardDescription className="flex justify-between">
            {tasks.length} {tasks.length === 1 ? "task" : "tasks"} ready to be
            scheduled
            <Checkbox
              checked={allSelected}
              onCheckedChange={handleSelectAll}
              className="h-6 w-6 border border-slate-500"
            />
          </CardDescription>
        </CardHeader>
      </Card>
      <div className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto">
        {tasks.map((task, index) => (
          <TaskCard
            key={index}
            index={index}
            task={task}
            isSelected={selectedIndices.has(index)}
            onSelect={handleTaskSelect}
            EditDialog={<></>}
          />
        ))}
      </div>
      <div className="flex justify-end gap-2">
        <Button
          variant="destructive"
          className="flex-1"
          onClick={() => deleteSelectedTasks()}
        >
          Delete Selected Tasks
        </Button>
        <Button className="flex-1" onClick={() => scheduleTasks()}>
          Schedule Selected Tasks
        </Button>
      </div>
    </div>
  );
}
