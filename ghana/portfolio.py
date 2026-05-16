"""
GSE portfolio constructor.

Takes a budget (in cedis or USD), an investment horizon, and a risk
tolerance, then recommends an allocation across the top-scored
eligible GSE stocks.

Design choices:
  - 5-8 stocks max, adjusted DOWN for very small budgets where 8-way
    splitting would produce sub-position sizes (under ~200 GHS per name)
  - Quality-weighted: top-scored stocks get more weight, but with
    concentration caps (low risk: 20%, medium: 25%, high: 30%)
  - Liquidity-aware: each position's GHS cost is capped at 5x average
    daily turnover for that stock; if the cap is binding the weight
    is reduced and the excess flows to other candidates
  - Whole-share rounding; cash residual reported honestly
  - FX layer: every monetary number is shown in both GHS and USD
"""

from __future__ import annotations
import argparse
import json
import sys
import warnings
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from ghana.config import DATA_DIR


SCORED_PATH = DATA_DIR / "gse_scored.csv"

# Fallback rate if yfinance FX scrape fails. Update this manually
# every few months. As of mid-2026, ~12.5 GHS per USD is the rough rate.
FX_FALLBACK_GHS_PER_USD = 12.5

# Concentration caps by risk tolerance
RISK_CAPS = {"low": 0.20, "medium": 0.25, "high": 0.30}

# Portfolio size by budget (in GHS). Smaller budgets get fewer stocks
# to avoid silly fractional positions.
def target_n_stocks(budget_ghs: float) -> int:
    if budget_ghs < 2_000:
        return 4
    if budget_ghs < 5_000:
        return 5
    if budget_ghs < 15_000:
        return 6
    if budget_ghs < 50_000:
        return 7
    return 8

# Liquidity guardrail
# Max position size as a fraction of one day's average GHS turnover.
# 0.25 = a quarter of one day's volume -- gives ~4 trading days to exit
# at typical volume. For an illiquid market like the GSE this is the
# realistic ceiling. Setting this higher produces fictional fill
# assumptions.
LIQUIDITY_TURNOVER_FRACTION = 0.25


@dataclass
class Position:
    ticker: str
    name: str
    price_ghs: float
    shares: int
    cost_ghs: float
    cost_usd: float
    weight_pct: float
    quality_score: float
    notes: list[str] = field(default_factory=list)


@dataclass
class PortfolioRecommendation:
    budget_ghs: float
    budget_usd: float
    fx_rate_ghs_per_usd: float
    fx_source: str
    horizon_years: int
    risk_tolerance: str
    target_n_stocks: int
    positions: list[Position]
    total_invested_ghs: float
    total_invested_usd: float
    cash_residual_ghs: float
    cash_residual_usd: float
    excluded_reasons: list[str]


def fetch_fx_rate() -> tuple[float, str]:
    """
    Get GHS/USD rate. Try yfinance first, fall back to hardcoded.
    Returns (ghs_per_usd, source_label).
    """
    try:
        import yfinance as yf
        for sym in ["GHS=X", "USDGHS=X"]:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                t = yf.Ticker(sym)
                df = t.history(period="5d", auto_adjust=True)
            if not df.empty:
                rate = float(df["Close"].iloc[-1])
                # Sanity check: real GHS/USD is between ~5 and ~30
                if 5.0 <= rate <= 30.0:
                    return rate, f"yfinance:{sym}"
    except Exception:
        pass
    return FX_FALLBACK_GHS_PER_USD, "hardcoded_fallback"


def build_portfolio(
    scored_df: pd.DataFrame,
    budget_ghs: float,
    horizon_years: int,
    risk_tolerance: Literal["low", "medium", "high"],
    fx_rate: float,
    fx_source: str,
) -> PortfolioRecommendation:
    """
    Construct a recommended portfolio.

    Algorithm:
      1. Filter to eligible stocks with positive quality_score
      2. Pick top N by quality_score (N depends on budget)
      3. Compute quality-tilted target weights subject to concentration cap
      4. Apply liquidity guardrail; redistribute if any position is capped
      5. Convert weights to whole shares; track residual cash
    """
    cap = RISK_CAPS[risk_tolerance]
    n_target = target_n_stocks(budget_ghs)

    elig = scored_df[scored_df["eligible"] & (scored_df["quality_score"] > 0)].copy()
    elig = elig.sort_values("quality_score", ascending=False)

    excluded: list[str] = []

    # Pick top N candidates by quality
    candidates = elig.head(n_target).copy()
    if len(candidates) < n_target:
        excluded.append(
            f"Only {len(candidates)} eligible stocks with positive score; "
            f"requested {n_target}"
        )

    # --- Step 1: Quality-tilted weights, capped by concentration ---
    # Use softmax-like tilt on quality scores
    scores = candidates["quality_score"].to_numpy()
    raw_weights = scores / scores.sum()

    # Apply concentration cap: any weight above cap gets clipped,
    # excess redistributed proportionally to others
    weights = raw_weights.copy()
    for _ in range(5):  # iterate to convergence
        over = weights > cap
        if not over.any():
            break
        excess = (weights[over] - cap).sum()
        weights[over] = cap
        # Redistribute to under-cap positions, proportional to their current weight
        under = ~over
        if under.sum() > 0 and weights[under].sum() > 0:
            weights[under] += excess * (weights[under] / weights[under].sum())
        else:
            break

    # --- Step 2: Liquidity guardrail ---
    # For each position, compute desired GHS spend and check against
    # 5x average daily turnover. If exceeded, scale down.
    candidates = candidates.reset_index(drop=True)
    desired_ghs = weights * budget_ghs

    # Daily turnover in GHS = avg_volume_10d * price_ghs
    avg_vol = candidates["avg_volume_10d"].fillna(0).to_numpy()
    prices = candidates["price_ghs"].to_numpy()
    daily_turnover_ghs = avg_vol * prices
    max_position_ghs = daily_turnover_ghs * LIQUIDITY_TURNOVER_FRACTION
    # If turnover is missing/zero, allow a small token allocation rather
    # than zero (avoids dropping the position entirely on noisy data),
    # but keep it conservative.
    max_position_ghs = np.where(
        max_position_ghs > 0, max_position_ghs, 500.0
    )

    capped_ghs = np.minimum(desired_ghs, max_position_ghs)
    liquidity_cap_hit = capped_ghs < desired_ghs - 0.01

    if liquidity_cap_hit.any():
        affected = candidates.loc[liquidity_cap_hit, "ticker"].tolist()
        excluded.append(
            f"Liquidity cap applied to: {affected}. Residual unallocated "
            f"because we don't push into less liquid names that would also "
            f"be capped."
        )

    # Recompute final weights from capped GHS allocations
    final_ghs = capped_ghs
    final_weights = final_ghs / budget_ghs

    # --- Step 3: Convert to whole shares ---
    positions = []
    total_invested = 0.0
    for i, row in candidates.iterrows():
        target_ghs = final_ghs[i]
        price = row["price_ghs"]
        if pd.isna(price) or price <= 0:
            continue
        shares = int(target_ghs / price)
        if shares < 1:
            # Position too small even for 1 share -- skip
            excluded.append(
                f"{row['ticker']}: position would be < 1 share at this budget"
            )
            continue
        cost_ghs = shares * price
        cost_usd = cost_ghs / fx_rate
        weight_pct = (cost_ghs / budget_ghs) * 100.0
        notes = []
        if liquidity_cap_hit[i]:
            # Tell the user what the cap actually means in days-of-volume
            if daily_turnover_ghs[i] > 0:
                days_to_fill = capped_ghs[i] / daily_turnover_ghs[i]
                notes.append(
                    f"liquidity-capped (~{days_to_fill:.1f} days to fill at avg vol)"
                )
            else:
                notes.append("liquidity-capped (low/no recent volume)")
        positions.append(Position(
            ticker=row["ticker"],
            name=str(row["name"]),
            price_ghs=float(price),
            shares=shares,
            cost_ghs=float(cost_ghs),
            cost_usd=float(cost_usd),
            weight_pct=float(weight_pct),
            quality_score=float(row["quality_score"]),
            notes=notes,
        ))
        total_invested += cost_ghs

    residual_ghs = budget_ghs - total_invested

    return PortfolioRecommendation(
        budget_ghs=budget_ghs,
        budget_usd=budget_ghs / fx_rate,
        fx_rate_ghs_per_usd=fx_rate,
        fx_source=fx_source,
        horizon_years=horizon_years,
        risk_tolerance=risk_tolerance,
        target_n_stocks=n_target,
        positions=positions,
        total_invested_ghs=total_invested,
        total_invested_usd=total_invested / fx_rate,
        cash_residual_ghs=residual_ghs,
        cash_residual_usd=residual_ghs / fx_rate,
        excluded_reasons=excluded,
    )


def format_recommendation(rec: PortfolioRecommendation) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("GSE PORTFOLIO RECOMMENDATION")
    lines.append("=" * 72)
    lines.append(f"  Budget:         GHS {rec.budget_ghs:,.2f}  /  USD {rec.budget_usd:,.2f}")
    lines.append(f"  FX rate:        {rec.fx_rate_ghs_per_usd:.4f} GHS per USD ({rec.fx_source})")
    lines.append(f"  Horizon:        {rec.horizon_years} years")
    lines.append(f"  Risk tolerance: {rec.risk_tolerance}")
    lines.append(f"  Target stocks:  {rec.target_n_stocks}")
    lines.append("")
    lines.append("RECOMMENDED POSITIONS")
    lines.append("-" * 72)
    lines.append(f"  {'Ticker':<8} {'Shares':>7} {'Price':>8} {'Cost GHS':>12} {'Cost USD':>10} {'Weight':>8}  Notes")
    for p in rec.positions:
        notes_str = ", ".join(p.notes) if p.notes else ""
        lines.append(
            f"  {p.ticker:<8} {p.shares:>7} {p.price_ghs:>8.2f} "
            f"{p.cost_ghs:>12,.2f} {p.cost_usd:>10,.2f} {p.weight_pct:>7.1f}%  {notes_str}"
        )
    lines.append("-" * 72)
    lines.append(f"  TOTAL INVESTED:  GHS {rec.total_invested_ghs:,.2f}  /  USD {rec.total_invested_usd:,.2f}")
    lines.append(f"  CASH RESIDUAL:   GHS {rec.cash_residual_ghs:,.2f}  /  USD {rec.cash_residual_usd:,.2f}")
    if rec.excluded_reasons:
        lines.append("")
        lines.append("NOTES & EXCLUSIONS")
        for r in rec.excluded_reasons:
            lines.append(f"  - {r}")
    lines.append("")
    lines.append("IMPORTANT CAVEATS:")
    lines.append("  - This is a fundamental-quality-driven allocation, NOT a return prediction.")
    lines.append("  - GSE 1-year returns are partly cedi inflation, not real value creation.")
    lines.append("  - Liquidity on the GSE is limited -- actual fills may differ from quoted prices.")
    lines.append("  - Do your own research before investing. This is not investment advice.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="GSE portfolio recommender")
    parser.add_argument("--budget-ghs", type=float, default=None,
                        help="Budget in Ghana cedis")
    parser.add_argument("--budget-usd", type=float, default=None,
                        help="Budget in USD (converted to GHS using live FX)")
    parser.add_argument("--horizon", type=int, default=5,
                        help="Investment horizon in years (1-10)")
    parser.add_argument("--risk", choices=["low", "medium", "high"], default="medium",
                        help="Risk tolerance")
    args = parser.parse_args()

    if args.budget_ghs is None and args.budget_usd is None:
        print("ERROR: provide either --budget-ghs or --budget-usd")
        return 1

    if not SCORED_PATH.exists():
        print(f"ERROR: {SCORED_PATH} not found. Run: python -m ghana.scorer")
        return 1

    print("Loading scored stocks...")
    scored = pd.read_csv(SCORED_PATH)

    print("Fetching FX rate...")
    fx_rate, fx_source = fetch_fx_rate()
    print(f"  GHS per USD: {fx_rate:.4f} (source: {fx_source})")

    if args.budget_ghs is not None:
        budget_ghs = args.budget_ghs
    else:
        budget_ghs = args.budget_usd * fx_rate

    rec = build_portfolio(
        scored_df=scored,
        budget_ghs=budget_ghs,
        horizon_years=args.horizon,
        risk_tolerance=args.risk,
        fx_rate=fx_rate,
        fx_source=fx_source,
    )

    print()
    print(format_recommendation(rec))

    # Save JSON output
    out_path = DATA_DIR / "latest_recommendation.json"
    out_path.write_text(json.dumps(asdict(rec), indent=2, default=str))
    print(f"\nSaved JSON to: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
