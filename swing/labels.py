"""
Labels for cross-sectional mean-reversion strategy.

For each (symbol, date), compute:
  - fwd_ret_5d:        raw 5-day forward return (regression target)
  - fwd_ret_5d_xs_rank: rank of forward return across all stocks that day,
                       normalized to [0, 1] (PRIMARY TARGET)
  - fwd_ret_20d:       longer horizon for robustness checks

The xs_rank target is what we predict. Why a rank, not raw return?
  - Cross-sectional strategies care about *relative* outperformance
  - Ranks are bounded [0, 1], stable across market regimes
  - Models train better on bounded targets than fat-tailed raw returns
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

import pandas as pd
import numpy as np
from tqdm import tqdm

from swing.config import DATA_DIR


FORWARD_HORIZONS = [5, 20]


def add_forward_returns(panel: pd.DataFrame, horizons: list[int]) -> pd.DataFrame:
    """For each symbol, compute close-to-close return N days ahead."""
    out_frames = []
    grouped = panel.groupby("symbol", sort=False)
    for symbol, group in tqdm(grouped, desc="Forward returns", total=grouped.ngroups):
        g = group.sort_values("timestamp").copy()
        for h in horizons:
            # pct_change(h).shift(-h) gives return from t to t+h
            g[f"fwd_ret_{h}d"] = g["close"].pct_change(h).shift(-h)
        out_frames.append(g)
    return pd.concat(out_frames, ignore_index=True)


def add_cross_sectional_rank_labels(panel: pd.DataFrame, horizons: list[int]) -> pd.DataFrame:
    """Rank forward returns across all stocks on each date."""
    panel = panel.copy()
    for h in horizons:
        col = f"fwd_ret_{h}d"
        panel[f"{col}_xs_rank"] = panel.groupby("timestamp")[col].rank(pct=True)
    return panel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path",
                        default=str(DATA_DIR / "features.parquet"))
    parser.add_argument("--out", default=str(DATA_DIR / "training_set.parquet"))
    args = parser.parse_args()

    in_path = Path(args.in_path)
    if not in_path.exists():
        print(f"ERROR: {in_path} not found.")
        return 1
    
    print(f"Loading features from {in_path}")
    df = pd.read_parquet(in_path)
    print(f"  shape: {df.shape}")
    
    print("\nAdding forward returns...")
    df = add_forward_returns(df, FORWARD_HORIZONS)
    
    print("\nAdding cross-sectional rank labels...")
    df = add_cross_sectional_rank_labels(df, FORWARD_HORIZONS)
    
    # Drop rows where we can't compute the primary target
    before = len(df)
    df = df.dropna(subset=["fwd_ret_5d_xs_rank"])
    print(f"\nDropped {before - len(df):,} rows with missing forward returns")
    print(f"Final shape: {df.shape}")
    
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"\n  Saved to: {out_path} ({size_mb:.1f} MB)")
    
    # Sanity check
    print("\n--- LABEL SANITY ---")
    rank_target = df["fwd_ret_5d_xs_rank"]
    print(f"fwd_ret_5d_xs_rank min/max: {rank_target.min():.4f} / {rank_target.max():.4f}")
    print(f"  mean: {rank_target.mean():.4f} (should be ~0.5)")
    print(f"  median: {rank_target.median():.4f}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
