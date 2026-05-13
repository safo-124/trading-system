import { redirect } from "next/navigation";

type StockDetailPageProps = {
  params: Promise<{ ticker: string }>;
};

export default async function StockDetailPage({ params }: StockDetailPageProps) {
  await params;
  redirect("/dividend");
}
