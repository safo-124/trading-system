"""
Long-short backtest for the cross-sectional mean-reversion strategy.

Methodology: daily rebalance, 5-day overlapping holds, equal-weight,
dollar-neutral. Reports both frictionless and after-cost results.

Output:
- Equity curves (NAV over time)
- Annualized Sharpe ratio
- Max drawdown
- Year-by-year returns
- EZA benchmark comparison

Conventions:
- Returns are decimal (0.01 = 1%)
- Cost is per leg, one-way: 3 bps default
- 'Long-short' return = (long_leg_return - short_leg_return) / 2
  (Average so we can compare to EZA on a similar volatility scale.)
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # no GUI; just save PNGs
import matplotlib.pyplot as plt

from swing_africa.config import DATA_DIR


# Strategy params
N_PER_SIDE = 5   # JSE: 63 stocks, top/bottom 5 is ~8% each side
HOLD_DAYS = 5
COST_BPS_PER_LEG_ONE_WAY = 3  # 3 basis points per leg per trade direction


# ---------------------------------------------------------------
# CORE: portfolio construction
# ---------------------------------------------------------------

def daily_portfolio_returns(
    predictions: pd.DataFrame,
    n_per_side: int = N_PER_SIDE,
    hold_days: int = HOLD_DAYS,
) -> pd.DataFrame:
    """
    For each day, pick top/bottom N by model prediction.
    Compute the long-short return realized over the next HOLD_DAYS days.
    
    Returns DataFrame with: timestamp, long_ret, short_ret, ls_ret, n_long, n_short
    
    IMPORTANT: realized returns use fwd_ret_5d which was the model's target.
    This is a HOLD-5-DAYS strategy with overlapping positions.
    """
    # Sanity filter: drop rows with implausible 5-day returns.
    # A real 5-day return rarely exceeds 100% or drops below -50%.
    # Values outside [-50%, +200%] are almost always data errors 
    # (unadjusted splits, stale prices, etc.)
    before = len(predictions)
    predictions = predictions[
        (predictions["fwd_ret_5d"] > -0.50)
        & (predictions["fwd_ret_5d"] < 2.00)
    ].copy()
    after = len(predictions)
    if after < before:
        print(f"  Filtered {before - after:,} rows with implausible returns "
              f"({100*(before-after)/before:.2f}% of total)")

    out_rows = []
    
    # Sort once
    predictions = predictions.sort_values(["timestamp", "pred"]).reset_index(drop=True)
    
    # Group by day
    for ts, day in predictions.groupby("timestamp"):
        if len(day) < 2 * n_per_side:
            continue
        # Model predicts the forward return rank: high pred = high future return.
        # Diagnostic confirmed Spearman(pred, fwd_ret_5d) = +0.010 (positive).
        # So LONG the highest predictions, SHORT the lowest predictions.
        long_leg = day.nlargest(n_per_side, "pred")
        short_leg = day.nsmallest(n_per_side, "pred")
        
        # Use fwd_ret_5d (the model's target horizon) as the realized return
        long_ret = long_leg["fwd_ret_5d"].mean()
        short_ret = short_leg["fwd_ret_5d"].mean()
        
        # Long-short: long the longs, short the shorts. We average so the
        # vol is on a per-leg basis (comparable to long-only benchmarks).
        ls_ret = (long_ret - short_ret) / 2
        
        out_rows.append({
            "timestamp": ts,
            "long_ret": long_ret,
            "short_ret": short_ret,
            "ls_ret_5d": ls_ret,
            "n_long": len(long_leg),
            "n_short": len(short_leg),
        })
    
    df = pd.DataFrame(out_rows)
    
    # Convert 5-day overlapping returns to daily contributions:
    # Each day we open new positions. With 5-day hold and daily rebal,
    # 1/5 of capital rotates each day. Daily P&L = 1/5 * ls_ret_5d
    # of THAT day's new positions, plus the contributions of positions
    # opened 1-4 days ago. In aggregate (steady-state) daily return is
    # just ls_ret_5d / 5.
    df["daily_ret_gross"] = df["ls_ret_5d"] / hold_days
    
    return df


def apply_costs(
    df: pd.DataFrame,
    n_per_side: int = N_PER_SIDE,
    hold_days: int = HOLD_DAYS,
    cost_bps_per_leg_one_way: float = COST_BPS_PER_LEG_ONE_WAY,
) -> pd.DataFrame:
    """
    Apply transaction costs.
    
    Each day: 1/hold_days of the portfolio rotates (closing old + opening new).
    Per rotation, we pay one-way cost on BOTH legs (long and short),
    on both the close and the open = 4x one-way cost on the rotated capital.
    
    Daily cost as fraction of capital = (4 * cost_bps / 10000) * (1 / hold_days)
    """
    df = df.copy()
    daily_cost = (4 * cost_bps_per_leg_one_way / 10000.0) / hold_days
    df["daily_ret_net"] = df["daily_ret_gross"] - daily_cost
    df["daily_cost"] = daily_cost
    return df


# ---------------------------------------------------------------
# METRICS
# ---------------------------------------------------------------

def compute_metrics(daily_returns: pd.Series, label: str = "") -> dict:
    """Standard performance metrics."""
    r = daily_returns.dropna()
    if len(r) == 0:
        return {"label": label}
    
    ann_ret = r.mean() * 252
    ann_vol = r.std() * np.sqrt(252)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
    
    # Drawdown
    nav = (1 + r).cumprod()
    peak = nav.cummax()
    dd = (nav - peak) / peak
    max_dd = dd.min()
    
    # Hit rate
    hit_rate = (r > 0).mean()
    
    # Total return
    total_ret = nav.iloc[-1] - 1
    
    return {
        "label": label,
        "n_days": len(r),
        "ann_return": ann_ret,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "max_dd": max_dd,
        "hit_rate": hit_rate,
        "total_return": total_ret,
    }


def yearly_returns(daily_returns: pd.Series) -> pd.DataFrame:
    """Year-by-year compounded returns."""
    df = pd.DataFrame({"ret": daily_returns})
    df["year"] = pd.to_datetime(df.index).year
    yearly = df.groupby("year")["ret"].apply(lambda x: (1 + x).prod() - 1)
    return yearly.to_frame("annual_return")


# ---------------------------------------------------------------
# BENCHMARK (EZA)
# ---------------------------------------------------------------

def load_benchmark_returns(start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Load EZA (iShares MSCI South Africa ETF) as JSE benchmark."""
    import yfinance as yf
    eza = yf.Ticker("EZA").history(
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        auto_adjust=True,
    )["Close"]
    return eza.pct_change().dropna()


# ---------------------------------------------------------------
# PLOTTING
# ---------------------------------------------------------------

def plot_equity_curves(
    gross: pd.Series,
    net: pd.Series,
    benchmark: pd.Series,
    out_path: Path,
) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Top: equity curves
    ax = axes[0]
    (1 + gross).cumprod().plot(ax=ax, label="L/S Gross (no costs)", color="green")
    (1 + net).cumprod().plot(ax=ax, label="L/S Net (3 bps)", color="blue")
    (1 + benchmark).cumprod().plot(ax=ax, label="EZA (long only)", color="gray", alpha=0.7)
    ax.set_title("Equity Curves (starting NAV = 1)")
    ax.set_ylabel("NAV")
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Bottom: drawdowns
    ax = axes[1]
    for ret, label, color in [(gross, "Gross", "green"), (net, "Net", "blue"), (benchmark, "EZA", "gray")]:
        nav = (1 + ret).cumprod()
        dd = (nav - nav.cummax()) / nav.cummax()
        dd.plot(ax=ax, label=label, color=color, alpha=0.7)
    ax.set_title("Drawdowns")
    ax.set_ylabel("Drawdown")
    ax.legend()
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=100)
    plt.close()


# ---------------------------------------------------------------
# DRIVER
# ---------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path",
                        default=str(DATA_DIR / "predictions.parquet"))
    parser.add_argument("--n-per-side", type=int, default=N_PER_SIDE)
    parser.add_argument("--cost-bps", type=float, default=COST_BPS_PER_LEG_ONE_WAY)
    args = parser.parse_args()
    
    in_path = Path(args.in_path)
    if not in_path.exists():
        print(f"ERROR: {in_path} not found. Run swing/train.py first.")
        return 1
    
    print(f"Loading predictions from {in_path}")
    preds = pd.read_parquet(in_path)
    print(f"  shape: {preds.shape}")
    print(f"  date range: {preds['timestamp'].min().date()} to {preds['timestamp'].max().date()}")
    
    print(f"\nStrategy: top/bottom {args.n_per_side} by prediction")
    print(f"  Hold period: {HOLD_DAYS} days")
    print(f"  Cost: {args.cost_bps} bps per leg one-way")
    
    print("\nComputing portfolio returns...")
    pf = daily_portfolio_returns(preds, n_per_side=args.n_per_side, hold_days=HOLD_DAYS)
    pf = apply_costs(pf, n_per_side=args.n_per_side, hold_days=HOLD_DAYS,
                     cost_bps_per_leg_one_way=args.cost_bps)
    
    # Set timestamp as index for time-series ops
    pf = pf.set_index("timestamp").sort_index()
    pf.index = pd.to_datetime(pf.index)
    
    print(f"  Trading days: {len(pf)}")
    print(f"  Avg daily gross return: {pf['daily_ret_gross'].mean() * 1e4:.2f} bps")
    print(f"  Avg daily cost:         {pf['daily_cost'].iloc[0] * 1e4:.2f} bps")
    print(f"  Avg daily net return:   {pf['daily_ret_net'].mean() * 1e4:.2f} bps")
    
    # Metrics
    print("\n" + "=" * 70)
    print("PERFORMANCE METRICS")
    print("=" * 70)
    
    m_gross = compute_metrics(pf["daily_ret_gross"], "L/S Gross")
    m_net = compute_metrics(pf["daily_ret_net"], "L/S Net (3 bps)")
    
    # EZA benchmark (South Africa ETF)
    print("\nLoading EZA benchmark...")
    bench_ret = load_benchmark_returns(pf.index.min(), pf.index.max())
    bench_ret.index = pd.to_datetime(bench_ret.index).tz_localize(None) if bench_ret.index.tz is not None else pd.to_datetime(bench_ret.index)
    bench_ret = bench_ret.reindex(pf.index, method="ffill").dropna()
    m_bench = compute_metrics(bench_ret, "EZA")
    
    metrics_df = pd.DataFrame([m_gross, m_net, m_bench])
    print(metrics_df.to_string(index=False, formatters={
        "ann_return": "{:+.2%}".format,
        "ann_vol": "{:.2%}".format,
        "sharpe": "{:+.2f}".format,
        "max_dd": "{:.2%}".format,
        "hit_rate": "{:.2%}".format,
        "total_return": "{:+.1%}".format,
    }))
    
    # Yearly breakdown
    print("\n" + "=" * 70)
    print("YEAR-BY-YEAR (Net of costs)")
    print("=" * 70)
    yearly_net = yearly_returns(pf["daily_ret_net"])
    yearly_bench = yearly_returns(bench_ret).rename(columns={"annual_return": "eza_return"})
    yearly = yearly_net.rename(columns={"annual_return": "ls_net_return"}).join(yearly_bench)
    yearly["excess"] = yearly["ls_net_return"] - yearly["eza_return"]
    print(yearly.to_string(formatters={
        "ls_net_return": "{:+.2%}".format,
        "eza_return": "{:+.2%}".format,
        "excess": "{:+.2%}".format,
    }))
    
    # Save outputs
    out_csv = DATA_DIR / "backtest_results.csv"
    pf.to_csv(out_csv)
    print(f"\n  Daily returns saved to: {out_csv}")
    
    out_png = DATA_DIR / "backtest_equity.png"
    try:
        plot_equity_curves(
            pf["daily_ret_gross"],
            pf["daily_ret_net"],
            bench_ret,
            out_png,
        )
        print(f"  Equity curve plot saved to: {out_png}")
    except Exception as e:
        print(f"  [plot failed: {e}]")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
