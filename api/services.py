"""Service layer — loads parquet/CSV and produces Pydantic models."""
from __future__ import annotations
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from api.config import (
    DIVIDEND_PICKS_PATH,
    PREDICTIONS_PATH,
    BACKTEST_RESULTS_PATH,
)


# ---------- Dividend ----------

def load_dividend_picks() -> pd.DataFrame:
    """Load latest dividend picks CSV. Returns empty DataFrame if missing."""
    if not DIVIDEND_PICKS_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(DIVIDEND_PICKS_PATH)


def dividend_picks_payload() -> dict:
    df = load_dividend_picks()
    if df.empty:
        return {"generated_at": None, "n_picks": 0, "picks": []}
    
    generated_at = datetime.fromtimestamp(DIVIDEND_PICKS_PATH.stat().st_mtime)
    
    picks = []
    for _, row in df.iterrows():
        picks.append({
            "ticker": row["ticker"],
            "yield": float(row.get("yield", 0)) if pd.notna(row.get("yield", 0)) else 0.0,
            "payout_ratio": float(row.get("payout_ratio", 0)) if pd.notna(row.get("payout_ratio", 0)) else 0.0,
            "div_cagr_5y": float(row.get("div_cagr_5y", 0)) if pd.notna(row.get("div_cagr_5y", 0)) else 0.0,
            "consec_increases": int(row.get("consec_increases", 0)) if pd.notna(row.get("consec_increases", 0)) else 0,
            "fcf_coverage": float(row.get("fcf_coverage", 0)) if pd.notna(row.get("fcf_coverage", 0)) else 0.0,
            "safety_score": float(row.get("safety_score", 0)) if pd.notna(row.get("safety_score", 0)) else 0.0,
            "composite_score": float(row.get("composite_score", 0)) if pd.notna(row.get("composite_score", 0)) else 0.0,
        })
    return {
        "generated_at": generated_at,
        "n_picks": len(picks),
        "picks": picks,
    }


# ---------- Swing predictions ----------

@lru_cache(maxsize=1)
def _load_predictions_cached() -> pd.DataFrame:
    """Cache the predictions parquet in memory (~50 MB)."""
    if not PREDICTIONS_PATH.exists():
        return pd.DataFrame()
    df = pd.read_parquet(PREDICTIONS_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def swing_latest_predictions(n_per_side: int = 20) -> dict:
    df = _load_predictions_cached()
    if df.empty:
        return {"as_of": None, "n_stocks": 0, "long_picks": [], "short_picks": []}
    
    last_day = df["timestamp"].max()
    day_df = df[df["timestamp"] == last_day].copy()
    
    long_df = day_df.nlargest(n_per_side, "pred")
    short_df = day_df.nsmallest(n_per_side, "pred")
    
    def to_records(d: pd.DataFrame) -> list[dict]:
        rows = []
        for _, row in d.iterrows():
            rows.append({
                "timestamp": row["timestamp"].date(),
                "symbol": row["symbol"],
                "pred": float(row["pred"]),
                "fwd_ret_5d": float(row["fwd_ret_5d"]) if pd.notna(row["fwd_ret_5d"]) else None,
            })
        return rows
    
    return {
        "as_of": last_day.date(),
        "n_stocks": len(day_df),
        "long_picks": to_records(long_df),
        "short_picks": to_records(short_df),
    }


# ---------- Backtest ----------

@lru_cache(maxsize=1)
def _load_backtest_cached() -> pd.DataFrame:
    if not BACKTEST_RESULTS_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(BACKTEST_RESULTS_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def backtest_summary_payload() -> dict:
    df = _load_backtest_cached()
    if df.empty:
        return None
    
    gross = df["daily_ret_gross"].dropna()
    net = df["daily_ret_net"].dropna()
    
    def annualize_ret(r: pd.Series) -> float:
        return float(r.mean() * 252)
    
    def annualize_vol(r: pd.Series) -> float:
        return float(r.std() * np.sqrt(252))
    
    def sharpe(r: pd.Series) -> float:
        v = annualize_vol(r)
        return float(annualize_ret(r) / v) if v > 0 else 0.0
    
    def max_dd(r: pd.Series) -> float:
        nav = (1 + r).cumprod()
        peak = nav.cummax()
        return float(((nav - peak) / peak).min())
    
    summary = {
        "n_days": len(df),
        "start_date": df["timestamp"].min().date(),
        "end_date": df["timestamp"].max().date(),
        "ann_return_gross": annualize_ret(gross),
        "ann_return_net": annualize_ret(net),
        "ann_vol": annualize_vol(net),
        "sharpe_gross": sharpe(gross),
        "sharpe_net": sharpe(net),
        "max_drawdown_net": max_dd(net),
        "hit_rate_net": float((net > 0).mean()),
        "total_return_net": float((1 + net).cumprod().iloc[-1] - 1),
    }
    
    last_30 = df.tail(30).copy()
    last_30_records = []
    for _, row in last_30.iterrows():
        last_30_records.append({
            "timestamp": row["timestamp"].date(),
            "daily_ret_gross": float(row["daily_ret_gross"]),
            "daily_ret_net": float(row["daily_ret_net"]),
            "long_ret": float(row["long_ret"]),
            "short_ret": float(row["short_ret"]),
        })
    
    return {"summary": summary, "last_30_days": last_30_records}


def clear_caches() -> None:
    """Call after underlying files are regenerated."""
    _load_predictions_cached.cache_clear()
    _load_backtest_cached.cache_clear()
