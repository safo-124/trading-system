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


class LivePick(BaseModel):
    timestamp: date
    symbol: str
    pred: float
    close: float


class LivePredictionResponse(BaseModel):
    as_of: date
    n_stocks_predicted: int
    model_trained_at: Optional[str] = None
    universe_size: int
    long_picks: list[LivePick]
    short_picks: list[LivePick]


class DatedBestPick(BaseModel):
    market_key: str
    market_label: str
    region: str
    benchmark: str
    timestamp: date
    symbol: str
    pred: float
    fwd_ret_5d: Optional[float] = None


class BestPickByDateResponse(BaseModel):
    requested_date: date
    global_best: Optional[DatedBestPick] = None
    market_picks: list[DatedBestPick]
    n_markets: int
    n_candidates: int


# ---------- European swing strategy ----------

class SwingEUPrediction(BaseModel):
    timestamp: date
    symbol: str
    pred: float
    fwd_ret_5d: Optional[float] = None


class SwingEUPredictionsResponse(BaseModel):
    as_of: date
    n_stocks: int
    long_picks: list[SwingEUPrediction]
    short_picks: list[SwingEUPrediction]


class SwingEUBacktestSummary(BaseModel):
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


class SwingEUBacktestResponse(BaseModel):
    summary: SwingEUBacktestSummary


class SwingEULivePick(BaseModel):
    timestamp: date
    symbol: str
    pred: float
    close: float


class SwingEULivePredictionResponse(BaseModel):
    as_of: date
    n_stocks_predicted: int
    model_trained_at: Optional[str] = None
    universe_size: int
    long_picks: list[SwingEULivePick]
    short_picks: list[SwingEULivePick]


# ---------- African swing strategy ----------

class SwingAfricaPrediction(BaseModel):
    timestamp: date
    symbol: str
    pred: float
    fwd_ret_5d: Optional[float] = None


class SwingAfricaPredictionsResponse(BaseModel):
    as_of: date
    n_stocks: int
    long_picks: list[SwingAfricaPrediction]
    short_picks: list[SwingAfricaPrediction]


class SwingAfricaBacktestSummary(BaseModel):
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


class SwingAfricaBacktestResponse(BaseModel):
    summary: SwingAfricaBacktestSummary


class SwingAfricaLivePick(BaseModel):
    timestamp: date
    symbol: str
    pred: float
    close: float


class SwingAfricaLivePredictionResponse(BaseModel):
    as_of: date
    n_stocks_predicted: int
    model_trained_at: Optional[str] = None
    universe_size: int
    long_picks: list[SwingAfricaLivePick]
    short_picks: list[SwingAfricaLivePick]
