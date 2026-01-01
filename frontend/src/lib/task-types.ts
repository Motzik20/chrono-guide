import { z } from "zod";

export const TaskBaseSchema = z.object({
  title: z.string(),
  description: z.string(),
  expected_duration_minutes: z.number(),
  tips: z.array(z.string()),
  priority: z.number().nullable().optional(),
  deadline: z.string().nullable().optional(),
});

export type TaskDraft = z.infer<typeof TaskBaseSchema>;
export type TaskBase = z.infer<typeof TaskBaseSchema>;

export const TaskResponseSchema = TaskBaseSchema.extend({
  id: z.number(),
  user_id: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
  scheduled_at: z.string().nullable().optional(),
  completed_at: z.string().nullable().optional(),
});

export type Task = z.infer<typeof TaskResponseSchema>;

export const TasksResponseSchema = z.array(TaskResponseSchema);

export const ScheduleBlockSchema = z.object({
  task_id: z.number(),
  start_time: z.string(),
  end_time: z.string(),
  source: z.string(),
  title: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
});

export const SchedulableTaskSchema = z.object({
  id: z.number(),
  title: z.string(),
  description: z.string().nullable().optional(),
  expected_duration_minutes: z.number(),
  deadline: z.string().nullable().optional(),
  priority: z.number(),
});

export type SchedulableTask = z.infer<typeof SchedulableTaskSchema>;

export type ScheduleBlock = z.infer<typeof ScheduleBlockSchema>;

export const ScheduleResponseSchema = z.object({
  schedule_blocks: z.array(ScheduleBlockSchema),
  warnings: z.array(SchedulableTaskSchema),
});

export type ScheduleResponse = z.infer<typeof ScheduleResponseSchema>;

export const DeleteTasksRequestSchema = z.object({
  task_ids: z.array(z.number()),
});

export type DeleteTasksRequest = z.infer<typeof DeleteTasksRequestSchema>;
