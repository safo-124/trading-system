from fastapi import APIRouter

from app.api import pipeline, predictions, stocks

api_router = APIRouter()
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
