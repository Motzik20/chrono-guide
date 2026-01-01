import { z } from "zod";

export const ScheduleItemSchema = z.object({
  id: z.number(),
  user_id: z.number(),
  task_id: z.number().nullable().optional(),
  start_time: z.string(),
  end_time: z.string(),
  title: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  source: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type ScheduleItem = z.infer<typeof ScheduleItemSchema>;

export const ScheduleItemsResponseSchema = z.array(ScheduleItemSchema);
