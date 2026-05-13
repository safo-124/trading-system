"use client";

import {
  ColorType,
  createChart,
  type IChartApi,
  type LineData,
  LineSeries,
  type Time,
} from "lightweight-charts";
import { useEffect, useMemo, useRef } from "react";
import type { BacktestDayRecord } from "@/lib/api/client";

type ChartPoint = LineData<Time>;

export function ReturnsChart({ days }: { days: BacktestDayRecord[] }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const { grossData, netData } = useMemo(() => buildNavSeries(days), [days]);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const chart = createReturnsChart(containerRef.current);
    const grossSeries = chart.addSeries(LineSeries, {
      color: "#10b981",
      lineWidth: 2,
      priceLineVisible: false,
    });
    const netSeries = chart.addSeries(LineSeries, {
      color: "#60a5fa",
      lineWidth: 2,
      priceLineVisible: false,
    });

    grossSeries.setData(grossData);
    netSeries.setData(netData);
    chart.timeScale().fitContent();

    const resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) {
        return;
      }
      chart.applyOptions({ width: Math.floor(entry.contentRect.width) });
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [grossData, netData]);

  if (days.length === 0) {
    return (
      <div className="flex h-80 items-center justify-center rounded-lg border border-border/70 text-muted-foreground text-sm">
        No backtest days available.
      </div>
    );
  }

  return <div className="h-80 w-full" ref={containerRef} />;
}

function buildNavSeries(days: BacktestDayRecord[]): {
  grossData: ChartPoint[];
  netData: ChartPoint[];
} {
  let grossNav = 1;
  let netNav = 1;

  const grossData: ChartPoint[] = [];
  const netData: ChartPoint[] = [];

  for (const day of days) {
    grossNav *= 1 + day.daily_ret_gross;
    netNav *= 1 + day.daily_ret_net;
    grossData.push({ time: day.timestamp as Time, value: grossNav });
    netData.push({ time: day.timestamp as Time, value: netNav });
  }

  return { grossData, netData };
}

function createReturnsChart(container: HTMLElement): IChartApi {
  return createChart(container, {
    width: container.clientWidth,
    height: 320,
    layout: {
      background: { type: ColorType.Solid, color: "transparent" },
      textColor: "#a1a1aa",
      fontFamily: "var(--font-geist-mono)",
    },
    grid: {
      vertLines: { color: "rgba(255,255,255,0.06)" },
      horzLines: { color: "rgba(255,255,255,0.06)" },
    },
    rightPriceScale: {
      borderColor: "rgba(255,255,255,0.12)",
    },
    timeScale: {
      borderColor: "rgba(255,255,255,0.12)",
      timeVisible: false,
    },
  });
}
