"use client";

import { DividendPicksTable } from "@/components/dividend/dividend-picks-table";
import type { DividendPick } from "@/lib/api/client";

export function StocksTable({ rows }: { rows: DividendPick[] }) {
  return <DividendPicksTable picks={rows} />;
}
