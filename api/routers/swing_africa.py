from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query

from api.schemas import (
    SwingAfricaPredictionsResponse,
    SwingAfricaBacktestResponse,
    SwingAfricaLivePredictionResponse,
)
from api.services import (
    swing_africa_latest_predictions,
    swing_africa_backtest_summary_payload,
    get_africa_live_predictions,
)

router = APIRouter(prefix="/swing_africa", tags=["swing_africa"])


@router.get("/predictions/latest", response_model=SwingAfricaPredictionsResponse)
def get_latest_africa_predictions(n_per_side: int = Query(5, ge=1, le=30)):
    """Top/bottom N JSE picks for the most recent historical prediction day."""
    payload = swing_africa_latest_predictions(n_per_side=n_per_side)
    if payload["as_of"] is None:
        raise HTTPException(status_code=404, detail="No Africa predictions.")
    return payload


@router.get("/backtest", response_model=SwingAfricaBacktestResponse)
def get_africa_backtest_summary():
    """Africa walk-forward backtest summary."""
    payload = swing_africa_backtest_summary_payload()
    if payload is None:
        raise HTTPException(status_code=404, detail="No Africa backtest results.")
    return payload


@router.get("/predict_today", response_model=SwingAfricaLivePredictionResponse)
def predict_today_africa(
    n_per_side: int = Query(5, ge=1, le=30),
    force_refresh: bool = Query(False),
):
    """Run Africa production model on fresh JSE market data."""
    try:
        return get_africa_live_predictions(n_per_side=n_per_side, force_refresh=force_refresh)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Africa live prediction failed: {type(e).__name__}: {e}")
