"use client";

import { useState, useCallback } from "react";
import {
  type Setting,
  type Option,
  getSettingInputType,
  OptionsResponseSchema,
  SettingSchema,
} from "@/lib/settings-types";
import { apiRequest } from "@/lib/chrono-client";
import { SettingSwitch } from "./SettingSwitch";
import { SettingSelect } from "./SettingSelect";
import { SettingCombobox } from "./SettingCombobox";
import { SettingText } from "./SettingText";
import { toast } from "sonner";

interface SettingRowProps {
  setting: Setting;
  onSettingUpdated: (updated: Setting) => void;
}

export function SettingRow({ setting, onSettingUpdated }: SettingRowProps) {
  const [options, setOptions] = useState<Option[]>([]);
  const [isLoadingOptions, setIsLoadingOptions] = useState(false);
  const [optionsLoaded, setOptionsLoaded] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const inputType = getSettingInputType(setting);

  // Lazy load options when needed
  const loadOptions = useCallback(async () => {
    if (optionsLoaded || isLoadingOptions) return;
    if (inputType !== "select" && inputType !== "combobox") return;

    setIsLoadingOptions(true);
    try {
      const response = await apiRequest(
        `/settings/options/${setting.key}`,
        OptionsResponseSchema
      );
      setOptions(response);
      setOptionsLoaded(true);
    } catch (error) {
      console.error("Failed to load options:", error);
      toast.error("Failed to load options");
    } finally {
      setIsLoadingOptions(false);
    }
  }, [setting.key, inputType, optionsLoaded, isLoadingOptions]);

  // Update setting value
  const handleUpdate = useCallback(
    async (value: string, label: string | null) => {
      setIsUpdating(true);
      try {
        const updated = await apiRequest(`/settings/`, SettingSchema, {
          method: "PATCH",
          body: JSON.stringify({ key: setting.key, value, label }),
        });
        onSettingUpdated(updated);
        toast.success("Setting updated");
      } catch (error) {
        console.error("Failed to update setting:", error);
        toast.error("Failed to update setting");
      } finally {
        setIsUpdating(false);
      }
    },
    [setting.key, onSettingUpdated]
  );

  // Format key to a human-readable label
  const formatLabel = (key: string) => {
    return key
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const renderInput = () => {
    switch (inputType) {
      case "switch":
        return (
          <SettingSwitch
            setting={setting}
            onUpdate={handleUpdate}
            disabled={isUpdating}
          />
        );
      case "select":
        return (
          <div onFocus={loadOptions} onMouseEnter={loadOptions}>
            <SettingSelect
              setting={setting}
              options={options}
              onUpdate={handleUpdate}
              disabled={isUpdating}
            />
          </div>
        );
      case "combobox":
        return (
          <div onFocus={loadOptions} onMouseEnter={loadOptions}>
            <SettingCombobox
              setting={setting}
              options={options}
              onUpdate={handleUpdate}
              disabled={isUpdating}
              isLoading={isLoadingOptions}
            />
          </div>
        );
      case "text":
      default:
        return (
          <SettingText
            setting={setting}
            onUpdate={handleUpdate}
            disabled={isUpdating}
          />
        );
    }
  };

  return (
    <div className="flex items-center justify-between py-4 border-b border-border last:border-b-0">
      <div className="flex flex-col gap-1">
        <span className="font-medium text-sm">{formatLabel(setting.key)}</span>
        <span className="text-xs text-muted-foreground">
          {setting.description}
        </span>
      </div>
      <div className="flex items-center">{renderInput()}</div>
    </div>
  );
}
