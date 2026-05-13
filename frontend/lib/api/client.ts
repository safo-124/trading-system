import createClient from "openapi-fetch";
import { z } from "zod";
import type { components, paths } from "@/lib/api/schema";

export type HealthResponse = components["schemas"]["HealthResponse"];
export type DividendPick = components["schemas"]["DividendPick"];
export type DividendPicksResponse = components["schemas"]["DividendPicksResponse"];
export type SwingPrediction = components["schemas"]["SwingPrediction"];
export type SwingPredictionsResponse = components["schemas"]["SwingPredictionsResponse"];
export type BacktestDayRecord = components["schemas"]["BacktestDayRecord"];
export type BacktestSummary = components["schemas"]["BacktestSummary"];
export type BacktestSummaryResponse = components["schemas"]["BacktestSummaryResponse"];

export type MarketKey = "us" | "eu" | "africa";
export type MarketInfo = {
  key: MarketKey;
  label: string;
  region: string;
  endpointPrefix: "/swing" | "/swing_eu" | "/swing_africa";
  defaultNPerSide: number;
  benchmark: string;
};

export type MarketBacktestSummaryResponse = {
  summary: BacktestSummary;
  last_30_days?: BacktestDayRecord[];
};

type ApiResult<T> = {
  data?: T;
  error?: unknown;
  response: Response;
};

type NextFetchOptions = RequestInit & {
  next?: {
    revalidate?: number | false;
    tags?: string[];
  };
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient = createClient<paths>({
  baseUrl: apiBaseUrl,
});

const healthResponseSchema = z.object({
  status: z.string(),
  api_version: z.string(),
  data_files: z.record(z.string(), z.boolean()),
}) satisfies z.ZodType<HealthResponse>;

const dividendPickSchema = z.object({
  ticker: z.string(),
  yield: z.number(),
  payout_ratio: z.number(),
  div_cagr_5y: z.number(),
  consec_increases: z.number(),
  fcf_coverage: z.number(),
  safety_score: z.number(),
  composite_score: z.number(),
}) satisfies z.ZodType<DividendPick>;

const dividendPicksResponseSchema = z.object({
  generated_at: z.string().nullable().optional(),
  n_picks: z.number(),
  picks: z.array(dividendPickSchema),
}) satisfies z.ZodType<DividendPicksResponse>;

const swingPredictionSchema = z.object({
  timestamp: z.string(),
  symbol: z.string(),
  pred: z.number(),
  fwd_ret_5d: z.number().nullable().optional(),
}) satisfies z.ZodType<SwingPrediction>;

const swingPredictionsResponseSchema = z.object({
  as_of: z.string(),
  n_stocks: z.number(),
  long_picks: z.array(swingPredictionSchema),
  short_picks: z.array(swingPredictionSchema),
}) satisfies z.ZodType<SwingPredictionsResponse>;

const backtestDayRecordSchema = z.object({
  timestamp: z.string(),
  daily_ret_gross: z.number(),
  daily_ret_net: z.number(),
  long_ret: z.number(),
  short_ret: z.number(),
}) satisfies z.ZodType<BacktestDayRecord>;

const backtestSummarySchema = z.object({
  n_days: z.number(),
  start_date: z.string(),
  end_date: z.string(),
  ann_return_gross: z.number(),
  ann_return_net: z.number(),
  ann_vol: z.number(),
  sharpe_gross: z.number(),
  sharpe_net: z.number(),
  max_drawdown_net: z.number(),
  hit_rate_net: z.number(),
  total_return_net: z.number(),
}) satisfies z.ZodType<BacktestSummary>;

const backtestSummaryResponseSchema = z.object({
  summary: backtestSummarySchema,
  last_30_days: z.array(backtestDayRecordSchema),
}) satisfies z.ZodType<BacktestSummaryResponse>;

const marketBacktestSummaryResponseSchema = z.object({
  summary: backtestSummarySchema,
  last_30_days: z.array(backtestDayRecordSchema).optional(),
}) satisfies z.ZodType<MarketBacktestSummaryResponse>;

const liveFetch = createNextFetch({ cache: "no-store" });

export const markets: MarketInfo[] = [
  {
    key: "us",
    label: "United States",
    region: "S&P 500",
    endpointPrefix: "/swing",
    defaultNPerSide: 20,
    benchmark: "SPY",
  },
  {
    key: "eu",
    label: "Europe",
    region: "STOXX Europe 600",
    endpointPrefix: "/swing_eu",
    defaultNPerSide: 20,
    benchmark: "FEZ",
  },
  {
    key: "africa",
    label: "Africa",
    region: "JSE liquid universe",
    endpointPrefix: "/swing_africa",
    defaultNPerSide: 5,
    benchmark: "EZA",
  },
];

function createNextFetch(options: NextFetchOptions) {
  return (request: Request) => fetch(request, options);
}

async function readApiResponse<T>(result: ApiResult<T>, schema: z.ZodType<T>): Promise<T> {
  if (result.error !== undefined) {
    throw new Error(`API request failed with status ${result.response.status}`);
  }

  if (result.data === undefined) {
    throw new Error(`API request returned no data with status ${result.response.status}`);
  }

  return schema.parse(result.data);
}

async function fetchJson<T>(path: string, schema: z.ZodType<T>): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }
  return schema.parse(await response.json());
}

export async function getHealth(): Promise<HealthResponse> {
  const result = await apiClient.GET("/", {
    fetch: liveFetch,
  });
  return readApiResponse(result, healthResponseSchema);
}

export async function getDividendPicks(): Promise<DividendPicksResponse> {
  const result = await apiClient.GET("/dividend/picks", {
    fetch: liveFetch,
  });
  return readApiResponse(result, dividendPicksResponseSchema);
}

export async function getSwingLatestPredictions(nPerSide = 20): Promise<SwingPredictionsResponse> {
  const result = await apiClient.GET("/swing/predictions/latest", {
    params: { query: { n_per_side: nPerSide } },
    fetch: liveFetch,
  });
  return readApiResponse(result, swingPredictionsResponseSchema);
}

export async function getBacktestSummary(): Promise<BacktestSummaryResponse> {
  const result = await apiClient.GET("/swing/backtest", {
    fetch: liveFetch,
  });
  return readApiResponse(result, backtestSummaryResponseSchema);
}

export async function getMarketLatestPredictions(
  market: MarketInfo,
  nPerSide = market.defaultNPerSide,
): Promise<SwingPredictionsResponse> {
  if (market.key === "us") {
    return getSwingLatestPredictions(nPerSide);
  }

  return fetchJson(
    `${market.endpointPrefix}/predictions/latest?n_per_side=${nPerSide}`,
    swingPredictionsResponseSchema,
  );
}

export async function getMarketBacktestSummary(
  market: MarketInfo,
): Promise<MarketBacktestSummaryResponse> {
  if (market.key === "us") {
    return getBacktestSummary();
  }

  return fetchJson(`${market.endpointPrefix}/backtest`, marketBacktestSummaryResponseSchema);
}

export async function getAllMarketSnapshots(nPerSide = 5) {
  return Promise.all(
    markets.map(async (market) => {
      const [predictions, backtest] = await Promise.all([
        getMarketLatestPredictions(market, Math.min(nPerSide, market.defaultNPerSide)),
        getMarketBacktestSummary(market),
      ]);

      return { market, predictions, backtest };
    }),
  );
}

export function topDividendPicks(picks: DividendPick[], count: number): DividendPick[] {
  return [...picks]
    .sort((left, right) => right.composite_score - left.composite_score)
    .slice(0, count);
}
