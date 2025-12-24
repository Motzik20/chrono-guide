"use client";

import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Clock, Lightbulb } from "lucide-react";
import type { TaskDraft } from "./IngestionInput";

interface TaskDraftsProps {
  drafts: TaskDraft[];
}

export default function TaskDrafts({ drafts }: TaskDraftsProps) {
  if (drafts.length === 0) {
    return (
      <Card className="mx-auto w-full max-w-2xl">
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
          <CardTitle className="text-2xl font-bold tracking-tight">
            Task Drafts
          </CardTitle>
          <CardDescription>
            {drafts.length} {drafts.length === 1 ? "draft" : "drafts"} found
          </CardDescription>
        </CardHeader>
      </Card>
      <div className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto">
        {drafts.map((draft, index) => (
          <TaskDraft key={index} draft={draft} />
        ))}
      </div>
    </div>
  );
}

export function TaskDraft({ draft }: { draft: TaskDraft }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{draft.title}</CardTitle>
        <CardDescription className="whitespace-pre-wrap">
          {draft.description}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-4 w-4" />
          <span>
            {draft.expected_duration_minutes}{" "}
            {draft.expected_duration_minutes === 1 ? "minute" : "minutes"}
          </span>
        </div>
        {draft.tips && draft.tips.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Lightbulb className="h-4 w-4" />
              <span>Tips</span>
            </div>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground ml-6">
              {draft.tips.map((tip, tipIndex) => (
                <li key={tipIndex}>{tip}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
