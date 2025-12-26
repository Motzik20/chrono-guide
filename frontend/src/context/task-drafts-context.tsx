"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
} from "react";
import type { TaskDraft } from "@/components/tasks/IngestionInput";

interface TaskDraftsContextType {
  drafts: TaskDraft[];
  addDrafts: (newDrafts: TaskDraft[]) => void;
  updateDrafts: (
    selectedIndices: Set<number>,
    update: Partial<TaskDraft>
  ) => void;
  deleteDrafts: (selectedIndices: Set<number>) => void;
}

const TaskDraftsContext = createContext<TaskDraftsContextType | undefined>(
  undefined
);

export function TaskDraftsProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [drafts, setDrafts] = useState<TaskDraft[]>([]);

  const addDrafts: (newDrafts: TaskDraft[]) => void = useCallback(
    (newDrafts: TaskDraft[]) => {
      setDrafts((prev) => [...prev, ...newDrafts]);
    },
    []
  );

  const updateDrafts: (
    selectedIndices: Set<number>,
    update: Partial<TaskDraft>
  ) => void = useCallback(
    (selectedIndices: Set<number>, update: Partial<TaskDraft>) => {
      setDrafts((prev) => {
        const newDrafts: TaskDraft[] = [...prev];
        selectedIndices.forEach((index) => {
          if (index < 0 || index >= newDrafts.length) {
            return newDrafts;
          }
          newDrafts[index] = { ...newDrafts[index], ...update };
        });
        return newDrafts;
      });
    },
    []
  );

  const deleteDrafts: (selectedIndices: Set<number>) => void = useCallback(
    (selectedIndices: Set<number>) => {
      setDrafts((prev) => {
        const newDrafts: TaskDraft[] = [...prev];
        const sortedIndices = Array.from(selectedIndices).sort((a, b) => b - a);
        sortedIndices.forEach((index) => {
          newDrafts.splice(index, 1);
        });
        return newDrafts;
      });
    },
    []
  );

  return (
    <TaskDraftsContext.Provider
      value={{
        drafts,
        addDrafts,
        updateDrafts,
        deleteDrafts,
      }}
    >
      {children}
    </TaskDraftsContext.Provider>
  );
}

export function useTaskDrafts() {
  const context = useContext(TaskDraftsContext);
  if (context === undefined) {
    throw new Error("useTaskDrafts must be used within a TaskDraftsProvider");
  }
  return context;
}
