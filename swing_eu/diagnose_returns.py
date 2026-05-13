"""
Find rows in data_eu/predictions.parquet with implausible fwd_ret_5d.
A 5-day return outside [-50%, +200%] is almost certainly bad data.
"""
import pandas as pd
from swing_eu.config import DATA_DIR

df = pd.read_parquet(DATA_DIR / "predictions.parquet")
print(f"Total rows: {len(df):,}")
print(f"Total symbols: {df['symbol'].nunique()}")
print()

print("fwd_ret_5d distribution:")
print(df["fwd_ret_5d"].describe(percentiles=[0.001, 0.01, 0.5, 0.99, 0.999]).to_string())
print()

# Flag implausible returns
bad = df[(df["fwd_ret_5d"] < -0.5) | (df["fwd_ret_5d"] > 2.0)]
print(f"Rows with fwd_ret_5d outside [-50%, +200%]: {len(bad):,}")
if len(bad) > 0:
    print()
    print("Symbols affected (top 20 by frequency):")
    print(bad["symbol"].value_counts().head(20).to_string())
    print()
    print("Top 10 most extreme returns:")
    print(bad.nlargest(10, "fwd_ret_5d")[["timestamp", "symbol", "pred", "fwd_ret_5d"]].to_string(index=False))
    print()
    print("Bottom 10 most extreme returns:")
    print(bad.nsmallest(10, "fwd_ret_5d")[["timestamp", "symbol", "pred", "fwd_ret_5d"]].to_string(index=False))
