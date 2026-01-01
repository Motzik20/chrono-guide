"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ChevronDownIcon, X } from "lucide-react";
import { useTaskDrafts } from "@/context/task-drafts-context";
import type { TaskDraft } from "@/lib/task-types";

interface EditDialogProps {
  selectedIndices: Set<number>;
  trigger?: React.ReactNode;
  isSingleEdit?: boolean;
}

export function DraftEditDialog({
  selectedIndices,
  trigger,
  isSingleEdit = false,
}: EditDialogProps) {
  const { drafts, updateDrafts } = useTaskDrafts();
  const [priority, setPriority] = useState<string | undefined>(undefined);
  const [date, setDate] = useState<Date | undefined>(undefined);
  const [time, setTime] = useState<string>("10:30");
  const [datePickerOpen, setDatePickerOpen] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);

  const selectedCount = selectedIndices.size;

  // Initialize form with current values when editing a single draft
  useEffect(() => {
    if (isSingleEdit && selectedCount === 1 && dialogOpen) {
      const index = Array.from(selectedIndices)[0];
      const draft = drafts[index];
      if (draft) {
        setPriority(draft.priority?.toString());
        if (draft.deadline) {
          const deadlineDate = new Date(draft.deadline);
          setDate(deadlineDate);
          const hours = deadlineDate.getHours().toString().padStart(2, "0");
          const minutes = deadlineDate.getMinutes().toString().padStart(2, "0");
          setTime(`${hours}:${minutes}`);
        } else {
          setDate(undefined);
          setTime("10:30");
        }
      }
    } else if (dialogOpen) {
      // Reset for bulk edit
      setPriority(undefined);
      setDate(undefined);
      setTime("10:30");
    }
  }, [dialogOpen, isSingleEdit, selectedCount, selectedIndices, drafts]);

  const priorityLabels: Record<string, string> = {
    "0": "Highest (0)",
    "1": "High (1)",
    "2": "Medium (2)",
    "3": "Low (3)",
    "4": "Lowest (4)",
  };

  const handleSave = () => {
    const updates: Partial<TaskDraft> = {};

    if (priority !== undefined) {
      updates.priority = parseInt(priority, 10);
    }

    if (date) {
      const [hours, minutes] = time.split(":");
      const deadline = new Date(date);
      deadline.setHours(parseInt(hours, 10), parseInt(minutes, 10), 0, 0);
      updates.deadline = deadline.toISOString();
    } else if (isSingleEdit && date === undefined && selectedCount === 1) {
      // For single edit, if date is cleared, set deadline to null
      const index = Array.from(selectedIndices)[0];
      const draft = drafts[index];
      if (draft?.deadline) {
        updates.deadline = null;
      }
    }

    // Only update if there are changes
    if (Object.keys(updates).length > 0) {
      const selectedDrafts = Array.from(selectedIndices).map(
        (index) => drafts[index]
      );
      updateDrafts(selectedDrafts, updates);
    }

    // Reset form and close dialog
    if (!isSingleEdit) {
      setPriority(undefined);
      setDate(undefined);
      setTime("10:30");
    }
    setDialogOpen(false);
  };

  const handleClearDeadline = () => {
    setDate(undefined);
    setTime("10:30");
  };

  const currentYear = new Date().getFullYear();

  return (
    <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
      {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>
            {isSingleEdit ? "Edit Task" : "Bulk Edit Tasks"}
          </DialogTitle>
          <DialogDescription>
            {isSingleEdit
              ? "Update priority and deadline for this task."
              : `Update priority and deadline for ${selectedCount} selected${
                  selectedCount === 1 ? " task" : " tasks"
                }. Leave fields empty to keep current values.`}
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-3">
            <Label htmlFor="priority">Priority *</Label>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  id="priority"
                  className="w-full justify-between"
                >
                  {priority !== undefined
                    ? priorityLabels[priority]
                    : "Keep current"}
                  <ChevronDownIcon className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56">
                <DropdownMenuLabel>Task Priority</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuRadioGroup
                  value={priority}
                  onValueChange={setPriority}
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
              <Label htmlFor="date-picker">Deadline Date</Label>
              <div className="flex gap-2">
                <Popover open={datePickerOpen} onOpenChange={setDatePickerOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      id="date-picker"
                      className="flex-1 justify-between font-normal"
                    >
                      {date
                        ? date.toLocaleDateString()
                        : isSingleEdit
                          ? "Not set"
                          : "Select date"}
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
                      startMonth={new Date(currentYear, 0, 1)}
                      endMonth={new Date(currentYear + 2, 0)}
                      onSelect={(selectedDate) => {
                        setDate(selectedDate || undefined);
                        setDatePickerOpen(false);
                      }}
                    />
                  </PopoverContent>
                </Popover>
                {date && (
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setDate(undefined)}
                    className="shrink-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
            <div className="flex flex-col gap-3 flex-1">
              <Label htmlFor="time-picker">Time</Label>
              <Input
                type="time"
                id="time-picker"
                step="60"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                disabled={!date}
                className="bg-background appearance-none [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none"
              />
            </div>
          </div>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button type="button" onClick={handleSave}>
            Apply Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
