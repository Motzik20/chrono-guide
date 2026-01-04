import { TaskBase } from "@/lib/task-types";

import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Clock, Flag, Calendar } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Lightbulb } from "lucide-react";
import { ChevronsUpDown } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { formatDateTime } from "@/lib/format-dt";

export function TaskCard<T extends TaskBase>({
  task,
  index,
  isSelected,
  onSelect,
  EditDialog,
}: {
  task: T;
  index: number;
  isSelected: boolean;
  onSelect: (index: number, checked: boolean) => void;
  EditDialog?: React.ReactNode;
}) {
  const priorityLabels: Record<string, string> = {
    "0": "Highest (0)",
    "1": "High (1)",
    "2": "Medium (2)",
    "3": "Low (3)",
    "4": "Lowest (4)",
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <CardTitle className="text-lg">{task.title}</CardTitle>
            <CardDescription className="whitespace-pre-wrap mt-1">
              {task.description}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {EditDialog}
            <Checkbox
              checked={isSelected}
              className="h-6 w-6 border border-slate-500"
              onCheckedChange={(checked) => onSelect(index, checked === true)}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-col gap-2">
          <Label className="text-md">
            <Clock className="h-4 w-4" /> Estimated Duration
          </Label>
          <div className="flex items-center gap-2 text-muted-foreground">
            <span>
              {task.expected_duration_minutes}{" "}
              {task.expected_duration_minutes === 1 ? "minute" : "minutes"}
            </span>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex flex-col gap-2">
            <Label className="text-md">
              <Flag className="h-4 w-4" /> Priority
            </Label>
            <div className="text-muted-foreground">
              <span>{priorityLabels[(task.priority ?? 2).toString()]}</span>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Label className="text-md">
              <Calendar className="h-4 w-4" /> Deadline
            </Label>
            <div className="text-muted-foreground">
              {task.deadline
                ? formatDateTime(task.deadline, task.user_timezone)
                : "Not set"}
            </div>
          </div>
        </div>
        {task.tips && task.tips.length > 0 && (
          <Collapsible>
            <div className="space-y-2">
              <CollapsibleTrigger asChild className="w-20">
                <div className="flex items-center gap-2 font-medium">
                  <Lightbulb className="h-4 w-4" />
                  <span>Tips</span>
                  <ChevronsUpDown className="h-4 w-4" />
                </div>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground ml-6">
                  {task.tips.map((tip, tipIndex) => (
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
