"""Pydantic response models. Strict typing for every endpoint."""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


# ---------- Common ----------

class HealthResponse(BaseModel):
    status: str
    api_version: str
    data_files: dict[str, bool]


# ---------- Dividend ----------

class DividendPick(BaseModel):
    ticker: str
    yield_: float = Field(..., alias="yield")
    payout_ratio: float
    div_cagr_5y: float
    consec_increases: int
    fcf_coverage: float
    safety_score: float
    composite_score: float
    
    model_config = {"populate_by_name": True}


class DividendPicksResponse(BaseModel):
    generated_at: Optional[datetime] = None
    n_picks: int
    picks: list[DividendPick]


# ---------- Swing strategy ----------

class SwingPrediction(BaseModel):
    timestamp: date
    symbol: str
    pred: float
    fwd_ret_5d: Optional[float] = None


class SwingPredictionsResponse(BaseModel):
    as_of: date
    n_stocks: int
    long_picks: list[SwingPrediction]  # top N by pred (highest = LONG)
    short_picks: list[SwingPrediction]  # bottom N by pred (lowest = SHORT)


class BacktestDayRecord(BaseModel):
    timestamp: date
    daily_ret_gross: float
    daily_ret_net: float
    long_ret: float
    short_ret: float


class BacktestSummary(BaseModel):
    n_days: int
    start_date: date
    end_date: date
    ann_return_gross: float
    ann_return_net: float
    ann_vol: float
    sharpe_gross: float
    sharpe_net: float
    max_drawdown_net: float
    hit_rate_net: float
    total_return_net: float


class BacktestSummaryResponse(BaseModel):
    summary: BacktestSummary
    last_30_days: list[BacktestDayRecord]
