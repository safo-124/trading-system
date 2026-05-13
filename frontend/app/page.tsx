import { Suspense } from "react";
import Loading from "@/app/loading";
import { ReturnsChart } from "@/components/backtest/returns-chart";
import { PredictionTable } from "@/components/swing/prediction-table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getBacktestSummary,
  getDividendPicks,
  getHealth,
  getSwingLatestPredictions,
  topDividendPicks,
} from "@/lib/api/client";
import { formatDate, formatNumber, formatSignedPercent } from "@/lib/utils";

export default function DashboardPage() {
  return (
    <Suspense fallback={<Loading />}>
      <DashboardContent />
    </Suspense>
  );
}

async function DashboardContent() {
  const [health, dividendPicks, swingPredictions, backtest] = await Promise.all([
    getHealth(),
    getDividendPicks(),
    getSwingLatestPredictions(5),
    getBacktestSummary(),
  ]);
  const bestDividendPicks = topDividendPicks(dividendPicks.picks, 5);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <h1 className="font-semibold text-2xl tracking-tight">Trading System</h1>
          <p className="text-muted-foreground text-sm">
            Dividend safety picks and the cross-sectional swing model.
          </p>
        </div>
        <Badge className="w-fit bg-emerald-500/15 text-emerald-300" variant="secondary">
          API {health.status}
        </Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Dividend Picks" value={formatNumber(dividendPicks.n_picks)} />
        <MetricCard label="Swing Universe" value={formatNumber(swingPredictions.n_stocks)} />
        <MetricCard
          label="Net Sharpe"
          value={formatNumber(backtest.summary.sharpe_net, { maximumFractionDigits: 2 })}
        />
        <MetricCard
          label="Net Total Return"
          tone="positive"
          value={formatSignedPercent(backtest.summary.total_return_net, 1)}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Dividend Screener</CardTitle>
            <CardDescription>
              Latest run from {formatDate(dividendPicks.generated_at ?? null)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3">
              {bestDividendPicks.map((pick) => (
                <div
                  className="grid grid-cols-[1fr_auto_auto] items-center gap-3 rounded-lg border border-border/70 px-3 py-2"
                  key={pick.ticker}
                >
                  <div>
                    <div className="font-semibold">{pick.ticker}</div>
                    <div className="text-muted-foreground text-xs">
                      {pick.consec_increases} yearly increases
                    </div>
                  </div>
                  <div className="text-right font-mono text-emerald-400">
                    {formatNumber(pick.yield, { style: "percent" })}
                  </div>
                  <div className="text-right font-mono">
                    {formatNumber(pick.composite_score, { maximumFractionDigits: 3 })}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Swing Model</CardTitle>
            <CardDescription>
              Latest predictions as of {formatDate(swingPredictions.as_of)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 lg:grid-cols-2">
              <div>
                <div className="mb-2 text-muted-foreground text-xs uppercase tracking-wide">
                  Long
                </div>
                <PredictionTable picks={swingPredictions.long_picks.slice(0, 5)} side="long" />
              </div>
              <div>
                <div className="mb-2 text-muted-foreground text-xs uppercase tracking-wide">
                  Short
                </div>
                <PredictionTable picks={swingPredictions.short_picks.slice(0, 5)} side="short" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Backtest: Last 30 Trading Days</CardTitle>
          <CardDescription>
            Net annual return {formatSignedPercent(backtest.summary.ann_return_net, 2)} across{" "}
            {formatDate(backtest.summary.start_date)} to {formatDate(backtest.summary.end_date)}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ReturnsChart days={backtest.last_30_days} />
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "positive" | "risk";
}) {
  return (
    <Card>
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle
          className={
            tone === "positive"
              ? "font-mono text-2xl text-emerald-400"
              : tone === "risk"
                ? "font-mono text-2xl text-red-400"
                : "font-mono text-2xl"
          }
        >
          {value}
        </CardTitle>
      </CardHeader>
    </Card>
  );
}
