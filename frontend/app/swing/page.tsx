import { StrategyTerminal } from "@/components/swing/strategy-terminal";
import { Badge } from "@/components/ui/badge";
import { getAllMarketSnapshots } from "@/lib/api/client";
import { formatDate } from "@/lib/utils";

export default async function SwingPage() {
  const snapshots = await getAllMarketSnapshots(30);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <h1 className="font-semibold text-2xl tracking-tight">Global Swing</h1>
          <p className="text-muted-foreground text-sm">
            A full strategy terminal for US, Europe, and JSE long-short books.
          </p>
        </div>
        <Badge className="w-fit" variant="secondary">
          {snapshots.map((snapshot) => formatDate(snapshot.predictions.as_of)).join(" · ")}
        </Badge>
      </div>

      <StrategyTerminal snapshots={snapshots} />
    </div>
  );
}
