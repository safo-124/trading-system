from __future__ import annotations
from fastapi import APIRouter, HTTPException

from api.schemas import DividendPicksResponse
from api.services import dividend_picks_payload

router = APIRouter(prefix="/dividend", tags=["dividend"])


@router.get("/picks", response_model=DividendPicksResponse)
def get_dividend_picks():
    """Latest picks from the rules-based dividend screener."""
    payload = dividend_picks_payload()
    if payload["n_picks"] == 0:
        raise HTTPException(
            status_code=404,
            detail=(
                "No dividend picks found. "
                "Run: python research/dividend_pipeline.py"
            ),
        )
    return payload
