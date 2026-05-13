"use client";

import { useQuery } from "@tanstack/react-query";

import {
  type BacktestSummaryResponse,
  type DividendPicksResponse,
  getBacktestSummary,
  getDividendPicks,
  getSwingLatestPredictions,
  type SwingPredictionsResponse,
} from "@/lib/api/client";

export const queryKeys = {
  dividendPicks: ["dividend", "picks"] as const,
  swingLatestPredictions: (nPerSide: number) => ["swing", "predictions", nPerSide] as const,
  backtestSummary: ["swing", "backtest"] as const,
};

export function useDividendPicksQuery(initialData?: DividendPicksResponse) {
  return useQuery({
    queryKey: queryKeys.dividendPicks,
    queryFn: getDividendPicks,
    initialData,
  });
}

export function useSwingLatestPredictionsQuery(
  nPerSide: number,
  initialData?: SwingPredictionsResponse,
) {
  return useQuery({
    queryKey: queryKeys.swingLatestPredictions(nPerSide),
    queryFn: () => getSwingLatestPredictions(nPerSide),
    initialData,
  });
}

export function useBacktestSummaryQuery(initialData?: BacktestSummaryResponse) {
  return useQuery({
    queryKey: queryKeys.backtestSummary,
    queryFn: getBacktestSummary,
    initialData,
  });
}
