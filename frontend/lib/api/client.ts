import createClient from "openapi-fetch";
import { z } from "zod";
import type { components, paths } from "@/lib/api/schema";
import { type NumberLike, toNumber } from "@/lib/utils";

export type Stock = components["schemas"]["StockSchema"];
export type Fundamental = components["schemas"]["FundamentalSchema"];
export type Dividend = components["schemas"]["DividendHistorySchema"];
export type RankedPick = components["schemas"]["RankedPickResponse"];
export type StockListResponse = components["schemas"]["StockListResponse"];
export type StockDetailResponse = components["schemas"]["StockDetailResponse"];
export type DividendHistoryResponse = components["schemas"]["DividendHistoryResponse"];
export type PipelineRunResponse = components["schemas"]["PipelineRunResponse"];
export type LatestPredictionsResponse = components["schemas"]["LatestPredictionsResponse"];

export type StockTableRow = {
  ticker: string;
  name: string | null;
  sector: string | null;
  marketCap: number | null;
  dividendYield: NumberLike;
  payoutRatio: NumberLike;
  cutProbability: NumberLike;
  compositeScore: NumberLike;
  recommendation: string | null;
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

const numberLikeSchema = z.union([z.number(), z.string()]);
const nullableNumberLikeSchema = numberLikeSchema.nullable();

const stockSchema = z.object({
  ticker: z.string(),
  name: z.string().nullable(),
  sector: z.string().nullable(),
  market_cap: z.number().nullable(),
  last_updated: z.string().nullable(),
}) satisfies z.ZodType<Stock>;

const fundamentalSchema = z.object({
  id: z.number().nullable(),
  ticker: z.string(),
  as_of_date: z.string(),
  yield: nullableNumberLikeSchema,
  payout_ratio: nullableNumberLikeSchema,
  fcf: nullableNumberLikeSchema,
  debt_to_equity: nullableNumberLikeSchema,
  roe: nullableNumberLikeSchema,
  profit_margin: nullableNumberLikeSchema,
}) satisfies z.ZodType<Fundamental>;

const dividendSchema = z.object({
  id: z.number().nullable(),
  ticker: z.string(),
  ex_date: z.string(),
  amount: numberLikeSchema,
  currency: z.string(),
}) satisfies z.ZodType<Dividend>;

const rankedPickSchema = z.object({
  rank: z.number(),
  ticker: z.string(),
  model_version: z.string(),
  predicted_at: z.string(),
  cut_probability: numberLikeSchema,
  composite_score: numberLikeSchema,
  recommendation: z.string(),
}) satisfies z.ZodType<RankedPick>;

const stockListResponseSchema = z.object({
  stocks: z.array(stockSchema),
}) satisfies z.ZodType<StockListResponse>;

const stockDetailResponseSchema = z.object({
  stock: stockSchema,
  latest_fundamentals: fundamentalSchema.nullable(),
}) satisfies z.ZodType<StockDetailResponse>;

const dividendHistoryResponseSchema = z.object({
  ticker: z.string(),
  dividends: z.array(dividendSchema),
}) satisfies z.ZodType<DividendHistoryResponse>;

const pipelineRunResponseSchema = z.object({
  model_version: z.string(),
  predicted_at: z.string(),
  picks: z.array(rankedPickSchema),
}) satisfies z.ZodType<PipelineRunResponse>;

const latestPredictionsResponseSchema = z.object({
  predictions: z.array(rankedPickSchema),
}) satisfies z.ZodType<LatestPredictionsResponse>;

const liveFetch = createNextFetch({ cache: "no-store" });

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

export async function getStocks(): Promise<StockListResponse> {
  const result = await apiClient.GET("/api/stocks", {
    fetch: liveFetch,
  });
  return readApiResponse(result, stockListResponseSchema);
}

export async function getStockDetail(ticker: string): Promise<StockDetailResponse> {
  const result = await apiClient.GET("/api/stocks/{ticker}", {
    params: { path: { ticker } },
    fetch: liveFetch,
  });
  return readApiResponse(result, stockDetailResponseSchema);
}

export async function getDividendHistory(ticker: string): Promise<DividendHistoryResponse> {
  const result = await apiClient.GET("/api/stocks/{ticker}/dividends", {
    params: { path: { ticker } },
    fetch: liveFetch,
  });
  return readApiResponse(result, dividendHistoryResponseSchema);
}

export async function getLatestPredictions(): Promise<LatestPredictionsResponse> {
  const result = await apiClient.GET("/api/predictions/latest", {
    fetch: liveFetch,
  });
  return readApiResponse(result, latestPredictionsResponseSchema);
}

export async function runPipeline(): Promise<PipelineRunResponse> {
  const result = await apiClient.POST("/api/pipeline/run");
  return readApiResponse(result, pipelineRunResponseSchema);
}

export async function getStockTableRows(): Promise<StockTableRow[]> {
  const [stockList, latestPredictions] = await Promise.all([getStocks(), getLatestPredictions()]);
  const predictionByTicker = new Map(
    latestPredictions.predictions.map((prediction) => [prediction.ticker, prediction]),
  );

  const details = await Promise.all(
    stockList.stocks.map(async (stock) => {
      try {
        return await getStockDetail(stock.ticker);
      } catch {
        return { stock, latest_fundamentals: null } satisfies StockDetailResponse;
      }
    }),
  );

  return details.map((detail) => {
    const prediction = predictionByTicker.get(detail.stock.ticker);

    return {
      ticker: detail.stock.ticker,
      name: detail.stock.name,
      sector: detail.stock.sector,
      marketCap: detail.stock.market_cap,
      dividendYield: detail.latest_fundamentals?.yield ?? null,
      payoutRatio: detail.latest_fundamentals?.payout_ratio ?? null,
      cutProbability: prediction?.cut_probability ?? null,
      compositeScore: prediction?.composite_score ?? null,
      recommendation: prediction?.recommendation ?? null,
    };
  });
}

export function getPickForTicker(
  predictions: LatestPredictionsResponse,
  ticker: string,
): RankedPick | null {
  return (
    predictions.predictions.find(
      (prediction) => prediction.ticker.toUpperCase() === ticker.toUpperCase(),
    ) ?? null
  );
}

export function sortPicksByScore(picks: RankedPick[]): RankedPick[] {
  return [...picks].sort((left, right) => {
    const rightScore = toNumber(right.composite_score) ?? 0;
    const leftScore = toNumber(left.composite_score) ?? 0;
    return rightScore - leftScore || left.ticker.localeCompare(right.ticker);
  });
}
