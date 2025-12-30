"use client";

import { SettingsList } from "@/components/settings/SettingsList";

export default function SettingsPage() {
  return (
    <div className="flex flex-col h-full p-8 items-center">
      <div className="max-w-2xl w-full">
        <h1 className="text-2xl font-semibold tracking-tight mb-2">Settings</h1>
        <p className="text-muted-foreground mb-8">
          Manage your preferences and application settings.
        </p>
        <SettingsList />
      </div>
    </div>
  );
}
