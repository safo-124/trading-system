import { Activity, BarChart3, Landmark, LineChart, ShieldCheck } from "lucide-react";
import Link from "next/link";

const navItems = [
  { href: "/" as const, label: "Dashboard", icon: Activity },
  { href: "/dividend" as const, label: "Dividend", icon: ShieldCheck },
  { href: "/swing" as const, label: "Global Swing", icon: Landmark },
  { href: "/backtest" as const, label: "Backtest", icon: BarChart3 },
];

export function Sidebar() {
  return (
    <aside className="border-border/70 border-r bg-sidebar/60 px-4 py-5">
      <div className="mb-8 flex items-center gap-2">
        <div className="flex size-8 items-center justify-center rounded-lg bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/25">
          <LineChart className="size-4" />
        </div>
        <div>
          <div className="font-semibold text-sm">Trading System</div>
          <div className="font-mono text-muted-foreground text-xs">research dashboard</div>
        </div>
      </div>

      <nav className="grid gap-1">
        {navItems.map((item) => {
          const Icon = item.icon;

          return (
            <Link
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-muted-foreground text-sm transition-colors hover:bg-accent hover:text-foreground"
              href={item.href}
              key={item.href}
            >
              <Icon className="size-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
