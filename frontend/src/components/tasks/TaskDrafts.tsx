"use client";

import { useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import {
  Clock,
  Lightbulb,
  ChevronDownIcon,
  X,
  ChevronsUpDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { TaskDraft } from "./IngestionInput";

interface TaskDraftsProps {
  drafts: TaskDraft[];
  onDraftUpdate: (index: number, draft: TaskDraft) => void;
}

export default function TaskDrafts({ drafts, onDraftUpdate }: TaskDraftsProps) {
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
          <TaskDraft
            key={index}
            draft={draft}
            onUpdate={(updatedDraft) => onDraftUpdate(index, updatedDraft)}
          />
        ))}
      </div>
      <Button>Save Tasks</Button>
    </div>
  );
}

export function TaskDraft({
  draft,
  onUpdate,
}: {
  draft: TaskDraft;
  onUpdate: (draft: TaskDraft) => void;
}) {
  const [priority, setPriority] = useState<string>(
    draft.priority?.toString() ?? "2"
  );
  const [date, setDate] = useState<Date | undefined>(
    draft.deadline ? new Date(draft.deadline) : undefined
  );
  const [time, setTime] = useState<string>(() => {
    if (draft.deadline) {
      const deadlineDate = new Date(draft.deadline);
      const hours = deadlineDate.getHours().toString().padStart(2, "0");
      const minutes = deadlineDate.getMinutes().toString().padStart(2, "0");
      return `${hours}:${minutes}`;
    }
    return "10:30";
  });
  const [datePickerOpen, setDatePickerOpen] = useState(false);

  const priorityLabels: Record<string, string> = {
    "0": "Highest (0)",
    "1": "High (1)",
    "2": "Medium (2)",
    "3": "Low (3)",
    "4": "Lowest (4)",
  };

  const handlePriorityChange = (value: string) => {
    setPriority(value);
    onUpdate({
      ...draft,
      priority: parseInt(value, 10),
    });
  };

  const handleDateChange = (selectedDate: Date | undefined) => {
    setDate(selectedDate);
    if (selectedDate) {
      const [hours, minutes] = time.split(":");
      const deadline = new Date(selectedDate);
      deadline.setHours(parseInt(hours, 10), parseInt(minutes, 10), 0, 0);
      onUpdate({
        ...draft,
        deadline: deadline.toISOString(),
      });
    } else {
      onUpdate({
        ...draft,
        deadline: null,
      });
    }
    setDatePickerOpen(false);
  };

  const handleTimeChange = (newTime: string) => {
    setTime(newTime);
    if (date) {
      const [hours, minutes] = newTime.split(":");
      const deadline = new Date(date);
      deadline.setHours(parseInt(hours, 10), parseInt(minutes, 10), 0, 0);
      onUpdate({
        ...draft,
        deadline: deadline.toISOString(),
      });
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{draft.title}</CardTitle>
        <CardDescription className="whitespace-pre-wrap">
          {draft.description}
        </CardDescription>
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
            <Label htmlFor={`priority-${draft.title}`}>Priority *</Label>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  id={`priority-${draft.title}`}
                  className="w-full justify-between"
                >
                  {priorityLabels[priority]}
                  <ChevronDownIcon className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56">
                <DropdownMenuLabel>Task Priority</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuRadioGroup
                  value={priority}
                  onValueChange={handlePriorityChange}
                >
                  <DropdownMenuRadioItem value="0">
                    Highest (0)
                  </DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="1">
                    High (1)
                  </DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="2">
                    Medium (2)
                  </DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="3">
                    Low (3)
                  </DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="4">
                    Lowest (4)
                  </DropdownMenuRadioItem>
                </DropdownMenuRadioGroup>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="flex gap-4">
            <div className="flex flex-col gap-3 flex-1">
              <Label htmlFor={`date-picker-${draft.title}`}>
                Deadline Date
              </Label>
              <div className="flex gap-2">
                <Popover open={datePickerOpen} onOpenChange={setDatePickerOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      id={`date-picker-${draft.title}`}
                      className="flex-1 justify-between font-normal"
                    >
                      {date ? date.toLocaleDateString() : "Select date"}
                      <ChevronDownIcon className="h-4 w-4" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent
                    className="w-auto overflow-hidden p-0"
                    align="start"
                  >
                    <Calendar
                      mode="single"
                      selected={date}
                      captionLayout="dropdown"
                      onSelect={handleDateChange}
                    />
                  </PopoverContent>
                </Popover>
                {date && (
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => handleDateChange(undefined)}
                    className="shrink-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
            <div className="flex flex-col gap-3 flex-1">
              <Label htmlFor={`time-picker-${draft.title}`}>Time</Label>
              <Input
                type="time"
                id={`time-picker-${draft.title}`}
                step="60"
                value={time}
                onChange={(e) => handleTimeChange(e.target.value)}
                disabled={!date}
                className="bg-background appearance-none [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none"
              />
            </div>
          </div>
        </div>
        <Collapsible>
          {draft.tips && draft.tips.length > 0 && (
            <div className="space-y-2">
              <CollapsibleTrigger asChild>
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Lightbulb className="h-4 w-4" />
                  <span>Tips</span>
                  <ChevronsUpDown className="h-4 w-4" />
                </div>
              </CollapsibleTrigger>
              <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground ml-6">
                {draft.tips.map((tip, tipIndex) => (
                  <CollapsibleContent key={tipIndex}>
                    <li key={tipIndex}>{tip}</li>
                  </CollapsibleContent>
                ))}
              </ul>
            </div>
          )}
        </Collapsible>
      </CardContent>
    </Card>
  );
}
