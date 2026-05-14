import { NextResponse } from "next/server";
import { livePredictionResponseSchema, type MarketKey, marketByKey } from "@/lib/api/client";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET(request: Request, context: { params: Promise<{ market: string }> }) {
  const { market } = await context.params;
  if (!isMarketKey(market)) {
    return NextResponse.json({ detail: "Unknown market" }, { status: 404 });
  }

  const url = new URL(request.url);
  const nPerSide =
    url.searchParams.get("n_per_side") ?? String(marketByKey[market].defaultNPerSide);
  const forceRefresh = url.searchParams.get("force_refresh") ?? "false";
  const upstreamUrl = `${apiBaseUrl}${marketByKey[market].endpointPrefix}/predict_today?n_per_side=${nPerSide}&force_refresh=${forceRefresh}`;

  const response = await fetch(upstreamUrl, { cache: "no-store" });
  const payload = await response.json();

  if (!response.ok) {
    return NextResponse.json(payload, { status: response.status });
  }

  return NextResponse.json(livePredictionResponseSchema.parse(payload));
}

function isMarketKey(value: string): value is MarketKey {
  return value === "us" || value === "eu" || value === "africa";
}
