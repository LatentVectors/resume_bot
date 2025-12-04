"use client";

import { useMemo } from "react";
import CalendarHeatmap from "react-calendar-heatmap";
import type { Job } from "@resume/database/types";

interface ActivityHeatMapProps {
  jobs: Job[];
}

interface HeatMapValue {
  date: string;
  count: number;
}

export function ActivityHeatMap({ jobs }: ActivityHeatMapProps) {
  // Filter jobs with applied_at date
  const appliedJobs = useMemo(
    () => jobs.filter((job) => job.applied_at),
    [jobs]
  );

  // Group jobs by date (YYYY-MM-DD format)
  const dateCounts = useMemo(() => {
    const counts: Record<string, number> = {};

    appliedJobs.forEach((job) => {
      if (job.applied_at) {
        // Extract date part (YYYY-MM-DD) from ISO datetime string
        const date = job.applied_at.split("T")[0];
        counts[date] = (counts[date] || 0) + 1;
      }
    });

    return counts;
  }, [appliedJobs]);

  // Generate data for the last 52 weeks
  const heatMapData = useMemo(() => {
    const data: HeatMapValue[] = [];
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - 52 * 7); // 52 weeks ago

    // Generate all dates in the range
    for (let d = new Date(startDate); d <= today; d.setDate(d.getDate() + 1)) {
      const dateStr = d.toISOString().split("T")[0];
      data.push({
        date: dateStr,
        count: dateCounts[dateStr] || 0,
      });
    }

    return data;
  }, [dateCounts]);

  // Get color class based on count
  const getClassForValue = (value: HeatMapValue | null) => {
    if (!value || value.count === 0) {
      return "color-empty";
    }
    if (value.count >= 10) {
      return "color-scale-5";
    }
    if (value.count >= 6) {
      return "color-scale-4";
    }
    if (value.count >= 3) {
      return "color-scale-3";
    }
    if (value.count >= 1) {
      return "color-scale-2";
    }
    return "color-scale-1";
  };

  // Format title attribute for each square
  const titleForValue = (value: HeatMapValue | null): string => {
    if (!value || value.count === 0) {
      if (value?.date) {
        const date = new Date(value.date);
        const formattedDate = date.toLocaleDateString(undefined, {
          month: "long",
          day: "numeric",
          year: "numeric",
        });
        return `${formattedDate} - No applications`;
      }
      return "No applications";
    }
    const date = new Date(value.date);
    const formattedDate = date.toLocaleDateString(undefined, {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
    return `${formattedDate} - ${value.count} ${value.count === 1 ? "application" : "applications"}`;
  };

  // Format tooltip data attributes
  const getTooltipDataAttrs = (value: HeatMapValue | null) => {
    if (!value || value.count === 0) {
      if (value?.date) {
        const date = new Date(value.date);
        const formattedDate = date.toLocaleDateString(undefined, {
          month: "long",
          day: "numeric",
          year: "numeric",
        });
        return {
          "data-tip": `${formattedDate} - No applications`,
        };
      }
      return {
        "data-tip": "No applications",
      };
    }
    const date = new Date(value.date);
    const formattedDate = date.toLocaleDateString(undefined, {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
    return {
      "data-tip": `${formattedDate} - ${value.count} ${value.count === 1 ? "application" : "applications"}`,
    };
  };

  // Calculate start date (52 weeks ago)
  const startDate = useMemo(() => {
    const date = new Date();
    date.setDate(date.getDate() - 52 * 7);
    return date;
  }, []);

  const endDate = new Date();

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Application Activity</h3>
        <p className="text-sm text-muted-foreground">
          Job applications over the past 52 weeks
        </p>
      </div>

      <div className="overflow-x-auto">
        <CalendarHeatmap
          startDate={startDate}
          endDate={endDate}
          values={heatMapData}
          classForValue={getClassForValue}
          titleForValue={titleForValue}
          tooltipDataAttrs={getTooltipDataAttrs}
          showWeekdayLabels
          showMonthLabels
        />
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <span>Less</span>
        <div className="flex gap-1">
          <div className="h-3 w-3 rounded bg-gray-200" />
          <div className="h-3 w-3 rounded bg-green-200" />
          <div className="h-3 w-3 rounded bg-green-400" />
          <div className="h-3 w-3 rounded bg-green-600" />
          <div className="h-3 w-3 rounded bg-green-800" />
        </div>
        <span>More</span>
      </div>
    </div>
  );
}

