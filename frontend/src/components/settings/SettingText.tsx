"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import type { Setting } from "@/lib/settings-types";

interface SettingTextProps {
  setting: Setting;
  onUpdate: (value: string, label: string | null) => void;
  disabled?: boolean;
}

export function SettingText({ setting, onUpdate, disabled }: SettingTextProps) {
  const [value, setValue] = useState(setting.value);

  const handleBlur = () => {
    if (value !== setting.value) {
      onUpdate(value, setting.label);
    }
  };

  return (
    <Input
      value={value}
      onChange={(e) => {
        setValue(e.target.value);
        onUpdate(e.target.value, setting.label);
      }}
      onBlur={handleBlur}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          handleBlur();
        }
      }}
      disabled={disabled}
      className="w-[280px]"
    />
  );
}
