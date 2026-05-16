from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import Literal

from api.schemas import (
    GhanaScoreResponse,
    GhanaRecommendationResponse,
    GhanaFundamentalsResponse,
)
from api.services import (
    ghana_score_payload,
    ghana_recommend_payload,
    ghana_fundamentals_payload,
)

router = APIRouter(prefix="/ghana", tags=["ghana"])


@router.get("/score", response_model=GhanaScoreResponse)
def get_ghana_score():
    """
    Current GSE fundamental quality ranking. 40 stocks, ranked by
    composite quality score (value + profitability + income + momentum).
    Eligible=False means the stock failed liquidity or P/E integrity gates.
    """
    payload = ghana_score_payload()
    if payload["n_stocks"] == 0:
        raise HTTPException(
            status_code=404,
            detail="No Ghana score data. Run: python -m ghana.scorer"
        )
    return payload


@router.get("/recommend", response_model=GhanaRecommendationResponse)
def get_ghana_recommendation(
    budget_usd: float | None = Query(None, ge=50, le=1_000_000,
        description="Budget in USD (mutually exclusive with budget_ghs)"),
    budget_ghs: float | None = Query(None, ge=500, le=10_000_000,
        description="Budget in Ghana cedis"),
    horizon_years: int = Query(5, ge=1, le=20,
        description="Investment horizon in years"),
    risk_tolerance: Literal["low", "medium", "high"] = Query("medium"),
):
    """
    Recommended GSE portfolio for a given budget, horizon, and risk level.

    Returns positions with whole-share quantities, GHS and USD costs, and
    liquidity-capped notes. The cash_residual field shows how much budget
    couldn't be deployed due to GSE liquidity limits -- this is intentional
    honesty, not a bug.

    Provide EITHER budget_usd or budget_ghs (not both).
    """
    if budget_usd is None and budget_ghs is None:
        raise HTTPException(
            status_code=422,
            detail="Provide either budget_usd or budget_ghs"
        )
    if budget_usd is not None and budget_ghs is not None:
        raise HTTPException(
            status_code=422,
            detail="Provide only one of budget_usd or budget_ghs, not both"
        )
    try:
        return ghana_recommend_payload(
            budget_usd=budget_usd,
            budget_ghs=budget_ghs,
            horizon_years=horizon_years,
            risk_tolerance=risk_tolerance,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation failed: {type(e).__name__}: {e}"
        )


@router.get("/fundamentals", response_model=GhanaFundamentalsResponse)
def get_ghana_fundamentals():
    """
    Raw fundamental data for all 40 GSE-listed stocks (price, EPS, P/E,
    dividend, returns, average volume). The data underlying the scorer.
    """
    payload = ghana_fundamentals_payload()
    if payload["n_stocks"] == 0:
        raise HTTPException(
            status_code=404,
            detail="No Ghana fundamentals. Run: python -m ghana.fundamental_scraper"
        )
    return payload
