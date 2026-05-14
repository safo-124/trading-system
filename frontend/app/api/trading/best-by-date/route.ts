import { NextResponse } from "next/server";
import { bestPickByDateResponseSchema } from "@/lib/api/client";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const date = url.searchParams.get("date");

  if (!date) {
    return NextResponse.json({ detail: "Missing date query parameter" }, { status: 400 });
  }

  const response = await fetch(`${apiBaseUrl}/swing/best_by_date?date=${date}`, {
    cache: "no-store",
  });
  const payload = await response.json();

  if (!response.ok) {
    return NextResponse.json(payload, { status: response.status });
  }

  return NextResponse.json(bestPickByDateResponseSchema.parse(payload));
}
