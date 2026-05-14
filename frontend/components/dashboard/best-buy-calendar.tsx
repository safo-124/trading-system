"use client";

import { CalendarDays, Loader2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { StockIdentity } from "@/components/stocks/stock-identity";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { BestPickByDateResponse } from "@/lib/api/client";
import { formatDate, formatNumber, formatSignedPercent } from "@/lib/utils";
import type { MarketSnapshot } from "../swing/market-overview";

export function BestBuyCalendar({ snapshots }: { snapshots: MarketSnapshot[] }) {
  const defaultDate = useMemo(() => latestSnapshotDate(snapshots), [snapshots]);
  const [selectedDate, setSelectedDate] = useState(defaultDate);
  const [result, setResult] = useState<BestPickByDateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSelectedDate(defaultDate);
  }, [defaultDate]);

  useEffect(() => {
    let cancelled = false;

    async function loadBestPick() {
      if (!selectedDate) return;
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/trading/best-by-date?date=${selectedDate}`);
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.detail ?? `Date lookup failed with status ${response.status}`);
        }
        if (!cancelled) setResult(payload);
      } catch (dateError) {
        if (!cancelled) {
          setError(dateError instanceof Error ? dateError.message : "Date lookup failed");
          setResult(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadBestPick();
    return () => {
      cancelled = true;
    };
  }, [selectedDate]);

  return (
    <Card className="border-sky-500/20 bg-sky-500/5">
      <CardHeader>
        <div className="flex flex-col justify-between gap-3 lg:flex-row lg:items-start">
          <div>
            <CardTitle className="flex items-center gap-2">
              <CalendarDays className="size-5 text-sky-300" />
              Best Buy By Date
            </CardTitle>
            <CardDescription>
              Pick a date. The system uses the latest trading book on or before that date and
              selects the highest predicted long across US, Europe, and JSE.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <input
              className="h-9 rounded-lg border border-input bg-background px-3 text-sm outline-none transition focus:border-primary focus:ring-3 focus:ring-primary/20"
              max={defaultDate}
              onChange={(event) => setSelectedDate(event.target.value)}
              type="date"
              value={selectedDate}
            />
            {loading ? <Loader2 className="size-4 animate-spin text-sky-300" /> : null}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-rose-200 text-sm">
            {error}
          </div>
        ) : null}

        {result?.global_best ? (
          <div className="grid gap-4 xl:grid-cols-[1fr_1.2fr]">
            <div className="rounded-lg border border-sky-500/25 bg-background/70 p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <Badge className="bg-sky-500/15 text-sky-200" variant="secondary">
                  Global best buy
                </Badge>
                <Badge variant="secondary">{formatDate(result.global_best.timestamp)}</Badge>
              </div>
              <StockIdentity logoClassName="size-12" symbol={result.global_best.symbol} />
              <div className="mt-4 grid grid-cols-3 gap-2">
                <MiniMetric label="Market" value={result.global_best.market_label} />
                <MiniMetric
                  label="Prediction"
                  value={formatNumber(result.global_best.pred, { maximumFractionDigits: 4 })}
                />
                <MiniMetric
                  label="Realized 5D"
                  value={formatSignedPercent(result.global_best.fwd_ret_5d)}
                />
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-3">
              {result.market_picks.map((pick) => (
                <div
                  className="rounded-lg border border-border/70 bg-background/60 p-3"
                  key={`${pick.market_key}-${pick.timestamp}`}
                >
                  <div className="mb-3 flex items-center justify-between gap-2">
                    <Badge variant="secondary">{pick.market_label}</Badge>
                    <div className="font-mono text-xs">
                      {formatNumber(pick.pred, { maximumFractionDigits: 4 })}
                    </div>
                  </div>
                  <StockIdentity dense symbol={pick.symbol} />
                  <div className="mt-3 border-border/60 border-t pt-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">{pick.benchmark}</span>
                      <span className="font-mono">{formatSignedPercent(pick.fwd_ret_5d)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : !loading ? (
          <div className="rounded-lg border border-dashed border-border px-3 py-6 text-center text-muted-foreground text-sm">
            Pick a date with available prediction history.
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg bg-secondary/35 px-2 py-2">
      <div className="truncate text-muted-foreground text-xs">{label}</div>
      <div className="truncate font-mono text-sm">{value}</div>
    </div>
  );
}

function latestSnapshotDate(snapshots: MarketSnapshot[]): string {
  const latest = snapshots
    .map((snapshot) => snapshot.predictions.as_of)
    .filter(Boolean)
    .sort()
    .at(-1);
  return latest ?? new Date().toISOString().slice(0, 10);
}
