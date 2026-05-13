from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query

from api.schemas import (
    SwingEUPredictionsResponse,
    SwingEUBacktestResponse,
    SwingEULivePredictionResponse,
)
from api.services import (
    swing_eu_latest_predictions,
    swing_eu_backtest_summary_payload,
    get_eu_live_predictions,
)

router = APIRouter(prefix="/swing_eu", tags=["swing_eu"])


@router.get("/predictions/latest", response_model=SwingEUPredictionsResponse)
def get_latest_eu_predictions(n_per_side: int = Query(20, ge=1, le=100)):
    """Top/bottom N European picks for the most recent historical prediction day."""
    payload = swing_eu_latest_predictions(n_per_side=n_per_side)
    if payload["as_of"] is None:
        raise HTTPException(
            status_code=404,
            detail="No EU predictions. Run swing_eu pipeline.",
        )
    return payload


@router.get("/backtest", response_model=SwingEUBacktestResponse)
def get_eu_backtest_summary():
    """EU walk-forward backtest summary."""
    payload = swing_eu_backtest_summary_payload()
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail="No EU backtest results. Run: python -m swing_eu.backtest",
        )
    return payload


@router.get("/predict_today", response_model=SwingEULivePredictionResponse)
def predict_today_eu(
    n_per_side: int = Query(20, ge=1, le=100),
    force_refresh: bool = Query(False),
):
    """Run EU production model on fresh European market data."""
    try:
        return get_eu_live_predictions(n_per_side=n_per_side, force_refresh=force_refresh)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EU live prediction failed: {type(e).__name__}: {e}")
