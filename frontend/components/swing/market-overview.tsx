import { ArrowDownRight, ArrowUpRight, Gauge, MoveRight } from "lucide-react";
import { StockIdentity } from "@/components/stocks/stock-identity";
import { PredictionTable } from "@/components/swing/prediction-table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { BacktestSummary, MarketInfo, SwingPredictionsResponse } from "@/lib/api/client";
import { formatDate, formatNumber, formatSignedPercent } from "@/lib/utils";

export type MarketSnapshot = {
  market: MarketInfo;
  predictions: SwingPredictionsResponse;
  backtest: {
    summary: BacktestSummary;
  };
};

const toneClass = {
  long: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/20",
  short: "bg-rose-500/15 text-rose-300 ring-rose-500/20",
};

export function MarketMoveView({ snapshots }: { snapshots: MarketSnapshot[] }) {
  return (
    <div className="grid gap-4 xl:grid-cols-3">
      {snapshots.map((snapshot) => {
        const longPick = snapshot.predictions.long_picks[0];
        const shortPick = snapshot.predictions.short_picks[0];
        const spread = longPick && shortPick ? longPick.pred - shortPick.pred : null;

        return (
          <Card key={snapshot.market.key}>
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <CardTitle>{snapshot.market.label}</CardTitle>
                  <CardDescription>
                    {snapshot.market.region} · as of {formatDate(snapshot.predictions.as_of)}
                  </CardDescription>
                </div>
                <Badge variant="secondary">{snapshot.market.benchmark}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] sm:items-center">
                {longPick ? <MoveCard pick={longPick} side="long" /> : null}
                <div className="hidden justify-center text-muted-foreground sm:flex">
                  <MoveRight className="size-5" />
                </div>
                {shortPick ? <MoveCard pick={shortPick} side="short" /> : null}
              </div>

              <div className="grid grid-cols-3 gap-2 border-border/70 border-t pt-3 text-sm">
                <Metric label="Spread" value={formatNumber(spread, { maximumFractionDigits: 4 })} />
                <Metric
                  label="Net return"
                  value={formatSignedPercent(snapshot.backtest.summary.ann_return_net)}
                />
                <Metric
                  label="Sharpe"
                  value={formatNumber(snapshot.backtest.summary.sharpe_net, {
                    maximumFractionDigits: 2,
                  })}
                />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

export function MarketBookGrid({ snapshots }: { snapshots: MarketSnapshot[] }) {
  return (
    <div className="grid gap-4 xl:grid-cols-3">
      {snapshots.map((snapshot) => (
        <Card key={snapshot.market.key}>
          <CardHeader>
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle>{snapshot.market.label} Book</CardTitle>
                <CardDescription>
                  {formatNumber(snapshot.predictions.n_stocks)} stocks ranked ·{" "}
                  {formatDate(snapshot.predictions.as_of)}
                </CardDescription>
              </div>
              <Badge className="bg-primary/15 text-primary" variant="secondary">
                {snapshot.market.region}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <div className="mb-2 flex items-center gap-2 text-emerald-300 text-xs uppercase tracking-wide">
                <ArrowUpRight className="size-3.5" />
                Long candidates
              </div>
              <PredictionTable picks={snapshot.predictions.long_picks.slice(0, 5)} side="long" />
            </div>
            <div>
              <div className="mb-2 flex items-center gap-2 text-rose-300 text-xs uppercase tracking-wide">
                <ArrowDownRight className="size-3.5" />
                Short candidates
              </div>
              <PredictionTable picks={snapshot.predictions.short_picks.slice(0, 5)} side="short" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function MoveCard({
  pick,
  side,
}: {
  pick: SwingPredictionsResponse["long_picks"][number];
  side: "long" | "short";
}) {
  return (
    <div className={`rounded-lg px-3 py-3 ring-1 ${toneClass[side]}`}>
      <div className="mb-3 flex items-center justify-between gap-2">
        <Badge className={toneClass[side]} variant="secondary">
          {side === "long" ? "Long" : "Short"}
        </Badge>
        <div className="flex items-center gap-1 font-mono text-xs">
          <Gauge className="size-3" />
          {formatNumber(pick.pred, { maximumFractionDigits: 4 })}
        </div>
      </div>
      <StockIdentity logoClassName="size-10" symbol={pick.symbol} />
    </div>
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
