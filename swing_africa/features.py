"""
Feature engineering for the swing strategy.

Loads daily OHLCV from data/bars_daily/*.parquet, computes features
per (symbol, timestamp), and saves a panel to data/features.parquet.

Two groups of features:
- BASIC: returns at multiple horizons, realized vol, volume features
- DSP:   Kalman-filtered trend, volatility regime, spectral power ratio

Cross-sectional features (ranks across all symbols on each date) are
computed AFTER the per-symbol features.
"""

from __future__ import annotations
import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal
from tqdm import tqdm

from swing_africa.config import BARS_DIR, DATA_DIR

warnings.filterwarnings("ignore", category=RuntimeWarning)


# ---------------------------------------------------------------
# BASIC FEATURES (per symbol, time-series)
# ---------------------------------------------------------------

RETURN_HORIZONS = [1, 5, 20, 60, 120]
VOL_HORIZONS = [20, 60]


def basic_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute basic time-series features for one symbol.
    Input df must have: timestamp, open, high, low, close, volume.
    Returns df with new columns added (no rows dropped here).
    """
    df = df.copy().sort_values("timestamp").reset_index(drop=True)
    close = df["close"]
    log_close = np.log(close)

    # Returns at multiple horizons (look-BACK: today vs N days ago)
    for h in RETURN_HORIZONS:
        df[f"ret_{h}d"] = close.pct_change(h)
        df[f"logret_{h}d"] = log_close.diff(h)

    # Realized volatility (std of daily log returns over window)
    daily_logret = log_close.diff(1)
    for h in VOL_HORIZONS:
        df[f"vol_{h}d"] = daily_logret.rolling(h).std() * np.sqrt(252)  # annualized

    # Volume features
    df["dollar_volume"] = df["close"] * df["volume"]
    df["dollar_volume_20d_mean"] = df["dollar_volume"].rolling(20).mean()
    df["volume_zscore_20d"] = (
        (df["volume"] - df["volume"].rolling(20).mean())
        / df["volume"].rolling(20).std()
    )

    return df


# ---------------------------------------------------------------
# DSP FEATURES (per symbol)
# ---------------------------------------------------------------

def kalman_trend(log_prices: np.ndarray, q: float = 1e-4, r: float = 1e-2) -> np.ndarray:
    """
    1D Kalman filter on log prices, separating trend (state) from noise.
    
    State model: x_t = x_{t-1} + drift_t + process_noise
    Observation:  y_t = x_t + measurement_noise
    
    q = process noise variance (how fast the trend can change)
    r = measurement noise variance (how noisy observations are)
    
    Returns the filtered trend estimate (same length as input).
    NaN-safe: leading NaNs in input become NaN in output.
    """
    y = np.asarray(log_prices, dtype=float)
    n = len(y)
    x_hat = np.full(n, np.nan)
    p = 1.0  # initial estimate variance

    # Find first non-NaN
    valid = np.where(~np.isnan(y))[0]
    if len(valid) == 0:
        return x_hat
    start = valid[0]
    x_hat[start] = y[start]

    for t in range(start + 1, n):
        if np.isnan(y[t]):
            x_hat[t] = x_hat[t - 1]
            p += q
            continue
        # Predict
        x_pred = x_hat[t - 1]
        p_pred = p + q
        # Update
        k = p_pred / (p_pred + r)
        x_hat[t] = x_pred + k * (y[t] - x_pred)
        p = (1 - k) * p_pred

    return x_hat


def spectral_power_ratio(log_returns: np.ndarray, window: int = 60) -> np.ndarray:
    """
    For each point, compute the ratio of low-frequency power to total power
    over a trailing window of log returns.
    
    High ratio = more trending behavior (low-freq dominates).
    Low ratio  = more mean-reverting / choppy (high-freq dominates).
    
    Returns array of same length; first (window-1) values are NaN.
    """
    r = np.asarray(log_returns, dtype=float)
    n = len(r)
    out = np.full(n, np.nan)

    for i in range(window - 1, n):
        chunk = r[i - window + 1 : i + 1]
        if np.any(np.isnan(chunk)):
            continue
        # Detrend, then power spectrum
        chunk = chunk - chunk.mean()
        freqs, psd = signal.welch(chunk, nperseg=min(window, 32))
        if psd.sum() == 0:
            continue
        # "Low frequency" = bottom third of frequency bins
        cutoff = len(freqs) // 3
        low_power = psd[:cutoff].sum()
        total_power = psd.sum()
        out[i] = low_power / total_power

    return out


def dsp_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add DSP-flavored features to a per-symbol DataFrame."""
    df = df.copy()
    log_close = np.log(df["close"].values)

    # Kalman-filtered trend (in log-price space)
    df["kalman_logprice"] = kalman_trend(log_close)
    # Deviation of actual price from Kalman trend (mean-reversion signal)
    df["kalman_deviation"] = log_close - df["kalman_logprice"]

    # Volatility regime: 252-day rolling z-score of 20-day vol
    if "vol_20d" in df.columns:
        roll_mean = df["vol_20d"].rolling(252).mean()
        roll_std = df["vol_20d"].rolling(252).std()
        df["vol_regime_z"] = (df["vol_20d"] - roll_mean) / roll_std

    # Spectral power ratio on daily log returns over trailing 60 days
    if "logret_1d" in df.columns:
        df["spectral_low_freq_ratio"] = spectral_power_ratio(
            df["logret_1d"].values, window=60
        )

    return df


# ---------------------------------------------------------------
# CROSS-SECTIONAL FEATURES (across symbols on each date)
# ---------------------------------------------------------------

XS_RANK_COLS = ["ret_5d", "ret_20d", "ret_60d", "ret_120d", "vol_20d"]


def add_cross_sectional_ranks(panel: pd.DataFrame) -> pd.DataFrame:
    """
    For each date, rank every symbol against all others on selected features.
    Returns ranks normalized to [0, 1].
    """
    panel = panel.copy()
    for col in XS_RANK_COLS:
        if col not in panel.columns:
            continue
        panel[f"{col}_xs_rank"] = panel.groupby("timestamp")[col].rank(pct=True)
    return panel


# ---------------------------------------------------------------
# DRIVER
# ---------------------------------------------------------------

def load_all_bars() -> pd.DataFrame:
    """Load every parquet file in BARS_DIR and concatenate."""
    files = sorted(BARS_DIR.glob("*.parquet"))
    if not files:
        raise RuntimeError(f"No parquet files found in {BARS_DIR}")
    frames = []
    for f in tqdm(files, desc="Loading bars"):
        df = pd.read_parquet(f)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def compute_features(panel: pd.DataFrame, include_dsp: bool = True) -> pd.DataFrame:
    """Compute per-symbol features, then cross-sectional ranks."""
    out_frames = []
    grouped = panel.groupby("symbol", sort=False)
    
    for symbol, group in tqdm(grouped, desc="Per-symbol features", total=grouped.ngroups):
        g = basic_features(group)
        if include_dsp:
            g = dsp_features(g)
        out_frames.append(g)
    
    result = pd.concat(out_frames, ignore_index=True)
    result = add_cross_sectional_ranks(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-dsp", action="store_true",
                        help="Skip DSP features (basic only)")
    parser.add_argument("--out", default=str(DATA_DIR / "features.parquet"))
    args = parser.parse_args()

    print("Loading bars from", BARS_DIR)
    panel = load_all_bars()
    print(f"  Loaded: {len(panel):,} rows, {panel['symbol'].nunique()} symbols")
    print(f"  Date range: {panel['timestamp'].min().date()} to {panel['timestamp'].max().date()}")

    print("\nComputing features...")
    features = compute_features(panel, include_dsp=not args.no_dsp)

    print(f"\n  Output shape: {features.shape}")
    print(f"  Columns: {list(features.columns)}")
    
    # Save
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(out_path, index=False)
    
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"\n  Saved to: {out_path} ({size_mb:.1f} MB)")
    
    # Quick sanity check on a sample
    print("\n--- SAMPLE: last 3 rows of AAPL ---")
    sample = features[features["symbol"] == "AAPL"].tail(3)
    # Print only key columns to fit terminal
    show_cols = ["timestamp", "close", "ret_20d", "ret_60d", "vol_20d"]
    if "kalman_deviation" in features.columns:
        show_cols += ["kalman_deviation", "vol_regime_z", "spectral_low_freq_ratio"]
    show_cols += ["ret_20d_xs_rank", "ret_60d_xs_rank"]
    show_cols = [c for c in show_cols if c in sample.columns]
    print(sample[show_cols].to_string(index=False))
    
    # Null audit
    print("\n--- NULL RATES (top 10 worst) ---")
    null_rates = features.isnull().mean().sort_values(ascending=False).head(10)
    print(null_rates.to_string())
    print("\n  (High null rates at the top are expected: long-horizon features")
    print("   need 120+ days of history; DSP features need 252+ days.)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
