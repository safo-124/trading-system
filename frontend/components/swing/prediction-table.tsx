import { StockIdentity } from "@/components/stocks/stock-identity";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { SwingPrediction } from "@/lib/api/client";
import { formatNumber, formatSignedPercent } from "@/lib/utils";

export function PredictionTable({
  picks,
  side,
}: {
  picks: SwingPrediction[];
  side: "long" | "short";
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Company</TableHead>
          <TableHead className="text-right">Pred</TableHead>
          <TableHead className="text-right">Forward 5D</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {picks.map((pick) => (
          <TableRow key={`${side}-${pick.symbol}`}>
            <TableCell>
              <div className="flex items-center gap-2">
                <StockIdentity dense symbol={pick.symbol} />
                <Badge
                  className={
                    side === "long"
                      ? "bg-emerald-500/15 text-emerald-300"
                      : "bg-red-500/15 text-red-300"
                  }
                  variant="secondary"
                >
                  {side}
                </Badge>
              </div>
            </TableCell>
            <TableCell className="text-right font-mono">
              {formatNumber(pick.pred, { maximumFractionDigits: 4 })}
            </TableCell>
            <TableCell className="text-right font-mono">
              {formatSignedPercent(pick.fwd_ret_5d)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
