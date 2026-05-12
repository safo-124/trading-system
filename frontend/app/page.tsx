import { Suspense } from "react";
import Loading from "@/app/loading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getLatestPredictions, getStocks } from "@/lib/api/client";
import { formatDate, formatNumber } from "@/lib/utils";

export default function DashboardPage() {
  return (
    <Suspense fallback={<Loading />}>
      <DashboardContent />
    </Suspense>
  );
}

async function DashboardContent() {
  const [stocks, latestPredictions] = await Promise.all([getStocks(), getLatestPredictions()]);
  const topPicks = latestPredictions.predictions.slice(0, 3);
  const lastRun = topPicks[0]?.predicted_at ?? null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-semibold text-2xl tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground text-sm">Current dividend safety universe.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardDescription>Stocks Tracked</CardDescription>
            <CardTitle className="font-mono text-3xl">{stocks.stocks.length}</CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardDescription>Last Pipeline Run</CardDescription>
            <CardTitle className="font-mono text-xl">{formatDate(lastRun)}</CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardDescription>Top 3 Picks</CardDescription>
            <CardTitle className="font-mono text-xl">{topPicks.length}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Ranked Picks</CardTitle>
          <CardDescription>Latest model output from the persisted prediction run.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-3">
            {topPicks.map((pick) => (
              <div className="rounded-lg border border-border/70 p-4" key={pick.ticker}>
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div>
                    <div className="font-semibold text-lg">{pick.ticker}</div>
                    <div className="font-mono text-muted-foreground text-xs">rank {pick.rank}</div>
                  </div>
                  <Badge variant={pick.recommendation === "BUY" ? "default" : "secondary"}>
                    {pick.recommendation}
                  </Badge>
                </div>
                <div className="grid gap-2 font-mono text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">score</span>
                    <span>{formatNumber(pick.composite_score)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">cut risk</span>
                    <span>{formatNumber(pick.cut_probability, { style: "percent" })}</span>
                  </div>
                </div>
              </div>
            ))}

            {topPicks.length === 0 ? (
              <div className="rounded-lg border border-border/70 p-4 text-muted-foreground text-sm md:col-span-3">
                No pipeline results yet.
              </div>
            ) : null}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
