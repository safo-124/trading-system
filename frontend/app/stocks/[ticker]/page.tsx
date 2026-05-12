import { notFound } from "next/navigation";
import { DividendChart } from "@/components/stocks/dividend-chart";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getDividendHistory,
  getLatestPredictions,
  getPickForTicker,
  getStockDetail,
} from "@/lib/api/client";
import { formatDate, formatNumber } from "@/lib/utils";

type StockDetailPageProps = {
  params: Promise<{ ticker: string }>;
};

export default async function StockDetailPage({ params }: StockDetailPageProps) {
  const { ticker } = await params;
  const normalizedTicker = decodeURIComponent(ticker).toUpperCase();

  try {
    const [detail, dividends, latestPredictions] = await Promise.all([
      getStockDetail(normalizedTicker),
      getDividendHistory(normalizedTicker),
      getLatestPredictions(),
    ]);
    const fundamentals = detail.latest_fundamentals;
    const modelOutput = getPickForTicker(latestPredictions, normalizedTicker);

    return (
      <div className="space-y-6">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <h1 className="font-semibold text-3xl tracking-tight">{detail.stock.ticker}</h1>
              {detail.stock.sector ? (
                <Badge variant="secondary">{detail.stock.sector}</Badge>
              ) : null}
            </div>
            <p className="text-muted-foreground text-sm">{detail.stock.name ?? "Unnamed stock"}</p>
          </div>
          <div className="text-left md:text-right">
            <div className="text-muted-foreground text-sm">Current Yield</div>
            <div className="font-mono text-2xl">
              {formatNumber(fundamentals?.yield ?? null, { style: "percent" })}
            </div>
          </div>
        </div>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,0.8fr)]">
          <Card>
            <CardHeader>
              <CardTitle>Dividend History</CardTitle>
              <CardDescription>{dividends.dividends.length} recorded payments</CardDescription>
            </CardHeader>
            <CardContent>
              <DividendChart dividends={dividends.dividends} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Model Output</CardTitle>
              <CardDescription>{formatDate(modelOutput?.predicted_at)}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              <MetricRow
                label="Cut Probability"
                tone="risk"
                value={formatNumber(modelOutput?.cut_probability ?? null, { style: "percent" })}
              />
              <MetricRow
                label="Composite Score"
                tone="positive"
                value={formatNumber(modelOutput?.composite_score ?? null)}
              />
              <MetricRow label="Recommendation" value={modelOutput?.recommendation ?? "—"} />
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Fundamentals</CardTitle>
            <CardDescription>{formatDate(fundamentals?.as_of_date)}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <tbody className="[&_tr]:border-b [&_tr:last-child]:border-0">
                  <FundamentalRow
                    label="Market Cap"
                    value={formatNumber(detail.stock.market_cap, { style: "currency" })}
                  />
                  <FundamentalRow
                    label="Yield"
                    value={formatNumber(fundamentals?.yield ?? null, { style: "percent" })}
                  />
                  <FundamentalRow
                    label="Payout Ratio"
                    value={formatNumber(fundamentals?.payout_ratio ?? null, { style: "percent" })}
                  />
                  <FundamentalRow
                    label="Free Cash Flow"
                    value={formatNumber(fundamentals?.fcf ?? null, { style: "currency" })}
                  />
                  <FundamentalRow
                    label="Debt to Equity"
                    value={formatNumber(fundamentals?.debt_to_equity ?? null)}
                  />
                  <FundamentalRow
                    label="Return on Equity"
                    value={formatNumber(fundamentals?.roe ?? null, { style: "percent" })}
                  />
                  <FundamentalRow
                    label="Profit Margin"
                    value={formatNumber(fundamentals?.profit_margin ?? null, {
                      style: "percent",
                    })}
                  />
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  } catch {
    notFound();
  }
}

function MetricRow({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "positive" | "risk";
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-border/70 px-3 py-2">
      <span className="text-muted-foreground text-sm">{label}</span>
      <span
        className={
          tone === "positive"
            ? "font-mono text-emerald-400"
            : tone === "risk"
              ? "font-mono text-red-400"
              : "font-mono"
        }
      >
        {value}
      </span>
    </div>
  );
}

function FundamentalRow({ label, value }: { label: string; value: string }) {
  return (
    <tr>
      <th className="py-3 pr-4 text-left font-medium text-muted-foreground">{label}</th>
      <td className="py-3 text-right font-mono">{value}</td>
    </tr>
  );
}
