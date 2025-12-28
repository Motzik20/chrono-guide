"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Setting, Option } from "@/lib/settings-types";

interface SettingSelectProps {
  setting: Setting;
  options: Option[];
  onUpdate: (value: string) => void;
  disabled?: boolean;
}

export function SettingSelect({
  setting,
  options,
  onUpdate,
  disabled,
}: SettingSelectProps) {
  const selectedOption = options.find((opt) => opt.value === setting.value);
  const displayValue = selectedOption?.label ?? setting.value;

  return (
    <Select value={setting.value} onValueChange={onUpdate} disabled={disabled}>
      <SelectTrigger className="w-[280px]">
        <span>{displayValue}</span>
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
