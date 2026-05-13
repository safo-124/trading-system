"""
yfinance wrapper for daily OHLCV bars.
Free, no API key, well-tested.
"""

from __future__ import annotations
from datetime import datetime
import pandas as pd
import yfinance as yf


def fetch_daily_bars(
    symbol: str,
    start: str | datetime,
    end: str | datetime | None = None,
) -> pd.DataFrame:
    """
    Fetch daily OHLCV from yfinance. Returns DataFrame with columns:
        timestamp, open, high, low, close, volume, symbol
    
    Returns empty DataFrame if no data.
    Raises RuntimeError on errors (caller decides how to handle).
    """
    if isinstance(start, datetime):
        start = start.strftime("%Y-%m-%d")
    if isinstance(end, datetime):
        end = end.strftime("%Y-%m-%d")
    
    try:
        t = yf.Ticker(symbol)
        df = t.history(start=start, end=end, auto_adjust=True)
    except Exception as e:
        raise RuntimeError(f"yfinance fetch failed for {symbol}: {e}") from e
    
    if df is None or df.empty:
        return pd.DataFrame()
    
    df = df.reset_index()
    # yfinance returns: Date, Open, High, Low, Close, Volume, Dividends, Stock Splits
    # Normalize to lowercase + rename Date -> timestamp
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={"date": "timestamp"})
    df["symbol"] = symbol
    
    # Make timestamp tz-naive for consistent parquet storage
    if pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        if df["timestamp"].dt.tz is not None:
            df["timestamp"] = df["timestamp"].dt.tz_localize(None)
    
    # Keep only the columns we need (drop dividends/splits since auto_adjust=True already applied them)
    keep_cols = ["timestamp", "open", "high", "low", "close", "volume", "symbol"]
    df = df[[c for c in keep_cols if c in df.columns]]
    
    return df
