import { PredictionTable } from "@/components/swing/prediction-table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getSwingLatestPredictions } from "@/lib/api/client";
import { formatDate, formatNumber, formatSignedPercent } from "@/lib/utils";

export default async function SwingPage() {
  const predictions = await getSwingLatestPredictions(20);
  const longAverage =
    predictions.long_picks.reduce((sum, pick) => sum + (pick.fwd_ret_5d ?? 0), 0) /
    Math.max(predictions.long_picks.length, 1);
  const shortAverage =
    predictions.short_picks.reduce((sum, pick) => sum + (pick.fwd_ret_5d ?? 0), 0) /
    Math.max(predictions.short_picks.length, 1);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <h1 className="font-semibold text-2xl tracking-tight">Swing Model</h1>
          <p className="text-muted-foreground text-sm">
            Cross-sectional model picks for the latest out-of-sample prediction day.
          </p>
        </div>
        <Badge className="w-fit" variant="secondary">
          {formatDate(predictions.as_of)}
        </Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Stocks Ranked" value={formatNumber(predictions.n_stocks)} />
        <MetricCard
          label="Long Avg Fwd 5D"
          tone="positive"
          value={formatSignedPercent(longAverage)}
        />
        <MetricCard
          label="Short Avg Fwd 5D"
          tone="risk"
          value={formatSignedPercent(shortAverage)}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-emerald-400">Long Book</CardTitle>
            <CardDescription>Highest model predictions</CardDescription>
          </CardHeader>
          <CardContent>
            <PredictionTable picks={predictions.long_picks} side="long" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-red-400">Short Book</CardTitle>
            <CardDescription>Lowest model predictions</CardDescription>
          </CardHeader>
          <CardContent>
            <PredictionTable picks={predictions.short_picks} side="short" />
          </CardContent>
        </Card>
      </div>
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
