import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type NumberLike = number | string | null | undefined;

type NumberFormatStyle = "number" | "percent" | "currency" | "compact";

type FormatNumberOptions = {
  style?: NumberFormatStyle;
  maximumFractionDigits?: number;
  minimumFractionDigits?: number;
  currency?: string;
};

export function toNumber(value: NumberLike): number | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatNumber(value: NumberLike, options: FormatNumberOptions = {}): string {
  const parsed = toNumber(value);
  if (parsed === null) {
    return "—";
  }

  const {
    style = "number",
    maximumFractionDigits = style === "currency" || style === "compact" ? 1 : 2,
    minimumFractionDigits = 0,
    currency = "USD",
  } = options;

  if (style === "percent") {
    return new Intl.NumberFormat("en-US", {
      style: "percent",
      maximumFractionDigits,
      minimumFractionDigits,
    }).format(parsed);
  }

  if (style === "currency") {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      notation: "compact",
      maximumFractionDigits,
      minimumFractionDigits,
    }).format(parsed);
  }

  if (style === "compact") {
    return new Intl.NumberFormat("en-US", {
      notation: "compact",
      maximumFractionDigits,
      minimumFractionDigits,
    }).format(parsed);
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits,
    minimumFractionDigits,
  }).format(parsed);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

export function formatSignedPercent(value: NumberLike, maximumFractionDigits = 2): string {
  const parsed = toNumber(value);
  if (parsed === null) {
    return "—";
  }

  const formatted = formatNumber(Math.abs(parsed), {
    style: "percent",
    maximumFractionDigits,
    minimumFractionDigits: Math.min(2, maximumFractionDigits),
  });

  return `${parsed >= 0 ? "+" : "-"}${formatted}`;
}

export function formatBps(value: NumberLike): string {
  const parsed = toNumber(value);
  if (parsed === null) {
    return "—";
  }

  return `${formatNumber(parsed * 10_000, {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  })} bps`;
}
