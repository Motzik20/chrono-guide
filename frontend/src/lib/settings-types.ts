import { z } from "zod";

// Schema for a single setting from the API
export const SettingSchema = z.object({
  id: z.number(),
  key: z.string(),
  value: z.string(),
  type: z.string(),
  description: z.string(),
  option_type: z.string().nullable(),
});

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
  value: z.string(),
});

export type SettingUpdate = z.infer<typeof SettingUpdateSchema>;

// Determines which component to render based on setting metadata
export type SettingInputType = "switch" | "select" | "combobox" | "text";

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
  // Default fallback for extensibility
  return "text";
}
