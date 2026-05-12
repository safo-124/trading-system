"use client";

import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";
import type { Route } from "next";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { StockTableRow } from "@/lib/api/client";
import { formatNumber, toNumber } from "@/lib/utils";

type SortKey = "ticker" | "dividendYield" | "payoutRatio" | "cutProbability" | "compositeScore";
type SortDirection = "asc" | "desc";

const columns: { key: SortKey; label: string; align?: "right" }[] = [
  { key: "ticker", label: "Ticker" },
  { key: "dividendYield", label: "Yield", align: "right" },
  { key: "payoutRatio", label: "Payout", align: "right" },
  { key: "cutProbability", label: "Cut Prob.", align: "right" },
  { key: "compositeScore", label: "Score", align: "right" },
];

export function StocksTable({ rows }: { rows: StockTableRow[] }) {
  const router = useRouter();
  const [sortKey, setSortKey] = useState<SortKey>("compositeScore");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  const sortedRows = useMemo(() => {
    return [...rows].sort((left, right) => {
      const leftValue = sortableValue(left, sortKey);
      const rightValue = sortableValue(right, sortKey);
      const direction = sortDirection === "asc" ? 1 : -1;

      if (typeof leftValue === "number" && typeof rightValue === "number") {
        return (leftValue - rightValue) * direction;
      }

      return String(leftValue).localeCompare(String(rightValue)) * direction;
    });
  }, [rows, sortDirection, sortKey]);

  function setSort(nextKey: SortKey) {
    if (nextKey === sortKey) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
      return;
    }

    setSortKey(nextKey);
    setSortDirection(nextKey === "ticker" ? "asc" : "desc");
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map((column) => (
            <TableHead
              className={column.align === "right" ? "text-right" : undefined}
              key={column.key}
            >
              <button
                className="inline-flex items-center gap-1 text-muted-foreground transition-colors hover:text-foreground"
                onClick={() => setSort(column.key)}
                type="button"
              >
                {column.label}
                {sortKey === column.key ? (
                  sortDirection === "asc" ? (
                    <ArrowUp className="size-3" />
                  ) : (
                    <ArrowDown className="size-3" />
                  )
                ) : (
                  <ChevronsUpDown className="size-3" />
                )}
              </button>
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortedRows.map((row) => (
          <TableRow
            className="cursor-pointer"
            key={row.ticker}
            onClick={() => router.push(`/stocks/${row.ticker}` as Route)}
          >
            <TableCell>
              <div className="font-semibold">{row.ticker}</div>
              <div className="text-muted-foreground text-xs">{row.name ?? row.sector ?? "—"}</div>
            </TableCell>
            <NumericCell>{formatNumber(row.dividendYield, { style: "percent" })}</NumericCell>
            <NumericCell>{formatNumber(row.payoutRatio, { style: "percent" })}</NumericCell>
            <NumericCell className="text-red-400">
              {formatNumber(row.cutProbability, { style: "percent" })}
            </NumericCell>
            <NumericCell className="text-emerald-400">
              {formatNumber(row.compositeScore)}
            </NumericCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function NumericCell({ children, className }: { children: string; className?: string }) {
  return <TableCell className={`text-right font-mono ${className ?? ""}`}>{children}</TableCell>;
}

function sortableValue(row: StockTableRow, key: SortKey): string | number {
  if (key === "ticker") {
    return row.ticker;
  }

  return toNumber(row[key]) ?? Number.NEGATIVE_INFINITY;
}
