from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import desc, func, select

from app.api.deps import SessionDep
from app.models.schemas import LatestPredictionsResponse, RankedPickResponse
from app.models.tables import Prediction

router = APIRouter()


@router.get("/latest", response_model=LatestPredictionsResponse)
async def get_latest_predictions(session: SessionDep) -> LatestPredictionsResponse:
    latest_predicted_at = await session.scalar(select(func.max(Prediction.predicted_at)))
    if latest_predicted_at is None:
        return LatestPredictionsResponse(predictions=[])

    result = await session.scalars(
        select(Prediction)
        .where(Prediction.predicted_at == latest_predicted_at)
        .order_by(desc(Prediction.composite_score).nullslast(), Prediction.ticker)
        .limit(10)
    )

    predictions = [
        RankedPickResponse(
            rank=rank,
            ticker=prediction.ticker,
            model_version=prediction.model_version,
            predicted_at=prediction.predicted_at,
            cut_probability=prediction.cut_probability or Decimal("0"),
            composite_score=prediction.composite_score or Decimal("0"),
            recommendation=prediction.recommendation or "UNKNOWN",
        )
        for rank, prediction in enumerate(result.all(), start=1)
    ]
    return LatestPredictionsResponse(predictions=predictions)
