import { DividendPicksTable } from "@/components/dividend/dividend-picks-table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getDividendPicks, topDividendPicks } from "@/lib/api/client";
import { formatDate, formatNumber } from "@/lib/utils";

export default async function DividendPage() {
  const dividendPicks = await getDividendPicks();
  const topPicks = topDividendPicks(dividendPicks.picks, 3);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <h1 className="font-semibold text-2xl tracking-tight">Dividend Screener</h1>
          <p className="text-muted-foreground text-sm">
            Rules-based yield, safety, and quality ranking from the research pipeline.
          </p>
        </div>
        <div className="text-left md:text-right">
          <div className="text-muted-foreground text-sm">Generated</div>
          <div className="font-mono text-sm">{formatDate(dividendPicks.generated_at ?? null)}</div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {topPicks.map((pick) => (
          <Card key={pick.ticker}>
            <CardHeader>
              <CardDescription>Top Pick</CardDescription>
              <CardTitle className="flex items-baseline justify-between gap-3">
                <span>{pick.ticker}</span>
                <span className="font-mono text-emerald-400 text-xl">
                  {formatNumber(pick.composite_score, { maximumFractionDigits: 3 })}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-2 text-sm">
              <MetricRow label="Yield" value={formatNumber(pick.yield, { style: "percent" })} />
              <MetricRow
                label="Safety"
                value={formatNumber(pick.safety_score, { maximumFractionDigits: 2 })}
              />
              <MetricRow
                label="FCF Coverage"
                value={`${formatNumber(pick.fcf_coverage, { maximumFractionDigits: 2 })}x`}
              />
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Dividend Picks</CardTitle>
          <CardDescription>{dividendPicks.n_picks} ranked stocks</CardDescription>
        </CardHeader>
        <CardContent>
          <DividendPicksTable picks={dividendPicks.picks} />
        </CardContent>
      </Card>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono">{value}</span>
    </div>
  );
}
