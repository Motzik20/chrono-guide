"use client";

import { Switch } from "@/components/ui/switch";
import type { Setting } from "@/lib/settings-types";

interface SettingSwitchProps {
  setting: Setting;
  onUpdate: (value: string) => void;
  disabled?: boolean;
}

export function SettingSwitch({
  setting,
  onUpdate,
  disabled,
}: SettingSwitchProps) {
  const isChecked = setting.value === "true";

  return (
    <Switch
      checked={isChecked}
      onCheckedChange={(checked) => onUpdate(checked ? "true" : "false")}
      disabled={disabled}
    />
  );
}
