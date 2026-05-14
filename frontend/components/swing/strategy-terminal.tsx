"use client";

import {
  type Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Boxes,
  Brain,
  CheckCircle2,
  CircleDollarSign,
  Clock3,
  Gauge,
  Globe2,
  Loader2,
  Radar,
  RefreshCw,
  Search,
  ShieldCheck,
  X,
  Zap,
} from "lucide-react";
import { useMemo, useState } from "react";
import { StockIdentity, StockLogo } from "@/components/stocks/stock-identity";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type {
  LivePick,
  LivePredictionResponse,
  MarketInfo,
  SwingPrediction,
} from "@/lib/api/client";
import { getStockMetadata } from "@/lib/stock-metadata";
import { cn, formatDate, formatNumber, formatSignedPercent } from "@/lib/utils";
import type { MarketSnapshot } from "./market-overview";

type TerminalTab = "overview" | "books" | "backtests" | "live";
type PositionSide = "long" | "short";
type PickRecord = SwingPrediction | LivePick;
type SelectedStock = {
  market: MarketInfo;
  side: PositionSide;
  pick: PickRecord;
  source: "historical" | "live";
};

const tabs: { key: TerminalTab; label: string; icon: typeof Activity }[] = [
  { key: "overview", label: "Overview", icon: Globe2 },
  { key: "books", label: "Books", icon: Boxes },
  { key: "backtests", label: "Backtests", icon: BarChart3 },
  { key: "live", label: "Live", icon: Zap },
];

const sideTone = {
  long: {
    text: "text-emerald-300",
    subtle: "bg-emerald-500/12 text-emerald-300 ring-emerald-500/20",
    solid: "bg-emerald-500 text-black",
    border: "border-emerald-500/25",
  },
  short: {
    text: "text-rose-300",
    subtle: "bg-rose-500/12 text-rose-300 ring-rose-500/20",
    solid: "bg-rose-500 text-white",
    border: "border-rose-500/25",
  },
};

export function StrategyTerminal({ snapshots }: { snapshots: MarketSnapshot[] }) {
  const [activeTab, setActiveTab] = useState<TerminalTab>("overview");
  const [countryFilter, setCountryFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStock, setSelectedStock] = useState<SelectedStock | null>(null);
  const countryOptions = useMemo(() => buildCountryOptions(snapshots), [snapshots]);
  const filteredSnapshots = useMemo(
    () => filterSnapshots(snapshots, countryFilter, searchQuery),
    [snapshots, countryFilter, searchQuery],
  );
  const strongestMarket = useMemo(
    () =>
      [...snapshots].sort(
        (left, right) => right.backtest.summary.sharpe_net - left.backtest.summary.sharpe_net,
      )[0],
    [snapshots],
  );
  const totalStocks = snapshots.reduce((sum, snapshot) => sum + snapshot.predictions.n_stocks, 0);

  return (
    <div className="space-y-5">
      <CommandCenter
        snapshots={snapshots}
        strongestMarketLabel={strongestMarket?.market.label ?? "—"}
        totalStocks={totalStocks}
      />

      <div className="sticky top-0 z-20 flex gap-2 border-border/70 border-b bg-background/90 py-2 backdrop-blur">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <Button
              className={cn(isActive && "bg-primary text-primary-foreground")}
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              type="button"
              variant={isActive ? "default" : "ghost"}
            >
              <Icon className="size-4" />
              {tab.label}
            </Button>
          );
        })}
      </div>

      <CountryFilterBar
        activeCountry={countryFilter}
        countries={countryOptions}
        onChange={setCountryFilter}
        onSearchChange={setSearchQuery}
        searchQuery={searchQuery}
      />

      {activeTab === "overview" ? (
        <OverviewTab onSelectStock={setSelectedStock} snapshots={filteredSnapshots} />
      ) : null}
      {activeTab === "books" ? (
        <BooksTab onSelectStock={setSelectedStock} snapshots={filteredSnapshots} />
      ) : null}
      {activeTab === "backtests" ? <BacktestsTab snapshots={snapshots} /> : null}
      {activeTab === "live" ? (
        <LiveTab
          countryFilter={countryFilter}
          searchQuery={searchQuery}
          onSelectStock={setSelectedStock}
          snapshots={snapshots}
        />
      ) : null}

      <StockDetailDrawer selected={selectedStock} onClose={() => setSelectedStock(null)} />
    </div>
  );
}

function CommandCenter({
  snapshots,
  totalStocks,
  strongestMarketLabel,
}: {
  snapshots: MarketSnapshot[];
  totalStocks: number;
  strongestMarketLabel: string;
}) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr_1fr_1fr]">
      <Card className="overflow-hidden border-primary/20 bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,0.16),transparent_36%),linear-gradient(135deg,rgba(255,255,255,0.06),transparent)]">
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div>
              <CardDescription>Trading System</CardDescription>
              <CardTitle className="text-2xl">Cross-Market Strategy Terminal</CardTitle>
            </div>
            <Badge className="bg-emerald-500/15 text-emerald-300" variant="secondary">
              <CheckCircle2 className="size-3.5" />
              Online
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-3">
          <MiniMetric label="Markets" value={formatNumber(snapshots.length)} />
          <MiniMetric label="Stocks ranked" value={formatNumber(totalStocks)} />
          <MiniMetric label="Best market" value={strongestMarketLabel} />
        </CardContent>
      </Card>

      {snapshots.map((snapshot) => (
        <Card key={snapshot.market.key}>
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardDescription>{snapshot.market.region}</CardDescription>
                <CardTitle>{snapshot.market.label}</CardTitle>
              </div>
              <Badge variant="secondary">{snapshot.market.benchmark}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <MiniMetric label="As of" value={formatDate(snapshot.predictions.as_of)} />
              <MiniMetric label="Ranked" value={formatNumber(snapshot.predictions.n_stocks)} />
              <MiniMetric
                label="Net Sharpe"
                value={formatNumber(snapshot.backtest.summary.sharpe_net, {
                  maximumFractionDigits: 2,
                })}
              />
              <MiniMetric
                label="Net Ann."
                value={formatSignedPercent(snapshot.backtest.summary.ann_return_net)}
              />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function CountryFilterBar({
  activeCountry,
  countries,
  onChange,
  onSearchChange,
  searchQuery,
}: {
  activeCountry: string;
  countries: { country: string; count: number }[];
  onChange: (country: string) => void;
  onSearchChange: (query: string) => void;
  searchQuery: string;
}) {
  return (
    <Card>
      <CardContent className="grid gap-3 py-3 xl:grid-cols-[minmax(16rem,24rem)_minmax(0,1fr)] xl:items-center">
        <div className="relative">
          <Search className="-translate-y-1/2 absolute top-1/2 left-3 size-4 text-muted-foreground" />
          <input
            className="h-9 w-full rounded-lg border border-input bg-background px-9 text-sm outline-none transition placeholder:text-muted-foreground focus:border-primary focus:ring-3 focus:ring-primary/20"
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search ticker, company, exchange, country..."
            type="search"
            value={searchQuery}
          />
          {searchQuery ? (
            <button
              className="-translate-y-1/2 absolute top-1/2 right-2 rounded-md p-1 text-muted-foreground transition hover:bg-muted hover:text-foreground"
              onClick={() => onSearchChange("")}
              type="button"
            >
              <X className="size-3.5" />
            </button>
          ) : null}
        </div>
        <div className="flex min-w-0 items-center gap-2">
          <div className="hidden shrink-0 items-center gap-2 text-muted-foreground text-sm lg:flex">
            <Globe2 className="size-4" />
            Countries
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1 lg:pb-0">
            <Button
              className={cn(activeCountry === "all" && "bg-primary text-primary-foreground")}
              onClick={() => onChange("all")}
              size="sm"
              type="button"
              variant={activeCountry === "all" ? "default" : "outline"}
            >
              All countries
            </Button>
            {countries.map((option) => (
              <Button
                className={cn(
                  activeCountry === option.country && "bg-primary text-primary-foreground",
                )}
                key={option.country}
                onClick={() => onChange(option.country)}
                size="sm"
                type="button"
                variant={activeCountry === option.country ? "default" : "outline"}
              >
                {option.country}
                <span className="font-mono text-xs opacity-70">{option.count}</span>
              </Button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function OverviewTab({
  snapshots,
  onSelectStock,
}: {
  snapshots: MarketSnapshot[];
  onSelectStock: (selected: SelectedStock) => void;
}) {
  return (
    <div className="space-y-5">
      <div className="grid gap-4 xl:grid-cols-3">
        {snapshots.map((snapshot) => (
          <MovePanel key={snapshot.market.key} snapshot={snapshot} onSelectStock={onSelectStock} />
        ))}
      </div>
      <SignalHeatmap snapshots={snapshots} onSelectStock={onSelectStock} />
    </div>
  );
}

function MovePanel({
  snapshot,
  onSelectStock,
}: {
  snapshot: MarketSnapshot;
  onSelectStock: (selected: SelectedStock) => void;
}) {
  const longPick = snapshot.predictions.long_picks[0];
  const shortPick = snapshot.predictions.short_picks[0];
  const spread = longPick && shortPick ? longPick.pred - shortPick.pred : null;

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>{snapshot.market.label} Move</CardTitle>
            <CardDescription>
              {snapshot.market.region} · {formatDate(snapshot.predictions.as_of)}
            </CardDescription>
          </div>
          <Badge variant="secondary">{snapshot.market.benchmark}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3">
          {longPick ? (
            <HeroPickButton
              market={snapshot.market}
              pick={longPick}
              side="long"
              source="historical"
              onSelectStock={onSelectStock}
            />
          ) : null}
          {shortPick ? (
            <HeroPickButton
              market={snapshot.market}
              pick={shortPick}
              side="short"
              source="historical"
              onSelectStock={onSelectStock}
            />
          ) : null}
          {!longPick && !shortPick ? <EmptyFilterState /> : null}
        </div>
        <div className="grid grid-cols-3 gap-2 border-border/70 border-t pt-3">
          <MiniMetric label="Spread" value={formatNumber(spread, { maximumFractionDigits: 4 })} />
          <MiniMetric
            label="Net return"
            value={formatSignedPercent(snapshot.backtest.summary.ann_return_net)}
          />
          <MiniMetric
            label="Sharpe"
            value={formatNumber(snapshot.backtest.summary.sharpe_net, {
              maximumFractionDigits: 2,
            })}
          />
        </div>
      </CardContent>
    </Card>
  );
}

function HeroPickButton({
  market,
  pick,
  side,
  source,
  onSelectStock,
}: {
  market: MarketInfo;
  pick: PickRecord;
  side: PositionSide;
  source: SelectedStock["source"];
  onSelectStock: (selected: SelectedStock) => void;
}) {
  const metadata = getStockMetadata(pick.symbol);
  const Icon = side === "long" ? ArrowUpRight : ArrowDownRight;

  return (
    <button
      className={cn(
        "group w-full rounded-lg border p-3 text-left transition hover:bg-accent/45",
        sideTone[side].border,
      )}
      onClick={() => onSelectStock({ market, pick, side, source })}
      type="button"
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <StockLogo className="size-11" symbol={pick.symbol} />
          <div className="min-w-0">
            <div className="flex min-w-0 items-center gap-2">
              <Badge className={sideTone[side].subtle} variant="secondary">
                <Icon className="size-3.5" />
                {side}
              </Badge>
              <span className="truncate font-semibold">{pick.symbol}</span>
            </div>
            <div className="truncate text-muted-foreground text-sm">{metadata.name}</div>
          </div>
        </div>
        <div className="text-right">
          <div className={cn("font-mono text-lg", sideTone[side].text)}>
            {formatNumber(pick.pred, { maximumFractionDigits: 4 })}
          </div>
          <div className="text-muted-foreground text-xs">{metadata.exchange}</div>
        </div>
      </div>
      <ScoreRail pred={pick.pred} side={side} />
    </button>
  );
}

function BooksTab({
  snapshots,
  onSelectStock,
}: {
  snapshots: MarketSnapshot[];
  onSelectStock: (selected: SelectedStock) => void;
}) {
  return (
    <div className="grid gap-4 xl:grid-cols-3">
      {snapshots.map((snapshot) => (
        <Card key={snapshot.market.key}>
          <CardHeader>
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle>{snapshot.market.label} Book</CardTitle>
                <CardDescription>
                  {formatNumber(snapshot.predictions.n_stocks)} stocks ·{" "}
                  {formatDate(snapshot.predictions.as_of)}
                </CardDescription>
              </div>
              <Badge className="bg-primary/15 text-primary" variant="secondary">
                {snapshot.market.region}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <BookList
              market={snapshot.market}
              picks={snapshot.predictions.long_picks}
              side="long"
              onSelectStock={onSelectStock}
            />
            <BookList
              market={snapshot.market}
              picks={snapshot.predictions.short_picks}
              side="short"
              onSelectStock={onSelectStock}
            />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function BookList({
  market,
  picks,
  side,
  onSelectStock,
}: {
  market: MarketInfo;
  picks: SwingPrediction[];
  side: PositionSide;
  onSelectStock: (selected: SelectedStock) => void;
}) {
  const Icon = side === "long" ? ArrowUpRight : ArrowDownRight;

  return (
    <div>
      <div className={cn("mb-2 flex items-center gap-2 text-xs uppercase", sideTone[side].text)}>
        <Icon className="size-3.5" />
        {side} candidates
      </div>
      {picks.length === 0 ? (
        <EmptyFilterState compact />
      ) : (
        <div className="overflow-hidden rounded-lg border border-border/70">
          {picks.map((pick, index) => (
            <button
              className="grid w-full grid-cols-[2rem_minmax(0,1fr)_auto] items-center gap-3 border-border/60 border-b px-3 py-2 text-left transition last:border-b-0 hover:bg-accent/45"
              key={`${market.key}-${side}-${pick.symbol}`}
              onClick={() => onSelectStock({ market, pick, side, source: "historical" })}
              type="button"
            >
              <div className="font-mono text-muted-foreground text-xs">#{index + 1}</div>
              <StockIdentity dense symbol={pick.symbol} />
              <div className="text-right">
                <div className="font-mono text-sm">
                  {formatNumber(pick.pred, { maximumFractionDigits: 4 })}
                </div>
                <div className="font-mono text-muted-foreground text-xs">
                  {formatSignedPercent(pick.fwd_ret_5d)}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function BacktestsTab({ snapshots }: { snapshots: MarketSnapshot[] }) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Card>
        <CardHeader>
          <CardTitle>Performance Matrix</CardTitle>
          <CardDescription>Walk-forward results by region, net of stated costs.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {snapshots.map((snapshot) => (
            <PerformanceRow key={snapshot.market.key} snapshot={snapshot} />
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Risk Map</CardTitle>
          <CardDescription>Annualized return, drawdown, and hit rate at a glance.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {snapshots.map((snapshot) => (
            <RiskMapRow key={snapshot.market.key} snapshot={snapshot} />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

export function BacktestAnalytics({ snapshots }: { snapshots: MarketSnapshot[] }) {
  return <BacktestsTab snapshots={snapshots} />;
}

function PerformanceRow({ snapshot }: { snapshot: MarketSnapshot }) {
  const summary = snapshot.backtest.summary;
  const sharpeWidth = Math.max(4, Math.min(100, Math.abs(summary.sharpe_net) * 55));

  return (
    <div className="rounded-lg border border-border/70 p-3">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{snapshot.market.benchmark}</Badge>
          <div className="font-semibold">{snapshot.market.label}</div>
        </div>
        <div className="font-mono text-muted-foreground text-xs">
          {formatDate(summary.start_date)} → {formatDate(summary.end_date)}
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-4">
        <MiniMetric label="Gross ann." value={formatSignedPercent(summary.ann_return_gross)} />
        <MiniMetric label="Net ann." value={formatSignedPercent(summary.ann_return_net)} />
        <MiniMetric
          label="Sharpe"
          value={formatNumber(summary.sharpe_net, { maximumFractionDigits: 2 })}
        />
        <MiniMetric
          label="Hit rate"
          value={formatNumber(summary.hit_rate_net, { style: "percent" })}
        />
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-secondary">
        <div
          className={cn(
            "h-full rounded-full",
            summary.sharpe_net >= 0 ? "bg-emerald-400" : "bg-rose-400",
          )}
          style={{ width: `${sharpeWidth}%` }}
        />
      </div>
    </div>
  );
}

function RiskMapRow({ snapshot }: { snapshot: MarketSnapshot }) {
  const summary = snapshot.backtest.summary;
  return (
    <div className="grid gap-2 rounded-lg border border-border/70 p-3 sm:grid-cols-[9rem_1fr] sm:items-center">
      <div>
        <div className="font-semibold">{snapshot.market.label}</div>
        <div className="text-muted-foreground text-xs">{formatNumber(summary.n_days)} days</div>
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        <RiskChip label="Net" value={summary.ann_return_net} />
        <RiskChip label="Drawdown" value={summary.max_drawdown_net} negativeIsGood />
        <RiskChip label="Vol" value={summary.ann_vol} neutral />
      </div>
    </div>
  );
}

function RiskChip({
  label,
  value,
  negativeIsGood = false,
  neutral = false,
}: {
  label: string;
  value: number;
  negativeIsGood?: boolean;
  neutral?: boolean;
}) {
  const good = neutral ? null : negativeIsGood ? value > -0.15 : value >= 0;
  return (
    <div
      className={cn(
        "rounded-lg px-3 py-2 ring-1",
        good === null
          ? "bg-sky-500/10 text-sky-200 ring-sky-500/20"
          : good
            ? "bg-emerald-500/10 text-emerald-200 ring-emerald-500/20"
            : "bg-rose-500/10 text-rose-200 ring-rose-500/20",
      )}
    >
      <div className="text-muted-foreground text-xs">{label}</div>
      <div className="font-mono">{formatSignedPercent(value)}</div>
    </div>
  );
}

function LiveTab({
  snapshots,
  countryFilter,
  searchQuery,
  onSelectStock,
}: {
  snapshots: MarketSnapshot[];
  countryFilter: string;
  searchQuery: string;
  onSelectStock: (selected: SelectedStock) => void;
}) {
  const [liveResults, setLiveResults] = useState<Record<string, LivePredictionResponse>>({});
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function runLive(market: MarketInfo, forceRefresh = false) {
    setLoading(market.key);
    setError(null);
    try {
      const response = await fetch(
        `/api/trading/${market.key}/predict-today?n_per_side=${market.defaultNPerSide}&force_refresh=${forceRefresh}`,
      );
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? `Live model failed with status ${response.status}`);
      }
      setLiveResults((current) => ({ ...current, [market.key]: payload }));
    } catch (liveError) {
      setError(liveError instanceof Error ? liveError.message : "Live model failed");
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="space-y-4">
      <Card className="border-amber-500/20 bg-amber-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Radar className="size-5 text-amber-300" />
            Live Model Console
          </CardTitle>
          <CardDescription>
            Runs fresh yfinance fetches through the saved production models. Responses are cached by
            the FastAPI layer for 15 minutes.
          </CardDescription>
        </CardHeader>
      </Card>

      {error ? (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-rose-200 text-sm">
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-3">
        {snapshots.map((snapshot) => {
          const result = liveResults[snapshot.market.key];
          const isLoading = loading === snapshot.market.key;
          return (
            <Card key={snapshot.market.key}>
              <CardHeader>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <CardTitle>{snapshot.market.label}</CardTitle>
                    <CardDescription>
                      {snapshot.market.defaultNPerSide}/side · benchmark {snapshot.market.benchmark}
                    </CardDescription>
                  </div>
                  <Badge variant="secondary">{result ? formatDate(result.as_of) : "cached"}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Button
                    disabled={isLoading}
                    onClick={() => runLive(snapshot.market)}
                    type="button"
                  >
                    {isLoading ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <Brain className="size-4" />
                    )}
                    Run live
                  </Button>
                  <Button
                    disabled={isLoading}
                    onClick={() => runLive(snapshot.market, true)}
                    type="button"
                    variant="outline"
                  >
                    <RefreshCw className="size-4" />
                    Refresh
                  </Button>
                </div>

                {result ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-2">
                      <MiniMetric
                        label="Predicted"
                        value={formatNumber(result.n_stocks_predicted)}
                      />
                      <MiniMetric label="Model" value={result.model_trained_at ? "trained" : "—"} />
                    </div>
                    <LivePickList
                      market={snapshot.market}
                      picks={filterPicks(
                        result.long_picks,
                        countryFilter,
                        searchQuery,
                        snapshot.market,
                      ).slice(0, 5)}
                      side="long"
                      onSelectStock={onSelectStock}
                    />
                    <LivePickList
                      market={snapshot.market}
                      picks={filterPicks(
                        result.short_picks,
                        countryFilter,
                        searchQuery,
                        snapshot.market,
                      ).slice(0, 5)}
                      side="short"
                      onSelectStock={onSelectStock}
                    />
                  </div>
                ) : (
                  <div className="rounded-lg border border-dashed border-border px-3 py-6 text-center text-muted-foreground text-sm">
                    No live run in this browser session yet.
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

function LivePickList({
  market,
  picks,
  side,
  onSelectStock,
}: {
  market: MarketInfo;
  picks: LivePick[];
  side: PositionSide;
  onSelectStock: (selected: SelectedStock) => void;
}) {
  return (
    <div>
      <div className={cn("mb-2 text-xs uppercase", sideTone[side].text)}>{side} live picks</div>
      {picks.length === 0 ? <EmptyFilterState compact /> : null}
      <div className="space-y-2">
        {picks.map((pick) => (
          <button
            className="flex w-full items-center justify-between gap-3 rounded-lg border border-border/70 px-3 py-2 text-left transition hover:bg-accent/45"
            key={`${market.key}-live-${side}-${pick.symbol}`}
            onClick={() => onSelectStock({ market, pick, side, source: "live" })}
            type="button"
          >
            <StockIdentity dense symbol={pick.symbol} />
            <div className="text-right">
              <div className="font-mono text-sm">
                {formatNumber(pick.pred, { maximumFractionDigits: 4 })}
              </div>
              <div className="font-mono text-muted-foreground text-xs">
                {formatNumber(pick.close, { maximumFractionDigits: 2 })}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function SignalHeatmap({
  snapshots,
  onSelectStock,
}: {
  snapshots: MarketSnapshot[];
  onSelectStock: (selected: SelectedStock) => void;
}) {
  const cells = snapshots.flatMap((snapshot) => [
    ...snapshot.predictions.long_picks.map((pick) => ({
      market: snapshot.market,
      pick,
      side: "long" as const,
    })),
    ...snapshot.predictions.short_picks.map((pick) => ({
      market: snapshot.market,
      pick,
      side: "short" as const,
    })),
  ]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Global Signal Heatmap</CardTitle>
        <CardDescription>
          Click any ranked cell to inspect company identity, score, signal posture, and leg context.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {cells.length === 0 ? (
          <EmptyFilterState />
        ) : (
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6">
            {cells.map(({ market, pick, side }) => (
              <button
                className={cn(
                  "rounded-lg border px-3 py-3 text-left transition hover:scale-[1.01] hover:bg-accent/45",
                  sideTone[side].border,
                )}
                key={`${market.key}-heat-${side}-${pick.symbol}`}
                onClick={() => onSelectStock({ market, pick, side, source: "historical" })}
                type="button"
              >
                <div className="mb-3 flex items-center justify-between gap-2">
                  <StockLogo className="size-8" symbol={pick.symbol} />
                  <Badge className={sideTone[side].subtle} variant="secondary">
                    {market.label}
                  </Badge>
                </div>
                <div className="truncate font-semibold">{pick.symbol}</div>
                <div className="truncate text-muted-foreground text-xs">
                  {getStockMetadata(pick.symbol).name}
                </div>
                <ScoreRail pred={pick.pred} side={side} compact />
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function StockDetailDrawer({
  selected,
  onClose,
}: {
  selected: SelectedStock | null;
  onClose: () => void;
}) {
  if (!selected) {
    return null;
  }

  const metadata = getStockMetadata(selected.pick.symbol);
  const observedReturn = "fwd_ret_5d" in selected.pick ? selected.pick.fwd_ret_5d : null;
  const close = "close" in selected.pick ? selected.pick.close : null;
  const directionalScore =
    selected.side === "long" ? selected.pick.pred : Math.max(0, 1 - selected.pick.pred);
  const conviction = Math.min(1, Math.abs(selected.pick.pred - 0.5) * 2);

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm">
      <button className="absolute inset-0 cursor-default" onClick={onClose} type="button" />
      <aside className="absolute top-0 right-0 h-full w-full max-w-md overflow-y-auto border-border border-l bg-background shadow-2xl">
        <div className="sticky top-0 z-10 flex items-center justify-between border-border border-b bg-background/95 px-5 py-4 backdrop-blur">
          <div className="flex items-center gap-3">
            <StockLogo className="size-11" symbol={selected.pick.symbol} />
            <div>
              <div className="font-semibold">{selected.pick.symbol}</div>
              <div className="text-muted-foreground text-xs">{metadata.exchange}</div>
            </div>
          </div>
          <Button onClick={onClose} size="icon" type="button" variant="ghost">
            <X className="size-4" />
          </Button>
        </div>

        <div className="space-y-5 px-5 py-5">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <Badge className={sideTone[selected.side].subtle} variant="secondary">
                {selected.side}
              </Badge>
              <Badge variant="secondary">{selected.market.label}</Badge>
              <Badge variant="secondary">{metadata.country}</Badge>
              <Badge variant="secondary">{selected.source}</Badge>
            </div>
            <h3 className="font-semibold text-xl">{metadata.name}</h3>
            <p className="mt-1 text-muted-foreground text-sm">
              {selected.market.region} book against {selected.market.benchmark}. The model ranks
              expected 5-day forward return on a cross-sectional scale.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <DetailMetric
              icon={Gauge}
              label="Model score"
              value={formatNumber(selected.pick.pred, { maximumFractionDigits: 4 })}
            />
            <DetailMetric
              icon={ShieldCheck}
              label="Conviction"
              value={formatNumber(conviction, { style: "percent" })}
            />
            <DetailMetric
              icon={CircleDollarSign}
              label={close === null ? "Observed 5D" : "Last close"}
              value={
                close === null
                  ? formatSignedPercent(observedReturn)
                  : formatNumber(close, { maximumFractionDigits: 2 })
              }
            />
            <DetailMetric icon={Clock3} label="As of" value={formatDate(selected.pick.timestamp)} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Signal Stack</CardTitle>
              <CardDescription>Direction-aware readout from the model score.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <SignalBar label="Directional score" value={directionalScore} />
              <SignalBar label="Cross-sectional spread" value={conviction} />
              <SignalBar label="Portfolio fit" value={selected.side === "long" ? 0.72 : 0.68} />
            </CardContent>
          </Card>
        </div>
      </aside>
    </div>
  );
}

function DetailMetric({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Gauge;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-border/70 px-3 py-3">
      <div className="mb-2 flex items-center gap-2 text-muted-foreground text-xs">
        <Icon className="size-3.5" />
        {label}
      </div>
      <div className="font-mono text-lg">{value}</div>
    </div>
  );
}

function SignalBar({ label, value }: { label: string; value: number }) {
  const pct = Math.max(0, Math.min(100, value * 100));
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-mono">{formatNumber(value, { style: "percent" })}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-secondary">
        <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function ScoreRail({
  pred,
  side,
  compact = false,
}: {
  pred: number;
  side: PositionSide;
  compact?: boolean;
}) {
  const pct = Math.max(4, Math.min(100, pred * 100));
  return (
    <div className={cn("mt-3", compact && "mt-2")}>
      <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
        <div
          className={cn("h-full rounded-full", side === "long" ? "bg-emerald-400" : "bg-rose-400")}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg bg-secondary/35 px-3 py-2">
      <div className="truncate text-muted-foreground text-xs">{label}</div>
      <div className="truncate font-mono text-sm">{value}</div>
    </div>
  );
}

function EmptyFilterState({ compact = false }: { compact?: boolean }) {
  return (
    <div
      className={cn(
        "rounded-lg border border-dashed border-border px-3 text-center text-muted-foreground text-sm",
        compact ? "py-3" : "py-6",
      )}
    >
      No names in this view for the selected filters.
    </div>
  );
}

function buildCountryOptions(snapshots: MarketSnapshot[]): { country: string; count: number }[] {
  const counts = new Map<string, number>();

  for (const snapshot of snapshots) {
    const picks = [...snapshot.predictions.long_picks, ...snapshot.predictions.short_picks];
    for (const pick of picks) {
      const country = getStockMetadata(pick.symbol).country ?? "Unknown";
      counts.set(country, (counts.get(country) ?? 0) + 1);
    }
  }

  return [...counts.entries()]
    .map(([country, count]) => ({ country, count }))
    .sort((left, right) => left.country.localeCompare(right.country));
}

function filterSnapshots(
  snapshots: MarketSnapshot[],
  country: string,
  query: string,
): MarketSnapshot[] {
  if (country === "all" && query.trim() === "") {
    return snapshots;
  }

  return snapshots.map((snapshot) => ({
    ...snapshot,
    predictions: {
      ...snapshot.predictions,
      long_picks: filterPicks(snapshot.predictions.long_picks, country, query, snapshot.market),
      short_picks: filterPicks(snapshot.predictions.short_picks, country, query, snapshot.market),
    },
  }));
}

function filterPicks<T extends PickRecord>(
  picks: T[],
  country: string,
  query: string,
  market?: MarketInfo,
): T[] {
  const normalizedQuery = query.trim().toLowerCase();

  return picks.filter((pick) => {
    const metadata = getStockMetadata(pick.symbol);
    const countryMatches = country === "all" || metadata.country === country;
    if (!countryMatches) {
      return false;
    }

    if (!normalizedQuery) {
      return true;
    }

    return [
      pick.symbol,
      metadata.name,
      metadata.exchange,
      metadata.country,
      market?.label,
      market?.region,
      market?.benchmark,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(normalizedQuery));
  });
}
