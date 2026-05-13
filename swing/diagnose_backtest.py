"""
Diagnostic: does the model's prediction correlate POSITIVELY or 
NEGATIVELY with realized forward returns?

If positive correlation -> high pred = high fwd_ret -> we should be 
LONG the high-pred stocks. Current code does the opposite.

If negative correlation -> high pred = low fwd_ret -> we should be 
SHORT the high-pred stocks (current code matches this).
"""

import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from swing.config import DATA_DIR

preds = pd.read_parquet(DATA_DIR / "predictions.parquet")
print(f"Loaded predictions: {preds.shape}")
print(f"Columns: {list(preds.columns)}")
print()

# Quick null check
print("Null counts:")
print(preds.isnull().sum())
print()

# Drop rows without realized returns
clean = preds.dropna(subset=["pred", "fwd_ret_5d"])
print(f"Clean rows: {len(clean):,}")
print()

# Overall correlation: predicted score vs actual forward return
ic, p = spearmanr(clean["pred"], clean["fwd_ret_5d"])
print(f"Overall Spearman(pred, fwd_ret_5d): {ic:+.4f} (p={p:.2e})")
print()

# Also check: predicted score vs the TARGET it was trained on
target_col = "fwd_ret_5d_xs_rank"
if target_col in clean.columns:
    ic2, p2 = spearmanr(clean["pred"], clean[target_col])
    print(f"Overall Spearman(pred, {target_col}): {ic2:+.4f} (p={p2:.2e})")

print()
print("=" * 60)
print("Quintile analysis: bin predictions, look at avg fwd_ret_5d per bin")
print("=" * 60)
clean["pred_quintile"] = pd.qcut(clean["pred"], 5, labels=["Q1_low", "Q2", "Q3", "Q4", "Q5_high"])
quintile_stats = clean.groupby("pred_quintile", observed=True)["fwd_ret_5d"].agg(["mean", "median", "count"])
print(quintile_stats.to_string(formatters={
    "mean": "{:+.4%}".format,
    "median": "{:+.4%}".format,
}))
print()
print("Interpretation:")
print("  - If Q1_low has the LOWEST mean fwd_ret_5d -> model predicts correctly")
print("    -> low pred = bad future return -> SHORT low-pred (current code is WRONG)")
print("  - If Q1_low has the HIGHEST mean fwd_ret_5d -> model is inverted")
print("    -> low pred = good future return -> LONG low-pred (current code is RIGHT)")
print()

# Sample one specific day to make it concrete
print("=" * 60)
print("Concrete example: one trading day")
print("=" * 60)
sample_day = clean["timestamp"].sort_values().unique()[len(clean["timestamp"].unique()) // 2]
day_df = clean[clean["timestamp"] == sample_day].copy()
day_df = day_df.sort_values("pred")
print(f"Date: {pd.Timestamp(sample_day).date()}")
print(f"Stocks that day: {len(day_df)}")
print()
print("Bottom 5 by prediction (current LONG leg):")
print(day_df.head(5)[["symbol", "pred", "fwd_ret_5d"]].to_string(index=False, formatters={
    "pred": "{:.4f}".format,
    "fwd_ret_5d": "{:+.2%}".format,
}))
print(f"  Avg fwd_ret_5d of bottom 5: {day_df.head(5)['fwd_ret_5d'].mean():+.2%}")
print()
print("Top 5 by prediction (current SHORT leg):")
print(day_df.tail(5)[["symbol", "pred", "fwd_ret_5d"]].to_string(index=False, formatters={
    "pred": "{:.4f}".format,
    "fwd_ret_5d": "{:+.2%}".format,
}))
print(f"  Avg fwd_ret_5d of top 5: {day_df.tail(5)['fwd_ret_5d'].mean():+.2%}")
