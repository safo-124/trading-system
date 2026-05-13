import { ReturnsChart } from "@/components/backtest/returns-chart";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getBacktestSummary } from "@/lib/api/client";
import { formatBps, formatDate, formatNumber, formatSignedPercent } from "@/lib/utils";

export default async function BacktestPage() {
  const backtest = await getBacktestSummary();
  const summary = backtest.summary;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-semibold text-2xl tracking-tight">Backtest</h1>
        <p className="text-muted-foreground text-sm">
          Walk-forward long-short results after the leg-sign fix.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard
          label="Gross Ann. Return"
          tone="positive"
          value={formatSignedPercent(summary.ann_return_gross)}
        />
        <MetricCard
          label="Net Ann. Return"
          tone="positive"
          value={formatSignedPercent(summary.ann_return_net)}
        />
        <MetricCard
          label="Net Sharpe"
          value={formatNumber(summary.sharpe_net, { maximumFractionDigits: 2 })}
        />
        <MetricCard
          label="Max Drawdown"
          tone="risk"
          value={formatSignedPercent(summary.max_drawdown_net)}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Last 30 Trading Days</CardTitle>
          <CardDescription>
            {formatDate(summary.start_date)} to {formatDate(summary.end_date)} ·{" "}
            {formatNumber(summary.n_days)} trading days
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ReturnsChart days={backtest.last_30_days} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Daily Return Detail</CardTitle>
          <CardDescription>Gross and net return records from the API.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">Gross</TableHead>
                <TableHead className="text-right">Net</TableHead>
                <TableHead className="text-right">Long Leg</TableHead>
                <TableHead className="text-right">Short Leg</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {backtest.last_30_days.map((day) => (
                <TableRow key={day.timestamp}>
                  <TableCell>{formatDate(day.timestamp)}</TableCell>
                  <TableCell className="text-right font-mono">
                    {formatBps(day.daily_ret_gross)}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatBps(day.daily_ret_net)}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatSignedPercent(day.long_ret)}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatSignedPercent(day.short_ret)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
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
