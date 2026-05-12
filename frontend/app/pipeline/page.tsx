import { RunButton } from "@/components/pipeline/run-button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getLatestPredictions } from "@/lib/api/client";
import { formatDate, formatNumber } from "@/lib/utils";

export default async function PipelinePage() {
  const latestPredictions = await getLatestPredictions();
  const latestTimestamp = latestPredictions.predictions[0]?.predicted_at ?? null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h1 className="font-semibold text-2xl tracking-tight">Pipeline</h1>
          <p className="text-muted-foreground text-sm">Run the dividend safety ranking model.</p>
        </div>
        <RunButton initialPredictions={latestPredictions} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Previous Picks</CardTitle>
          <CardDescription>{formatDate(latestTimestamp)}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="py-2 pr-3 text-right font-medium">Rank</th>
                  <th className="px-3 py-2 text-left font-medium">Ticker</th>
                  <th className="px-3 py-2 text-right font-medium">Cut Risk</th>
                  <th className="px-3 py-2 text-right font-medium">Score</th>
                  <th className="py-2 pl-3 text-left font-medium">Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {latestPredictions.predictions.map((pick) => (
                  <tr className="border-b last:border-0" key={`${pick.ticker}-${pick.rank}`}>
                    <td className="py-3 pr-3 text-right font-mono">{pick.rank}</td>
                    <td className="px-3 py-3 font-semibold">{pick.ticker}</td>
                    <td className="px-3 py-3 text-right font-mono text-red-400">
                      {formatNumber(pick.cut_probability, { style: "percent" })}
                    </td>
                    <td className="px-3 py-3 text-right font-mono text-emerald-400">
                      {formatNumber(pick.composite_score)}
                    </td>
                    <td className="py-3 pl-3">
                      <Badge variant={pick.recommendation === "BUY" ? "default" : "secondary"}>
                        {pick.recommendation}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {latestPredictions.predictions.length === 0 ? (
            <div className="rounded-lg border border-border/70 p-4 text-muted-foreground text-sm">
              No previous pipeline run.
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
