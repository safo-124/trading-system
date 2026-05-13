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


# ---------- Live swing prediction ----------

import time as _time

_LIVE_CACHE: dict = {"timestamp": None, "payload": None}
_LIVE_CACHE_TTL_SEC = 900  # 15 minutes


def get_live_predictions(n_per_side: int = 20, force_refresh: bool = False) -> dict:
    """Run live prediction or return cached result (15-min TTL)."""
    from datetime import date as _date
    from swing.predict_live import predict_latest
    
    now = _time.time()
    cached_at = _LIVE_CACHE["timestamp"]
    
    if (
        not force_refresh
        and cached_at is not None
        and (now - cached_at) < _LIVE_CACHE_TTL_SEC
        and _LIVE_CACHE["payload"] is not None
    ):
        return _LIVE_CACHE["payload"]
    
    result = predict_latest(universe_size=None, n_per_side=n_per_side)
    # Convert ISO date strings to date objects for Pydantic
    result["as_of"] = _date.fromisoformat(result["as_of"])
    result["universe_size"] = result.get("n_stocks_predicted", 0)
    for picks_key in ("long_picks", "short_picks"):
        for p in result[picks_key]:
            p["timestamp"] = _date.fromisoformat(p["timestamp"])
    
    _LIVE_CACHE["timestamp"] = now
    _LIVE_CACHE["payload"] = result
    return result


# ---------- EU swing services ----------

from pathlib import Path as _Path

_EU_DATA_DIR = _Path(__file__).resolve().parent.parent / "data_eu"
_EU_PREDICTIONS_PATH = _EU_DATA_DIR / "predictions.parquet"
_EU_BACKTEST_PATH = _EU_DATA_DIR / "backtest_results.csv"


@lru_cache(maxsize=1)
def _load_eu_predictions_cached() -> pd.DataFrame:
    if not _EU_PREDICTIONS_PATH.exists():
        return pd.DataFrame()
    df = pd.read_parquet(_EU_PREDICTIONS_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@lru_cache(maxsize=1)
def _load_eu_backtest_cached() -> pd.DataFrame:
    if not _EU_BACKTEST_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(_EU_BACKTEST_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def swing_eu_latest_predictions(n_per_side: int = 20) -> dict:
    df = _load_eu_predictions_cached()
    if df.empty:
        return {"as_of": None, "n_stocks": 0, "long_picks": [], "short_picks": []}
    
    last_day = df["timestamp"].max()
    day_df = df[df["timestamp"] == last_day].copy()
    
    long_df = day_df.nlargest(n_per_side, "pred")
    short_df = day_df.nsmallest(n_per_side, "pred")
    
    def to_records(d):
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


def swing_eu_backtest_summary_payload() -> dict | None:
    df = _load_eu_backtest_cached()
    if df.empty:
        return None
    
    gross = df["daily_ret_gross"].dropna()
    net = df["daily_ret_net"].dropna()
    
    def _ann_ret(r): return float(r.mean() * 252)
    def _ann_vol(r): return float(r.std() * np.sqrt(252))
    def _sharpe(r):
        v = _ann_vol(r)
        return float(_ann_ret(r) / v) if v > 0 else 0.0
    def _max_dd(r):
        nav = (1 + r).cumprod()
        peak = nav.cummax()
        return float(((nav - peak) / peak).min())
    
    return {
        "summary": {
            "n_days": len(df),
            "start_date": df["timestamp"].min().date(),
            "end_date": df["timestamp"].max().date(),
            "ann_return_gross": _ann_ret(gross),
            "ann_return_net": _ann_ret(net),
            "ann_vol": _ann_vol(net),
            "sharpe_gross": _sharpe(gross),
            "sharpe_net": _sharpe(net),
            "max_drawdown_net": _max_dd(net),
            "hit_rate_net": float((net > 0).mean()),
            "total_return_net": float((1 + net).cumprod().iloc[-1] - 1),
        }
    }


# Live EU prediction with caching (15-min TTL)
_EU_LIVE_CACHE: dict = {"timestamp": None, "payload": None}


def get_eu_live_predictions(n_per_side: int = 20, force_refresh: bool = False) -> dict:
    from datetime import date as _date
    from swing_eu.predict_live import predict_latest as eu_predict_latest
    
    now = _time.time()
    cached_at = _EU_LIVE_CACHE["timestamp"]
    
    if (
        not force_refresh
        and cached_at is not None
        and (now - cached_at) < _LIVE_CACHE_TTL_SEC
        and _EU_LIVE_CACHE["payload"] is not None
    ):
        return _EU_LIVE_CACHE["payload"]
    
    result = eu_predict_latest(universe_size=None, n_per_side=n_per_side)
    result["as_of"] = _date.fromisoformat(result["as_of"])
    result["universe_size"] = result.get("n_stocks_predicted", 0)
    for picks_key in ("long_picks", "short_picks"):
        for p in result[picks_key]:
            p["timestamp"] = _date.fromisoformat(p["timestamp"])
    
    _EU_LIVE_CACHE["timestamp"] = now
    _EU_LIVE_CACHE["payload"] = result
    return result


# ---------- Africa swing services ----------

_AFRICA_DATA_DIR = _Path(__file__).resolve().parent.parent / "data_africa"
_AFRICA_PREDICTIONS_PATH = _AFRICA_DATA_DIR / "predictions.parquet"
_AFRICA_BACKTEST_PATH = _AFRICA_DATA_DIR / "backtest_results.csv"


@lru_cache(maxsize=1)
def _load_africa_predictions_cached() -> pd.DataFrame:
    if not _AFRICA_PREDICTIONS_PATH.exists():
        return pd.DataFrame()
    df = pd.read_parquet(_AFRICA_PREDICTIONS_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@lru_cache(maxsize=1)
def _load_africa_backtest_cached() -> pd.DataFrame:
    if not _AFRICA_BACKTEST_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(_AFRICA_BACKTEST_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def swing_africa_latest_predictions(n_per_side: int = 5) -> dict:
    df = _load_africa_predictions_cached()
    if df.empty:
        return {"as_of": None, "n_stocks": 0, "long_picks": [], "short_picks": []}
    last_day = df["timestamp"].max()
    day_df = df[df["timestamp"] == last_day].copy()
    long_df = day_df.nlargest(n_per_side, "pred")
    short_df = day_df.nsmallest(n_per_side, "pred")
    def to_records(d):
        return [
            {
                "timestamp": row["timestamp"].date(),
                "symbol": row["symbol"],
                "pred": float(row["pred"]),
                "fwd_ret_5d": float(row["fwd_ret_5d"]) if pd.notna(row["fwd_ret_5d"]) else None,
            }
            for _, row in d.iterrows()
        ]
    return {
        "as_of": last_day.date(),
        "n_stocks": len(day_df),
        "long_picks": to_records(long_df),
        "short_picks": to_records(short_df),
    }


def swing_africa_backtest_summary_payload() -> dict | None:
    df = _load_africa_backtest_cached()
    if df.empty:
        return None
    gross = df["daily_ret_gross"].dropna()
    net = df["daily_ret_net"].dropna()
    def _ann_ret(r): return float(r.mean() * 252)
    def _ann_vol(r): return float(r.std() * np.sqrt(252))
    def _sharpe(r):
        v = _ann_vol(r)
        return float(_ann_ret(r) / v) if v > 0 else 0.0
    def _max_dd(r):
        nav = (1 + r).cumprod()
        peak = nav.cummax()
        return float(((nav - peak) / peak).min())
    return {
        "summary": {
            "n_days": len(df),
            "start_date": df["timestamp"].min().date(),
            "end_date": df["timestamp"].max().date(),
            "ann_return_gross": _ann_ret(gross),
            "ann_return_net": _ann_ret(net),
            "ann_vol": _ann_vol(net),
            "sharpe_gross": _sharpe(gross),
            "sharpe_net": _sharpe(net),
            "max_drawdown_net": _max_dd(net),
            "hit_rate_net": float((net > 0).mean()),
            "total_return_net": float((1 + net).cumprod().iloc[-1] - 1),
        }
    }


_AFRICA_LIVE_CACHE: dict = {"timestamp": None, "payload": None}


def get_africa_live_predictions(n_per_side: int = 5, force_refresh: bool = False) -> dict:
    from datetime import date as _date
    from swing_africa.predict_live import predict_latest as africa_predict_latest
    now = _time.time()
    cached_at = _AFRICA_LIVE_CACHE["timestamp"]
    if (
        not force_refresh
        and cached_at is not None
        and (now - cached_at) < _LIVE_CACHE_TTL_SEC
        and _AFRICA_LIVE_CACHE["payload"] is not None
    ):
        return _AFRICA_LIVE_CACHE["payload"]
    result = africa_predict_latest(universe_size=None, n_per_side=n_per_side)
    result["as_of"] = _date.fromisoformat(result["as_of"])
    result["universe_size"] = result.get("n_stocks_predicted", 0)
    for picks_key in ("long_picks", "short_picks"):
        for p in result[picks_key]:
            p["timestamp"] = _date.fromisoformat(p["timestamp"])
    _AFRICA_LIVE_CACHE["timestamp"] = now
    _AFRICA_LIVE_CACHE["payload"] = result
    return result
