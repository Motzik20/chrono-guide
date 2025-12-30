"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { StringSetting, Option } from "@/lib/settings-types";

interface SettingSelectProps {
  setting: StringSetting;
  options: Option[];
  onUpdate: (value: string, label: string | null) => void;
  disabled?: boolean;
}

export function SettingSelect({
  setting,
  options,
  onUpdate,
  disabled,
}: SettingSelectProps) {
  const displayValue = setting.label || setting.value;
  const handleValueChange = (value: string) => {
    const selectedOption = options.find((opt) => opt.value === value);
    const newLabel = selectedOption ? selectedOption.label : null;
    onUpdate(value, newLabel);
  };
  return (
    <Select
      value={setting.value}
      onValueChange={handleValueChange}
      disabled={disabled}
    >
      <SelectTrigger className="w-[280px]">
        <SelectValue placeholder="Select an option">{displayValue}</SelectValue>
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
