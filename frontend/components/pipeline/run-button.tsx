"use client";

import { RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { LatestPredictionsResponse, RankedPick } from "@/lib/api/client";
import { useLatestPredictionsQuery, useRunPipelineMutation } from "@/lib/api/queries";
import { formatNumber } from "@/lib/utils";

export function RunButton({
  initialPredictions,
}: {
  initialPredictions: LatestPredictionsResponse;
}) {
  const latestPredictions = useLatestPredictionsQuery(initialPredictions);
  const runPipeline = useRunPipelineMutation();
  const picks =
    runPipeline.data?.picks ??
    latestPredictions.data?.predictions ??
    initialPredictions.predictions;

  return (
    <div className="space-y-3">
      <Button disabled={runPipeline.isPending} onClick={() => runPipeline.mutate()} type="button">
        <RefreshCw className={runPipeline.isPending ? "animate-spin" : undefined} />
        {runPipeline.isPending ? "Running" : "Run Pipeline"}
      </Button>

      {runPipeline.isSuccess ? <PipelineResultTable picks={picks} /> : null}
      {runPipeline.isError ? (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-red-300 text-sm">
          Pipeline run failed.
        </div>
      ) : null}
    </div>
  );
}

function PipelineResultTable({ picks }: { picks: RankedPick[] }) {
  return (
    <div className="max-w-[720px] overflow-x-auto rounded-lg border border-border/70 bg-card">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-muted-foreground">
            <th className="px-3 py-2 text-right font-medium">Rank</th>
            <th className="px-3 py-2 text-left font-medium">Ticker</th>
            <th className="px-3 py-2 text-right font-medium">Cut Risk</th>
            <th className="px-3 py-2 text-right font-medium">Score</th>
            <th className="px-3 py-2 text-left font-medium">Recommendation</th>
          </tr>
        </thead>
        <tbody>
          {picks.map((pick) => (
            <tr className="border-b last:border-0" key={`${pick.ticker}-${pick.rank}`}>
              <td className="px-3 py-2 text-right font-mono">{pick.rank}</td>
              <td className="px-3 py-2 font-semibold">{pick.ticker}</td>
              <td className="px-3 py-2 text-right font-mono text-red-400">
                {formatNumber(pick.cut_probability, { style: "percent" })}
              </td>
              <td className="px-3 py-2 text-right font-mono text-emerald-400">
                {formatNumber(pick.composite_score)}
              </td>
              <td className="px-3 py-2">
                <Badge variant={pick.recommendation === "BUY" ? "default" : "secondary"}>
                  {pick.recommendation}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
