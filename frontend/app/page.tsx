import { Suspense } from "react";
import Loading from "@/app/loading";
import { StockIdentity } from "@/components/stocks/stock-identity";
import { MarketBookGrid, MarketMoveView } from "@/components/swing/market-overview";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getAllMarketSnapshots,
  getDividendPicks,
  getHealth,
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
  const [health, dividendPicks, marketSnapshots] = await Promise.all([
    getHealth(),
    getDividendPicks(),
    getAllMarketSnapshots(5),
  ]);
  const bestDividendPicks = topDividendPicks(dividendPicks.picks, 5);
  const totalRanked = marketSnapshots.reduce(
    (sum, snapshot) => sum + snapshot.predictions.n_stocks,
    0,
  );
  const strongestMarket = [...marketSnapshots].sort(
    (left, right) => right.backtest.summary.sharpe_net - left.backtest.summary.sharpe_net,
  )[0];

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <h1 className="font-semibold text-2xl tracking-tight">Global Strategy Desk</h1>
          <p className="text-muted-foreground text-sm">
            Dividend safety plus live cross-market swing books for the US, Europe, and JSE.
          </p>
        </div>
        <Badge className="w-fit bg-emerald-500/15 text-emerald-300" variant="secondary">
          API {health.status}
        </Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Markets Online" value={formatNumber(marketSnapshots.length)} />
        <MetricCard label="Stocks Ranked" value={formatNumber(totalRanked)} />
        <MetricCard label="Dividend Picks" value={formatNumber(dividendPicks.n_picks)} />
        <MetricCard
          label="Best Net Sharpe"
          value={`${strongestMarket.market.label} ${formatNumber(strongestMarket.backtest.summary.sharpe_net, { maximumFractionDigits: 2 })}`}
        />
      </div>

      <section className="space-y-3">
        <div>
          <h2 className="font-semibold text-lg">Move View</h2>
          <p className="text-muted-foreground text-sm">
            Top long versus top short in each market, with model spread and live benchmark context.
          </p>
        </div>
        <MarketMoveView snapshots={marketSnapshots} />
      </section>

      <section className="space-y-3">
        <div>
          <h2 className="font-semibold text-lg">Market Books</h2>
          <p className="text-muted-foreground text-sm">
            Company names and logos are shown next to the latest historical picks from each region.
          </p>
        </div>
        <MarketBookGrid snapshots={marketSnapshots} />
      </section>

      <Card>
        <CardHeader>
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
            <div>
              <CardTitle>Dividend Quality Picks</CardTitle>
              <CardDescription>
                Latest run from {formatDate(dividendPicks.generated_at ?? null)}
              </CardDescription>
            </div>
            <Badge variant="secondary">{dividendPicks.n_picks} names</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 lg:grid-cols-5">
            {bestDividendPicks.map((pick) => (
              <div className="rounded-lg border border-border/70 px-3 py-3" key={pick.ticker}>
                <StockIdentity symbol={pick.ticker} />
                <div className="mt-3 grid grid-cols-2 gap-2 border-border/70 border-t pt-3 text-sm">
                  <Metric label="Yield" value={formatNumber(pick.yield, { style: "percent" })} />
                  <Metric
                    label="Score"
                    value={formatNumber(pick.composite_score, { maximumFractionDigits: 3 })}
                  />
                  <Metric
                    label="Safety"
                    value={formatNumber(pick.safety_score, { maximumFractionDigits: 2 })}
                  />
                  <Metric label="Growth" value={formatSignedPercent(pick.div_cagr_5y, 1)} />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="font-mono text-2xl">{value}</CardTitle>
      </CardHeader>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-muted-foreground text-xs">{label}</div>
      <div className="font-mono text-sm">{value}</div>
    </div>
  );
}
