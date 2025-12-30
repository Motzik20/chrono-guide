import { ScheduleSetting, ScheduleSettingValue } from "@/lib/settings-types";
import { useState } from "react";
import { X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useForm, useFieldArray } from "react-hook-form";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

function timeToMinutes(time: string): number {
  if (!time) return 0;
  const parts = time.split(":");
  const hours = Number(parts[0]) || 0;
  const minutes = Number(parts[1]) || 0;
  return hours * 60 + minutes;
}

function formatTimeForInput(time: string): string {
  if (!time) return "";
  return time.slice(0, 5); // Take first 5 characters "HH:MM"
}

function formatTimeForAPI(time: string): string {
  if (!time) return "";
  return time.length === 5 ? `${time}:00` : time;
}

function windowsOverlap(
  window1: { start: string; end: string },
  window2: { start: string; end: string }
): boolean {
  const start1 = timeToMinutes(window1.start);
  const end1 = timeToMinutes(window1.end);
  const start2 = timeToMinutes(window2.start);
  const end2 = timeToMinutes(window2.end);

  return start1 < end2 && end1 > start2;
}

const TimeWindowSchema = z
  .object({
    start: z.string().min(1, "Start time is required"),
    end: z.string().min(1, "End time is required"),
  })
  .refine(
    (data) => {
      const start = timeToMinutes(data.start);
      const end = timeToMinutes(data.end);
      return start < end;
    },
    {
      path: ["end"],
      message: "End time must be after start time",
    }
  );

const DayWindowSchema = z.array(TimeWindowSchema).superRefine((data, ctx) => {
  for (let i = 0; i < data.length; i++) {
    for (let j = i + 1; j < data.length; j++) {
      if (windowsOverlap(data[i], data[j])) {
        ctx.addIssue({
          code: "custom",
          message: `Time window ${i + 1} and ${j + 1} overlap`,
          path: [j], // Attach error to the second window
        });
      }
    }
  }
});

const ScheduleFormSchema = z.object({
  "0": DayWindowSchema,
  "1": DayWindowSchema,
  "2": DayWindowSchema,
  "3": DayWindowSchema,
  "4": DayWindowSchema,
  "5": DayWindowSchema,
  "6": DayWindowSchema,
});

type ScheduleForm = z.infer<typeof ScheduleFormSchema>;

interface SettingScheduleProps {
  setting: ScheduleSetting;
  onUpdate: (
    value: ScheduleSettingValue,
    label: string | null
  ) => Promise<void> | void;
  disabled?: boolean;
}

const DAYS: Readonly<Record<string, string>> = {
  "0": "Mon",
  "1": "Tue",
  "2": "Wed",
  "3": "Thu",
  "4": "Fri",
  "5": "Sat",
  "6": "Sun",
};

export function SettingSchedule({
  setting,
  onUpdate,
  disabled,
}: SettingScheduleProps) {
  const [activeTab, setActiveTab] = useState<string>("0");
  const [open, setOpen] = useState(false);

  // Convert API time format to input format for default values
  const formattedDefaultValues: ScheduleForm = Object.keys(
    setting.value
  ).reduce((acc, day) => {
    acc[day as keyof ScheduleForm] = setting.value[day].map((window) => ({
      start: formatTimeForInput(window.start),
      end: formatTimeForInput(window.end),
    }));
    return acc;
  }, {} as ScheduleForm);

  const form = useForm<ScheduleForm>({
    resolver: zodResolver(ScheduleFormSchema),
    defaultValues: formattedDefaultValues,
    mode: "onChange", // Validate on change
  });

  const handleSave = async (data: ScheduleForm) => {
    // Convert form times (HH:MM) to API format (HH:MM:SS)
    const apiData: ScheduleSettingValue = Object.keys(data).reduce(
      (acc, day) => {
        acc[day] = data[day as keyof ScheduleForm].map((window) => ({
          start: formatTimeForAPI(window.start),
          end: formatTimeForAPI(window.end),
        }));
        return acc;
      },
      {} as ScheduleSettingValue
    );

    await onUpdate(apiData, null);
    setOpen(false);
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="w-[140px]">Edit</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[450px]">
        <DialogHeader>
          <DialogTitle>Edit Avaialbility Windows</DialogTitle>
          <DialogDescription>
            Edit the availability windows for each weekday.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSave)}>
            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v)}>
              <TabsList className="w-full">
                {Object.keys(DAYS).map((day) => (
                  <TabsTrigger
                    key={day}
                    value={day}
                    className={
                      form.formState.errors[day as keyof ScheduleForm]
                        ? "text-destructive border-destructive"
                        : ""
                    }
                  >
                    {DAYS[day]}
                  </TabsTrigger>
                ))}
              </TabsList>
              {/* Render all tabs but hide inactive ones to keep field arrays registered */}
              {Object.keys(DAYS).map((day) => (
                <TabsContent
                  key={day}
                  value={day}
                  forceMount
                  className={activeTab !== day ? "hidden" : undefined}
                >
                  <TimeWindowSelector form={form} activeTab={day} />
                </TabsContent>
              ))}
            </Tabs>
            <DialogFooter>
              <DialogClose asChild>
                <Button type="button" variant="outline">
                  Cancel
                </Button>
              </DialogClose>
              <Button type="submit" disabled={disabled}>
                Apply Changes
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

function TimeWindowSelector({
  form,
  activeTab,
}: {
  form: ReturnType<typeof useForm<ScheduleForm>>;
  activeTab: string;
}) {
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: activeTab as keyof ScheduleForm,
  });

  const dayErrors = form.formState.errors[activeTab as keyof ScheduleForm];

  return (
    <div className="grid gap-4 py-4">
      {fields.length === 0 && (
        <p className="text-muted-foreground text-sm">
          No time windows. Add one below.
        </p>
      )}
      {fields.map((field, index) => (
        <div key={field.id}>
          <TimeWindow
            form={form}
            activeTab={activeTab}
            index={index}
            onRemove={() => remove(index)}
          />
          {/* Display overlap error if it exists at this index - reserve space */}
          <div className="min-h-[20px]">
            {dayErrors?.[index]?.message && (
              <p className="text-destructive text-sm">
                {dayErrors[index]?.message}
              </p>
            )}
          </div>
        </div>
      ))}
      {/* Display root-level overlap error */}
      {dayErrors?.root?.message && (
        <p className="text-destructive text-sm">{dayErrors.root.message}</p>
      )}

      <Button
        type="button"
        variant="outline"
        onClick={() => append({ start: "", end: "" })}
        disabled={fields.length >= 5}
      >
        Add Time Window
      </Button>
    </div>
  );
}

function TimeWindow({
  form,
  activeTab,
  index,
  onRemove,
}: {
  form: ReturnType<typeof useForm<ScheduleForm>>;
  activeTab: string;
  index: number;
  onRemove: () => void;
}) {
  return (
    <div className="flex gap-4 items-start">
      <FormField
        control={form.control}
        name={`${activeTab}.${index}.start` as any}
        render={({ field }) => (
          <FormItem className="flex-1 flex flex-col">
            <FormLabel>Start-Time</FormLabel>
            <FormControl>
              <Input
                type="time"
                step="60"
                {...field}
                className="bg-background appearance-none [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={`${activeTab}.${index}.end` as any}
        render={({ field }) => (
          <FormItem className="flex-1 flex flex-col">
            <FormLabel>End-Time</FormLabel>
            <FormControl>
              <Input
                type="time"
                step="60"
                {...field}
                className="bg-background appearance-none [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <Button
        type="button"
        variant="outline"
        onClick={onRemove}
        aria-label="Remove time window"
        className="mt-5.5"
      >
        <X />
      </Button>
    </div>
  );
}
