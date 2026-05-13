"""
Signal sanity check.

For each candidate feature, compute its correlation with forward returns
(returns AFTER the feature is observed). Strong signals show up as 
consistent same-sign correlations across multiple horizons.

What we expect:
- Cross-sectional momentum (ret_60d_xs_rank) should have small POSITIVE
  correlation with forward returns (5-20 day) — that's the momentum effect.
- High volatility (vol_20d) should have small NEGATIVE correlation 
  (low-vol anomaly).
- Kalman deviation (price > trend) is more ambiguous but interesting.

Honest expectations:
- Correlations of 0.01-0.05 are REAL and TRADEABLE in cross-section.
- Correlations of 0 mean no edge in our universe/period.
- Correlations >0.10 are suspicious (look-ahead bias somewhere).
"""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from swing_eu.config import DATA_DIR


# Features we want to test for predictive power
CANDIDATE_FEATURES = [
    "ret_5d", "ret_20d", "ret_60d", "ret_120d",
    "ret_5d_xs_rank", "ret_20d_xs_rank", "ret_60d_xs_rank", "ret_120d_xs_rank",
    "vol_20d", "vol_60d", "vol_20d_xs_rank",
    "kalman_deviation", "vol_regime_z", "spectral_low_freq_ratio",
    "volume_zscore_20d",
]

# Forward return horizons to predict
FORWARD_HORIZONS = [5, 20, 60]


def add_forward_returns(panel: pd.DataFrame, horizons: list[int]) -> pd.DataFrame:
    """For each symbol, compute close-to-close return N days ahead."""
    out = []
    for symbol, group in panel.groupby("symbol", sort=False):
        g = group.sort_values("timestamp").copy()
        for h in horizons:
            g[f"fwd_ret_{h}d"] = g["close"].pct_change(h).shift(-h)
        out.append(g)
    return pd.concat(out, ignore_index=True)


def correlation_table(
    df: pd.DataFrame,
    features: list[str],
    forward_cols: list[str],
) -> pd.DataFrame:
    """Spearman rank correlation: feature vs each forward-return column."""
    rows = []
    for f in features:
        if f not in df.columns:
            continue
        row = {"feature": f}
        for fwd in forward_cols:
            sub = df[[f, fwd]].dropna()
            if len(sub) < 1000:
                row[fwd] = np.nan
                continue
            rho, _ = spearmanr(sub[f], sub[fwd])
            row[fwd] = rho
        rows.append(row)
    return pd.DataFrame(rows)


def correlation_by_year(
    df: pd.DataFrame,
    feature: str,
    forward_col: str,
) -> pd.DataFrame:
    """Same correlation but broken out by year — to see stability."""
    rows = []
    df = df.copy()
    df["year"] = pd.to_datetime(df["timestamp"]).dt.year
    for year, group in df.groupby("year"):
        sub = group[[feature, forward_col]].dropna()
        if len(sub) < 200:
            continue
        rho, _ = spearmanr(sub[feature], sub[forward_col])
        rows.append({"year": year, "corr": rho, "n_obs": len(sub)})
    return pd.DataFrame(rows)


def main() -> int:
    in_path = DATA_DIR / "features.parquet"
    if not in_path.exists():
        print(f"ERROR: {in_path} not found. Run swing/features.py first.")
        return 1

    print(f"Loading features from {in_path}")
    df = pd.read_parquet(in_path)
    print(f"  Loaded: {df.shape[0]:,} rows, {df['symbol'].nunique()} symbols")

    print("\nAdding forward returns...")
    df = add_forward_returns(df, FORWARD_HORIZONS)
    forward_cols = [f"fwd_ret_{h}d" for h in FORWARD_HORIZONS]

    print("\n" + "=" * 70)
    print("CORRELATION TABLE: feature vs forward return (Spearman rank)")
    print("=" * 70)
    print("(Positive = feature predicts higher future returns)")
    print("(Magnitudes of 0.01-0.05 are REAL signals at this scale)")
    print()
    
    corr_table = correlation_table(df, CANDIDATE_FEATURES, forward_cols)
    print(corr_table.to_string(
        index=False,
        formatters={c: "{:+.4f}".format for c in forward_cols},
    ))

    # Pick the strongest feature for a stability check
    print("\n" + "=" * 70)
    print("STABILITY CHECK: top feature's correlation by year")
    print("=" * 70)
    
    # Find feature with highest absolute correlation on 20d forward
    target = "fwd_ret_20d"
    abs_corrs = corr_table.set_index("feature")[target].abs()
    top_feature = abs_corrs.idxmax()
    top_corr = corr_table.set_index("feature").loc[top_feature, target]
    print(f"Top feature on {target}: {top_feature} (corr = {top_corr:+.4f})")
    print()
    
    yearly = correlation_by_year(df, top_feature, target)
    print(yearly.to_string(index=False, formatters={"corr": "{:+.4f}".format}))
    
    print("\n  Interpretation:")
    print("  - If sign flips frequently year-to-year, the signal is unstable")
    print("  - If sign is consistent (mostly +ve or -ve), the signal is durable")

    # Save the correlation table for later reference
    out_path = DATA_DIR / "signal_check.csv"
    corr_table.to_csv(out_path, index=False)
    print(f"\n  Correlation table saved to: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
