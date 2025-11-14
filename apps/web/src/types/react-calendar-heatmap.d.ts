declare module 'react-calendar-heatmap' {
  import { Component } from 'react';

  interface HeatMapValue {
    date: string;
    count: number;
  }

  interface CalendarHeatmapProps {
    startDate?: Date;
    endDate?: Date;
    values: HeatMapValue[];
    classForValue?: (value: HeatMapValue | null) => string;
    titleForValue?: (value: HeatMapValue | null) => string;
    tooltipDataAttrs?: (value: HeatMapValue | null) => Record<string, string>;
    showWeekdayLabels?: boolean;
    showMonthLabels?: boolean;
  }

  export default class CalendarHeatmap extends Component<CalendarHeatmapProps> {}
}

