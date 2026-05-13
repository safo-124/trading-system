import { MarketBookGrid, MarketMoveView } from "@/components/swing/market-overview";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getAllMarketSnapshots } from "@/lib/api/client";
import { formatDate, formatNumber, formatSignedPercent } from "@/lib/utils";

export default async function SwingPage() {
  const snapshots = await getAllMarketSnapshots(5);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <h1 className="font-semibold text-2xl tracking-tight">Swing Strategy</h1>
          <p className="text-muted-foreground text-sm">
            Regional long-short books with company names, logos, model scores, and benchmark
            context.
          </p>
        </div>
        <Badge className="w-fit" variant="secondary">
          {snapshots.map((snapshot) => formatDate(snapshot.predictions.as_of)).join(" · ")}
        </Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {snapshots.map((snapshot) => (
          <Card key={snapshot.market.key}>
            <CardHeader>
              <CardDescription>{snapshot.market.label}</CardDescription>
              <CardTitle className="font-mono text-2xl">
                {formatNumber(snapshot.predictions.n_stocks)}
              </CardTitle>
              <div className="grid grid-cols-2 gap-2 pt-2 text-sm">
                <div>
                  <div className="text-muted-foreground text-xs">Net return</div>
                  <div className="font-mono">
                    {formatSignedPercent(snapshot.backtest.summary.ann_return_net)}
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground text-xs">Benchmark</div>
                  <div className="font-mono">{snapshot.market.benchmark}</div>
                </div>
              </div>
            </CardHeader>
          </Card>
        ))}
      </div>

      <section className="space-y-3">
        <div>
          <h2 className="font-semibold text-lg">Move View</h2>
          <p className="text-muted-foreground text-sm">
            A compact view of the strongest long and short candidate in each market.
          </p>
        </div>
        <MarketMoveView snapshots={snapshots} />
      </section>

      <section className="space-y-3">
        <div>
          <h2 className="font-semibold text-lg">Full Regional Books</h2>
          <p className="text-muted-foreground text-sm">
            Top five long and short candidates per market with company identity and logo.
          </p>
        </div>
        <MarketBookGrid snapshots={snapshots} />
      </section>
    </div>
  );
}
