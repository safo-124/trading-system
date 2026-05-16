"""
GSE fundamental quality scorer.

Reads data_ghana/gse_fundamentals.csv and produces a 0-1 quality score
for each stock, plus eligibility flags.

This is RULES-BASED, not ML. The GSE has ~40 stocks -- far too few for
machine learning. Transparent scoring rules are the honest approach.

Two HARD GATES (a stock failing either is marked ineligible):
  1. Liquidity gate: the stock must have traded recently (volume present).
     A stock you cannot buy is not an investment candidate.
  2. Data-integrity gate: P/E must be >= 1.5. Values below that are almost
     always a currency mismatch (foreign-listed companies like AngloGold
     reporting EPS in USD while priced in cedis). Negative P/E (losses) is
     allowed through the gate but scores zero on the value component.

Quality score = weighted sum of four 0-1 components:
  - value      (35%): based on P/E ratio, lower is better
  - profitability (25%): positive EPS scores, negative scores zero
  - income     (20%): dividend yield (div_per_share / price)
  - momentum   (20%): 1-year return, capped to limit outlier influence

IMPORTANT CAVEAT baked into output: GSE 1-year returns are partly driven
by cedi inflation/devaluation, not real value creation. The momentum
component uses them as a RELATIVE ranking signal only. Do not read the
score as 'expected profit'.
"""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from ghana.config import DATA_DIR


FUNDAMENTALS_PATH = DATA_DIR / "gse_fundamentals.csv"
SCORED_OUTPUT_PATH = DATA_DIR / "gse_scored.csv"

# Hard gates
MIN_PE_FOR_INTEGRITY = 1.5   # below this = currency mismatch / data garbage
MAX_PE_REASONABLE = 60.0     # above this = effectively no earnings support

# Score component weights (must sum to 1.0)
W_VALUE = 0.35
W_PROFITABILITY = 0.25
W_INCOME = 0.20
W_MOMENTUM = 0.20


def value_score(pe: float | None) -> float:
    """
    Lower P/E = better value. Returns 0-1.
    Negative P/E (company losing money) scores 0 here -- profitability
    component handles the loss separately.
    """
    if pe is None or np.isnan(pe):
        return 0.0
    if pe <= 0:
        return 0.0  # losing money -- no value support
    if pe < MIN_PE_FOR_INTEGRITY:
        return 0.0  # data integrity issue, treated as unscorable
    if pe <= 8:
        return 1.0
    if pe <= 12:
        return 0.8
    if pe <= 18:
        return 0.55
    if pe <= 25:
        return 0.35
    if pe <= MAX_PE_REASONABLE:
        return 0.15
    return 0.0


def profitability_score(eps: float | None) -> float:
    """Positive EPS scores; negative scores 0. Scaled by magnitude lightly."""
    if eps is None or np.isnan(eps):
        return 0.0
    if eps <= 0:
        return 0.0
    # Any positive EPS gets a base score; bigger is slightly better but
    # we don't want huge-EPS foreign stocks to dominate, so cap gently.
    if eps >= 2.0:
        return 1.0
    if eps >= 1.0:
        return 0.85
    if eps >= 0.5:
        return 0.7
    if eps >= 0.1:
        return 0.55
    return 0.4  # tiny but positive


def income_score(div_per_share: float | None, price: float | None) -> float:
    """Dividend yield = div_per_share / price. Higher yield = higher score."""
    if (div_per_share is None or np.isnan(div_per_share)
            or price is None or np.isnan(price) or price <= 0):
        return 0.0
    if div_per_share <= 0:
        return 0.0
    yield_pct = div_per_share / price
    # GSE dividend yields range widely; score generously since paying
    # any dividend at all is a positive signal in this market.
    if yield_pct >= 0.08:
        return 1.0
    if yield_pct >= 0.05:
        return 0.85
    if yield_pct >= 0.03:
        return 0.65
    if yield_pct >= 0.01:
        return 0.45
    return 0.25  # pays something, but tiny


def momentum_score(ret_1yr: float | None) -> float:
    """
    1-year return as a momentum signal. CAPPED because GSE returns are
    partly cedi inflation -- we don't want a +700% inflation-driven number
    to dominate the score.
    """
    if ret_1yr is None or np.isnan(ret_1yr):
        return 0.5  # neutral when unknown -- don't penalize missing data
    if ret_1yr <= -0.20:
        return 0.0   # down 20%+ -- bad
    if ret_1yr <= 0.0:
        return 0.25
    if ret_1yr <= 0.30:
        return 0.55
    if ret_1yr <= 1.0:
        return 0.75
    # Anything above +100% gets max momentum score but no extra credit --
    # past +100%/yr is more likely inflation/illiquidity than skill.
    return 1.0


def score_stocks(df: pd.DataFrame) -> pd.DataFrame:
    """Apply gates and scoring. Returns df with new columns."""
    df = df.copy()

    # --- HARD GATE 1: Liquidity ---
    # Stock must have traded -- use 'volume' (snapshot) OR avg_volume_10d.
    has_volume = df["volume"].notna() & (df["volume"] > 0)
    has_avg_volume = (
        df["avg_volume_10d"].notna() & (df["avg_volume_10d"] > 0)
        if "avg_volume_10d" in df.columns else pd.Series(False, index=df.index)
    )
    df["liquid"] = has_volume | has_avg_volume

    # --- HARD GATE 2: Data integrity (P/E sanity) ---
    # P/E must be >= MIN_PE_FOR_INTEGRITY. Negative P/E is allowed through
    # (real losses) but P/E in (0, 1.5) is a currency-mismatch artifact.
    pe = df["pe_ratio"]
    df["pe_integrity_ok"] = ~((pe > 0) & (pe < MIN_PE_FOR_INTEGRITY))

    # Eligible = passes both gates
    df["eligible"] = df["liquid"] & df["pe_integrity_ok"]

    # --- Component scores (computed for all, but only meaningful if eligible) ---
    df["score_value"] = df["pe_ratio"].apply(value_score)
    df["score_profitability"] = df["eps"].apply(profitability_score)
    df["score_income"] = df.apply(
        lambda r: income_score(r.get("div_per_share"), r.get("price_ghs")), axis=1
    )
    df["score_momentum"] = df["ret_1yr"].apply(momentum_score)

    # --- Composite quality score ---
    df["quality_score"] = (
        W_VALUE * df["score_value"]
        + W_PROFITABILITY * df["score_profitability"]
        + W_INCOME * df["score_income"]
        + W_MOMENTUM * df["score_momentum"]
    )

    # Ineligible stocks get their score zeroed for ranking clarity
    df.loc[~df["eligible"], "quality_score"] = 0.0

    return df


def main() -> int:
    if not FUNDAMENTALS_PATH.exists():
        print(f"ERROR: {FUNDAMENTALS_PATH} not found. "
              f"Run: python -m ghana.fundamental_scraper")
        return 1

    print(f"Loading fundamentals from {FUNDAMENTALS_PATH}")
    df = pd.read_csv(FUNDAMENTALS_PATH)
    print(f"  {len(df)} stocks loaded")

    scored = score_stocks(df)

    # Save full scored output
    scored.to_csv(SCORED_OUTPUT_PATH, index=False)
    print(f"  Saved scored data to: {SCORED_OUTPUT_PATH}")

    # --- Report ---
    n_eligible = scored["eligible"].sum()
    n_liquid = scored["liquid"].sum()
    n_pe_ok = scored["pe_integrity_ok"].sum()
    print()
    print("=" * 70)
    print("ELIGIBILITY SUMMARY")
    print("=" * 70)
    print(f"  Total stocks:                    {len(scored)}")
    print(f"  Passed liquidity gate:           {n_liquid}")
    print(f"  Passed P/E data-integrity gate:  {n_pe_ok}")
    print(f"  ELIGIBLE (passed both):          {n_eligible}")

    # Show ineligible stocks and why
    print()
    print("INELIGIBLE STOCKS (and reason):")
    inelig = scored[~scored["eligible"]]
    for _, row in inelig.iterrows():
        reasons = []
        if not row["liquid"]:
            reasons.append("no recent volume")
        if not row["pe_integrity_ok"]:
            reasons.append(f"P/E={row['pe_ratio']:.2f} (currency mismatch?)")
        print(f"  {row['ticker']:10s} {row['name'][:35]:35s} - {', '.join(reasons)}")

    # Ranked eligible stocks
    print()
    print("=" * 70)
    print("RANKED ELIGIBLE STOCKS (by quality score)")
    print("=" * 70)
    elig = scored[scored["eligible"]].sort_values("quality_score", ascending=False)
    display_cols = [
        "ticker", "name", "price_ghs", "pe_ratio", "eps", "div_per_share",
        "ret_1yr", "score_value", "score_profitability", "score_income",
        "score_momentum", "quality_score",
    ]
    display_cols = [c for c in display_cols if c in elig.columns]
    print(elig[display_cols].to_string(index=False, formatters={
        "price_ghs": "{:.2f}".format,
        "pe_ratio": "{:.2f}".format,
        "eps": "{:.3f}".format,
        "div_per_share": "{:.3f}".format,
        "ret_1yr": "{:+.1%}".format,
        "score_value": "{:.2f}".format,
        "score_profitability": "{:.2f}".format,
        "score_income": "{:.2f}".format,
        "score_momentum": "{:.2f}".format,
        "quality_score": "{:.3f}".format,
    }))

    print()
    print("CAVEAT: quality_score is a relative ranking of fundamental quality,")
    print("NOT a prediction of returns. GSE 1-year returns are inflated by cedi")
    print("devaluation. Do your own research before investing.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
