"use client";

import { Building2 } from "lucide-react";
import Image from "next/image";
import { useState } from "react";
import { getLogoUrl, getStockMetadata } from "@/lib/stock-metadata";
import { cn } from "@/lib/utils";

export function StockIdentity({
  symbol,
  dense = false,
  logoClassName,
}: {
  symbol: string;
  dense?: boolean;
  logoClassName?: string;
}) {
  const metadata = getStockMetadata(symbol);

  return (
    <div className="flex min-w-0 items-center gap-3">
      <StockLogo className={logoClassName} symbol={symbol} />
      <div className="min-w-0">
        <div className="flex min-w-0 items-center gap-2">
          <span className="truncate font-semibold">{symbol}</span>
          {!dense && (
            <span className="shrink-0 rounded-md border border-border/70 px-1.5 py-0.5 text-muted-foreground text-[0.68rem]">
              {metadata.exchange}
            </span>
          )}
        </div>
        <div className="truncate text-muted-foreground text-xs">{metadata.name}</div>
      </div>
    </div>
  );
}

export function StockLogo({ symbol, className }: { symbol: string; className?: string }) {
  const [failed, setFailed] = useState(false);
  const logoUrl = getLogoUrl(symbol);
  const metadata = getStockMetadata(symbol);
  const initials = metadata.name
    .split(/\s+/u)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  return (
    <div
      className={cn(
        "relative flex size-9 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-secondary text-secondary-foreground ring-1 ring-border",
        className,
      )}
    >
      {logoUrl && !failed ? (
        <Image
          alt={`${metadata.name} logo`}
          className="size-full object-contain p-1.5"
          height={36}
          src={logoUrl}
          unoptimized
          width={36}
          onError={() => setFailed(true)}
        />
      ) : (
        <span className="font-semibold text-xs">
          {initials || <Building2 className="size-4" />}
        </span>
      )}
    </div>
  );
}
