"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Calendar, Clock, Download } from "lucide-react";
import {
  ScheduleItem,
  ScheduleItemsResponseSchema,
} from "@/lib/schedule-types";
import { apiDownloadRequest, apiRequest, ApiError } from "@/lib/chrono-client";
import { useSchedule } from "@/context/schedule-context";
import { toast } from "sonner";
import { formatDateTime, formatDuration } from "@/lib/format-dt";

export default function ScheduleItemsList() {
  const [scheduleItems, setScheduleItems] = useState<ScheduleItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const { refreshTrigger } = useSchedule();

  useEffect(() => {
    const fetchScheduleItems = async () => {
      try {
        setIsLoading(true);
        const items = await apiRequest(
          "/schedule/items?source=task",
          ScheduleItemsResponseSchema,
          { method: "GET" }
        );
        setScheduleItems(items);
      } catch (error) {
        const message =
          error instanceof ApiError
            ? error.message
            : "Failed to load schedule items";
        toast.error(message);
        setScheduleItems([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchScheduleItems();
  }, [refreshTrigger]);

  const handleExport = async () => {
    if (scheduleItems.length === 0) {
      toast.warning("No schedule items to export");
      return;
    }

    setIsExporting(true);
    try {
      await apiDownloadRequest("/schedule/export", {
        method: "GET",
      });
      toast.success("Schedule exported successfully");
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Failed to export schedule";
      toast.error(message);
    } finally {
      setIsExporting(false);
    }
  };

  if (isLoading) {
    return (
      <Card className="mx-auto w-2xl w-full">
        <CardHeader>
          <CardTitle>Schedule</CardTitle>
          <CardDescription>Loading schedule items...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="flex flex-col h-full mx-auto w-full">
      <Card className="flex-shrink-0 mb-4">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Scheduled Tasks</CardTitle>
              <CardDescription>
                {scheduleItems.length}{" "}
                {scheduleItems.length === 1 ? "item" : "items"} scheduled
              </CardDescription>
            </div>
            <Button
              onClick={handleExport}
              variant="outline"
              size="sm"
              disabled={isExporting || scheduleItems.length === 0}
            >
              <Download className="h-4 w-4 mr-2" />
              {isExporting ? "Exporting..." : "Export"}
            </Button>
          </div>
        </CardHeader>
      </Card>

      {scheduleItems.length === 0 ? (
        <Card className="flex-1">
          <CardContent className="flex items-center justify-center h-full">
            <div className="text-center text-muted-foreground">
              <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No scheduled tasks found</p>
              <p className="text-sm mt-2">
                Schedule tasks from the left panel to see them here
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-4">
          {scheduleItems.map((item) => (
            <Card key={item.id}>
              <CardHeader>
                <CardTitle className="text-lg">
                  {item.title || "Untitled Task"}
                </CardTitle>
                {item.description && (
                  <CardDescription className="whitespace-pre-wrap">
                    {item.description}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span>
                    {formatDateTime(item.start_time, item.user_timezone)} -{" "}
                    {formatDateTime(item.end_time, item.user_timezone)}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  <span>
                    Duration: {formatDuration(item.start_time, item.end_time)}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
