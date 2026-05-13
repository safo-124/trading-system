"""
Walk-forward training of a LightGBM model to predict 5-day forward rank.

Walk-forward setup:
  - Initial train window: 4 years (~1000 trading days)
  - Test window: 6 months (~125 trading days)
  - Re-train every 6 months, slide forward
  - This gives us ~14-15 out-of-sample test folds across 2014-2026

Why this matters: a single train/test split would be lucky or unlucky.
Walk-forward shows whether the model has consistent edge across regimes.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.stats import spearmanr
from tqdm import tqdm

from swing.config import DATA_DIR


# Features the model is allowed to see — chosen from signal check results.
# Mean-reversion features (durable signal):
MR_FEATURES = [
    "ret_5d", "ret_20d", "ret_60d", "ret_120d",
    "logret_5d", "logret_20d",
    "kalman_deviation",
]

# Volatility features (use the normalized ones, NOT raw vol_20d/vol_60d
# which were contaminated by AI-bubble bias)
VOL_FEATURES = [
    "vol_regime_z",
    "vol_20d_xs_rank",
]

# Volume features
VOL_FEAT = ["volume_zscore_20d"]

FEATURES = MR_FEATURES + VOL_FEATURES + VOL_FEAT

TARGET = "fwd_ret_5d_xs_rank"

# Walk-forward config
TRAIN_YEARS = 4
TEST_MONTHS = 6


def make_walk_forward_splits(dates: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    """
    Returns list of (train_start, train_end, test_end) tuples.
    Each test_end is train_end + 6 months. Slides forward by 6 months.
    """
    dates_sorted = pd.to_datetime(sorted(dates.unique()))
    start = dates_sorted[0]
    end = dates_sorted[-1]
    
    splits = []
    cursor_train_end = start + pd.DateOffset(years=TRAIN_YEARS)
    
    while cursor_train_end + pd.DateOffset(months=TEST_MONTHS) <= end:
        train_start = start
        train_end = cursor_train_end
        test_end = cursor_train_end + pd.DateOffset(months=TEST_MONTHS)
        splits.append((train_start, train_end, test_end))
        cursor_train_end = test_end
    
    return splits


def train_one_fold(
    df: pd.DataFrame,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    test_end: pd.Timestamp,
) -> dict:
    """Train on [train_start, train_end), test on [train_end, test_end)."""
    train_mask = (df["timestamp"] >= train_start) & (df["timestamp"] < train_end)
    test_mask = (df["timestamp"] >= train_end) & (df["timestamp"] < test_end)
    
    train_df = df.loc[train_mask].dropna(subset=FEATURES + [TARGET])
    test_df = df.loc[test_mask].dropna(subset=FEATURES + [TARGET])
    
    if len(train_df) < 1000 or len(test_df) < 100:
        return None
    
    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]
    X_test = test_df[FEATURES]
    y_test = test_df[TARGET]
    
    model = lgb.LGBMRegressor(
        n_estimators=300,
        learning_rate=0.03,
        max_depth=6,
        num_leaves=31,
        min_child_samples=200,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=42,
        verbose=-1,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    
    # Spearman correlation of predictions vs realized rank
    ic, _ = spearmanr(preds, y_test)
    
    # Also compute IC per-day (more honest measure)
    test_df = test_df.copy()
    test_df["pred"] = preds
    daily_ic = test_df.groupby("timestamp").apply(
        lambda g: spearmanr(g["pred"], g[TARGET])[0] if len(g) > 5 else np.nan
    ).dropna()
    
    return {
        "train_start": train_start,
        "train_end": train_end,
        "test_end": test_end,
        "n_train": len(train_df),
        "n_test": len(test_df),
        "ic_overall": ic,
        "ic_daily_mean": daily_ic.mean(),
        "ic_daily_std": daily_ic.std(),
        "ic_daily_t": daily_ic.mean() / (daily_ic.std() / np.sqrt(len(daily_ic))) if daily_ic.std() > 0 else 0,
        "feature_importance": dict(zip(FEATURES, model.feature_importances_)),
        "predictions": test_df[["timestamp", "symbol", "pred", TARGET, "fwd_ret_5d"]].copy(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path",
                        default=str(DATA_DIR / "training_set.parquet"))
    parser.add_argument("--out", default=str(DATA_DIR / "predictions.parquet"))
    args = parser.parse_args()
    
    in_path = Path(args.in_path)
    if not in_path.exists():
        print(f"ERROR: {in_path} not found. Run swing/labels.py first.")
        return 1
    
    print(f"Loading training set from {in_path}")
    df = pd.read_parquet(in_path)
    print(f"  shape: {df.shape}")
    
    # Make walk-forward splits
    splits = make_walk_forward_splits(df["timestamp"])
    print(f"\n{len(splits)} walk-forward folds:")
    for i, (a, b, c) in enumerate(splits):
        print(f"  Fold {i+1:2d}: train [{a.date()} -> {b.date()})  test [{b.date()} -> {c.date()})")
    
    print("\nTraining each fold...")
    results = []
    all_preds = []
    for split in tqdm(splits, desc="Folds"):
        res = train_one_fold(df, *split)
        if res is None:
            continue
        results.append(res)
        all_preds.append(res["predictions"])
    
    # Summary table
    print("\n" + "=" * 75)
    print("WALK-FORWARD RESULTS")
    print("=" * 75)
    summary = pd.DataFrame([
        {
            "fold": i + 1,
            "test_start": r["train_end"].date(),
            "test_end": r["test_end"].date(),
            "n_test": r["n_test"],
            "ic_daily_mean": r["ic_daily_mean"],
            "ic_daily_t": r["ic_daily_t"],
        }
        for i, r in enumerate(results)
    ])
    print(summary.to_string(index=False, formatters={
        "ic_daily_mean": "{:+.4f}".format,
        "ic_daily_t": "{:+.2f}".format,
    }))
    
    print("\n--- AGGREGATE ---")
    print(f"  Mean daily IC: {summary['ic_daily_mean'].mean():+.4f}")
    print(f"  Std daily IC:  {summary['ic_daily_mean'].std():.4f}")
    print(f"  Fraction of folds with positive IC: "
          f"{(summary['ic_daily_mean'] > 0).mean():.2%}")
    
    # Aggregate feature importance across all folds
    print("\n--- AVERAGE FEATURE IMPORTANCE (across folds) ---")
    avg_imp = pd.DataFrame([r["feature_importance"] for r in results]).mean()
    print(avg_imp.sort_values(ascending=False).to_string())
    
    # Save all predictions for backtest
    combined_preds = pd.concat(all_preds, ignore_index=True)
    out_path = Path(args.out)
    combined_preds.to_parquet(out_path, index=False)
    print(f"\n  Predictions saved to: {out_path} ({len(combined_preds):,} rows)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
