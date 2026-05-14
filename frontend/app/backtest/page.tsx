import { BacktestAnalytics } from "@/components/swing/strategy-terminal";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getAllMarketSnapshots } from "@/lib/api/client";
import { formatNumber, formatSignedPercent } from "@/lib/utils";

export default async function BacktestPage() {
  const snapshots = await getAllMarketSnapshots(5);
  const bestSharpe = [...snapshots].sort(
    (left, right) => right.backtest.summary.sharpe_net - left.backtest.summary.sharpe_net,
  )[0];
  const bestReturn = [...snapshots].sort(
    (left, right) => right.backtest.summary.ann_return_net - left.backtest.summary.ann_return_net,
  )[0];
  const avgSharpe =
    snapshots.reduce((sum, snapshot) => sum + snapshot.backtest.summary.sharpe_net, 0) /
    snapshots.length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <h1 className="font-semibold text-2xl tracking-tight">Backtest Lab</h1>
          <p className="text-muted-foreground text-sm">
            Cross-market walk-forward results for US, Europe, and JSE strategies.
          </p>
        </div>
        <Badge className="w-fit" variant="secondary">
          gross vs net · benchmark aware
        </Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          label="Best Net Sharpe"
          value={`${bestSharpe.market.label} ${formatNumber(bestSharpe.backtest.summary.sharpe_net, { maximumFractionDigits: 2 })}`}
        />
        <MetricCard
          label="Best Net Return"
          value={`${bestReturn.market.label} ${formatSignedPercent(bestReturn.backtest.summary.ann_return_net)}`}
        />
        <MetricCard
          label="Average Sharpe"
          value={formatNumber(avgSharpe, { maximumFractionDigits: 2 })}
        />
      </div>

      <BacktestAnalytics snapshots={snapshots} />
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
