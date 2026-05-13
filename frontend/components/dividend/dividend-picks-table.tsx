"use client";

import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";
import { useMemo, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { DividendPick } from "@/lib/api/client";
import { formatNumber } from "@/lib/utils";

type SortKey =
  | "ticker"
  | "yield"
  | "payout_ratio"
  | "div_cagr_5y"
  | "safety_score"
  | "composite_score";
type SortDirection = "asc" | "desc";

const columns: { key: SortKey; label: string; align?: "right" }[] = [
  { key: "ticker", label: "Ticker" },
  { key: "yield", label: "Yield", align: "right" },
  { key: "payout_ratio", label: "Payout", align: "right" },
  { key: "div_cagr_5y", label: "5Y CAGR", align: "right" },
  { key: "safety_score", label: "Safety", align: "right" },
  { key: "composite_score", label: "Score", align: "right" },
];

export function DividendPicksTable({ picks }: { picks: DividendPick[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("composite_score");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  const sortedPicks = useMemo(() => {
    return [...picks].sort((left, right) => {
      const direction = sortDirection === "asc" ? 1 : -1;
      const leftValue = left[sortKey];
      const rightValue = right[sortKey];

      if (typeof leftValue === "number" && typeof rightValue === "number") {
        return (leftValue - rightValue) * direction;
      }

      return String(leftValue).localeCompare(String(rightValue)) * direction;
    });
  }, [picks, sortDirection, sortKey]);

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
        {sortedPicks.map((pick) => (
          <TableRow key={pick.ticker}>
            <TableCell>
              <div className="font-semibold">{pick.ticker}</div>
              <div className="text-muted-foreground text-xs">
                {pick.consec_increases} consecutive increases
              </div>
            </TableCell>
            <NumericCell>{formatNumber(pick.yield, { style: "percent" })}</NumericCell>
            <NumericCell>{formatNumber(pick.payout_ratio, { style: "percent" })}</NumericCell>
            <NumericCell>{formatNumber(pick.div_cagr_5y, { style: "percent" })}</NumericCell>
            <NumericCell className="text-emerald-400">
              {formatNumber(pick.safety_score, { maximumFractionDigits: 2 })}
            </NumericCell>
            <NumericCell className="text-emerald-400">
              {formatNumber(pick.composite_score, { maximumFractionDigits: 3 })}
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
