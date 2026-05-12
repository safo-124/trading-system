import { StocksTable } from "@/components/stocks/stocks-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getStockTableRows } from "@/lib/api/client";

export default async function StocksPage() {
  const rows = await getStockTableRows();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-semibold text-2xl tracking-tight">Stocks</h1>
        <p className="text-muted-foreground text-sm">Ingested universe with latest fundamentals.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Universe</CardTitle>
        </CardHeader>
        <CardContent>
          <StocksTable rows={rows} />
        </CardContent>
      </Card>
    </div>
  );
}
