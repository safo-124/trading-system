"use client";

import {
  ColorType,
  createChart,
  type HistogramData,
  HistogramSeries,
  type IChartApi,
  type Time,
} from "lightweight-charts";
import { useEffect, useRef } from "react";
import { toNumber } from "@/lib/utils";

type DividendPayment = {
  ex_date: string;
  amount: number | string;
};

export function DividendChart({ dividends }: { dividends: DividendPayment[] }) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const chart = createDividendChart(containerRef.current);
    const series = chart.addSeries(HistogramSeries, {
      color: "#10b981",
      priceFormat: {
        type: "price",
        precision: 2,
        minMove: 0.01,
      },
    });
    const data: HistogramData<Time>[] = dividends
      .map((dividend) => ({
        time: dividend.ex_date as Time,
        value: toNumber(dividend.amount) ?? 0,
        color: "#10b981",
      }))
      .sort((left, right) => String(left.time).localeCompare(String(right.time)));

    series.setData(data);
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
  }, [dividends]);

  return <div className="h-80 w-full" ref={containerRef} />;
}

function createDividendChart(container: HTMLElement): IChartApi {
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
