import { z } from "zod";

// Value schema for a schedule setting
export const ScheduleSettingValue = z.record(
  z.string(),
  z.array(
    z.object({
      start: z.string(),
      end: z.string(),
    })
  )
);

// Base schema for a single setting from the API
export const SettingBaseSchema = z.object({
  id: z.number().nullable().optional(),
  key: z.string(),
  label: z.string().nullable(),
  description: z.string(),
  option_type: z.string().nullable(),
});

// Schema for a string setting
export const StringSettingSchema = SettingBaseSchema.extend({
  value: z.string(),
  type: z.literal("string"),
});

// Schema for a boolean setting
export const BooleanSettingSchema = SettingBaseSchema.extend({
  value: z.string(),
  type: z.literal("boolean"),
});

// Schema for a schedule setting
export const ScheduleSettingSchema = SettingBaseSchema.extend({
  value: ScheduleSettingValue,
  type: z.literal("schedule"),
});

// Decide which schema to use based on the type
export const SettingSchema = z.discriminatedUnion("type", [
  StringSettingSchema,
  BooleanSettingSchema,
  ScheduleSettingSchema,
]);

export type StringSetting = z.infer<typeof StringSettingSchema>;
export type ScheduleSetting = z.infer<typeof ScheduleSettingSchema>;
export type BooleanSetting = z.infer<typeof BooleanSettingSchema>;
export type Setting = z.infer<typeof SettingSchema>;

// Schema for the settings list response
export const SettingsResponseSchema = z.object({
  settings: z.array(SettingSchema),
});

export type SettingsResponse = z.infer<typeof SettingsResponseSchema>;

// Schema for options (used by both static and dynamic options)
export const OptionSchema = z.object({
  value: z.string(),
  label: z.string(),
});

export type Option = z.infer<typeof OptionSchema>;

export const OptionsResponseSchema = z.array(OptionSchema);

export type OptionsResponse = z.infer<typeof OptionsResponseSchema>;

// Setting update payload
export const SettingUpdateSchema = z.object({
  key: z.string(),
  value: z.any(),
  label: z.string().nullable(),
  type: z.string(),
});

export type SettingUpdate = z.infer<typeof SettingUpdateSchema>;

export type ScheduleSettingValue = z.infer<typeof ScheduleSettingValue>;

// Determines which component to render based on setting metadata
export type SettingInputType =
  | "switch"
  | "select"
  | "combobox"
  | "text"
  | "schedule";

export function getSettingInputType(setting: Setting): SettingInputType {
  if (setting.type === "boolean") {
    return "switch";
  }
  if (setting.type === "string" && setting.option_type === "static") {
    return "select";
  }
  if (setting.type === "string" && setting.option_type === "dynamic") {
    return "combobox";
  }
  if (setting.type === "schedule") {
    return "schedule";
  }
  // Default fallback for extensibility
  return "text";
}
