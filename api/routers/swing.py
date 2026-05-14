from __future__ import annotations
from datetime import date
from fastapi import APIRouter, HTTPException, Query

from api.schemas import (
    BestPickByDateResponse,
    SwingPredictionsResponse,
    BacktestSummaryResponse,
    LivePredictionResponse,
)
from api.services import (
    swing_latest_predictions,
    backtest_summary_payload,
    get_live_predictions,
    best_pick_by_date_payload,
)

router = APIRouter(prefix="/swing", tags=["swing"])


@router.get("/predictions/latest", response_model=SwingPredictionsResponse)
def get_latest_predictions(n_per_side: int = Query(20, ge=1, le=100)):
    """Top/bottom N picks for the most recent prediction day."""
    payload = swing_latest_predictions(n_per_side=n_per_side)
    if payload["as_of"] is None:
        raise HTTPException(
            status_code=404,
            detail="No predictions available. Run swing pipeline first.",
        )
    return payload


@router.get("/backtest", response_model=BacktestSummaryResponse)
def get_backtest_summary():
    """Walk-forward backtest summary + last 30 days of daily returns."""
    payload = backtest_summary_payload()
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail="No backtest results. Run: python -m swing.backtest",
        )
    return payload


@router.get("/best_by_date", response_model=BestPickByDateResponse)
def get_best_pick_by_date(date_: date = Query(..., alias="date")):
    """
    Best cross-market long candidate for a selected calendar date.
    
    Uses the latest available trading date on or before the requested date
    in each market, then picks the highest model prediction globally.
    """
    payload = best_pick_by_date_payload(date_)
    if payload["global_best"] is None:
        raise HTTPException(
            status_code=404,
            detail="No predictions available on or before requested date.",
        )
    return payload


@router.get("/predict_today", response_model=LivePredictionResponse)
def predict_today(
    n_per_side: int = Query(20, ge=1, le=100),
    force_refresh: bool = Query(False, description="Bypass 15-min cache"),
):
    """
    Run production model on FRESH market data. Returns today's picks.
    
    First call: 3-5 minutes (fetches from yfinance). 
    Subsequent calls within 15 minutes: <1 second (cached).
    """
    try:
        return get_live_predictions(n_per_side=n_per_side, force_refresh=force_refresh)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Live prediction failed: {type(e).__name__}: {e}")
