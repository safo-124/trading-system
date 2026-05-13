"""
Live prediction script.

Pulls the most recent 180 days of bars for the S&P 500 universe (enough
history to compute 120-day return and 252-day volatility z-score).
Computes features. Runs the production model. Returns ranked predictions
for the most recent trading day available.

This is what the FastAPI live endpoint will call.
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import lightgbm as lgb
import pandas as pd
from tqdm import tqdm

from swing.config import DATA_DIR
from swing.universe import get_universe
from swing.yf_client import fetch_daily_bars
from swing.features import basic_features, dsp_features, add_cross_sectional_ranks


PRODUCTION_MODEL_PATH = DATA_DIR / "model_production.txt"
MODEL_METADATA_PATH = DATA_DIR / "model_metadata.json"

# How much history to pull. Needs to cover the longest feature lookback.
# vol_regime_z uses 252-day rolling window, so we need at least 252 + buffer.
DEFAULT_LOOKBACK_DAYS = 380  # ~18 calendar months of trading days


def fetch_recent_bars(
    tickers: list[str],
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> pd.DataFrame:
    """Fetch the last N days of bars for each ticker. Returns a tall panel."""
    end = datetime.utcnow().date()
    start = end - timedelta(days=int(lookback_days * 1.5))  # buffer for weekends
    
    frames = []
    for ticker in tqdm(tickers, desc="Fetching live bars"):
        try:
            df = fetch_daily_bars(ticker, start=start.isoformat(), end=end.isoformat())
            if df.empty:
                continue
            frames.append(df)
        except Exception as e:
            print(f"  [skip {ticker}: {type(e).__name__}: {e}]", file=sys.stderr)
            continue
    
    if not frames:
        raise RuntimeError("No bars fetched for any ticker.")
    return pd.concat(frames, ignore_index=True)


def compute_live_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Run feature pipeline. Same as swing/features.py compute_features but inline."""
    out_frames = []
    for symbol, group in panel.groupby("symbol", sort=False):
        g = basic_features(group)
        g = dsp_features(g)
        out_frames.append(g)
    features = pd.concat(out_frames, ignore_index=True)
    features = add_cross_sectional_ranks(features)
    return features


def load_production_model() -> tuple[lgb.Booster, dict[str, Any]]:
    """Load saved model + metadata. Raises if files missing."""
    if not PRODUCTION_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Production model not found at {PRODUCTION_MODEL_PATH}. "
            f"Run: python -m swing.train_production"
        )
    if not MODEL_METADATA_PATH.exists():
        raise FileNotFoundError(f"Model metadata not found at {MODEL_METADATA_PATH}")
    
    model = lgb.Booster(model_file=str(PRODUCTION_MODEL_PATH))
    metadata = json.loads(MODEL_METADATA_PATH.read_text())
    return model, metadata


def predict_latest(
    universe_size: int | None = None,
    n_per_side: int = 20,
) -> dict[str, Any]:
    """
    Full live-prediction pipeline. Returns dict suitable for API response.
    """
    # Load model first — fail fast if missing
    model, metadata = load_production_model()
    features_used = metadata["features"]
    
    # Universe
    tickers = get_universe(n=universe_size, source="sp500")
    print(f"Universe: {len(tickers)} tickers")
    
    # Fetch bars
    panel = fetch_recent_bars(tickers)
    print(f"Fetched: {panel['symbol'].nunique()} symbols, {len(panel):,} rows")
    
    # Features
    print("Computing features...")
    features_df = compute_live_features(panel)
    
    # Most recent date with full features for at least 80% of universe
    daily_completeness = features_df.dropna(subset=features_used).groupby("timestamp").size()
    threshold = 0.8 * panel["symbol"].nunique()
    valid_dates = daily_completeness[daily_completeness >= threshold].index
    if len(valid_dates) == 0:
        raise RuntimeError("No date has features for enough stocks. Universe may be stale.")
    as_of = valid_dates.max()
    print(f"As-of date: {as_of.date()} (feature-complete)")
    
    # Predict on that day
    today = features_df[features_df["timestamp"] == as_of].dropna(subset=features_used).copy()
    X = today[features_used]
    today["pred"] = model.predict(X)
    
    # Rank
    today = today.sort_values("pred", ascending=False)
    
    # Build response
    def to_records(d: pd.DataFrame) -> list[dict]:
        return [
            {
                "timestamp": row["timestamp"].date().isoformat(),
                "symbol": row["symbol"],
                "pred": float(row["pred"]),
                "close": float(row["close"]),
            }
            for _, row in d.iterrows()
        ]
    
    long_picks = today.head(n_per_side)
    short_picks = today.tail(n_per_side).iloc[::-1]  # reverse so worst first
    
    return {
        "as_of": as_of.date().isoformat(),
        "n_stocks_predicted": int(len(today)),
        "model_trained_at": metadata.get("trained_at"),
        "long_picks": to_records(long_picks),
        "short_picks": to_records(short_picks),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=None,
                        help="Limit universe size (default: full SP500)")
    parser.add_argument("--n-per-side", type=int, default=20)
    parser.add_argument("--out", default=str(DATA_DIR / "live_predictions.json"))
    args = parser.parse_args()
    
    result = predict_latest(universe_size=args.size, n_per_side=args.n_per_side)
    
    print("\n" + "=" * 60)
    print(f"LIVE PREDICTIONS — as of {result['as_of']}")
    print("=" * 60)
    print(f"\nLONG PICKS ({len(result['long_picks'])}):")
    for p in result["long_picks"]:
        print(f"  {p['symbol']:6s}  pred={p['pred']:+.4f}  close=${p['close']:.2f}")
    print(f"\nSHORT PICKS ({len(result['short_picks'])}):")
    for p in result["short_picks"]:
        print(f"  {p['symbol']:6s}  pred={p['pred']:+.4f}  close=${p['close']:.2f}")
    
    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2, default=str))
    print(f"\n  Saved to: {out_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
