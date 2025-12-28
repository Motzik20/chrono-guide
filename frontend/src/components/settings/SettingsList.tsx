"use client";

import { useState, useEffect, useCallback } from "react";
import {
  type Setting,
  SettingsResponseSchema,
  type SettingsResponse,
} from "@/lib/settings-types";
import { apiRequest } from "@/lib/chrono-client";
import { SettingRow } from "./SettingRow";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

export function SettingsList() {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response: SettingsResponse = await apiRequest(
          "/settings/",
          SettingsResponseSchema
        );
        setSettings(response.settings);
      } catch (error) {
        console.error("Failed to fetch settings:", error);
        toast.error("Failed to load settings");
      } finally {
        setIsLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const handleSettingUpdated = useCallback((updated: Setting) => {
    setSettings((prev) =>
      prev.map((s) => (s.key === updated.key ? updated : s))
    );
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center justify-between py-4">
            <div className="space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-48" />
            </div>
            <Skeleton className="h-9 w-[280px]" />
          </div>
        ))}
      </div>
    );
  }

  if (settings.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No settings available
      </div>
    );
  }

  return (
    <div>
      {settings.map((setting) => (
        <SettingRow
          key={setting.key}
          setting={setting}
          onSettingUpdated={handleSettingUpdated}
        />
      ))}
    </div>
  );
}
