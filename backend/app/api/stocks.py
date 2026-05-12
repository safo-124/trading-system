from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep
from app.models.schemas import (
    DividendHistoryResponse,
    DividendHistorySchema,
    FundamentalSchema,
    StockDetailResponse,
    StockListResponse,
    StockSchema,
)
from app.models.tables import DividendHistory, Fundamental, Stock

router = APIRouter()


@router.get("", response_model=StockListResponse)
async def list_stocks(session: SessionDep) -> StockListResponse:
    result = await session.scalars(select(Stock).order_by(Stock.ticker))
    stocks = [StockSchema.model_validate(stock) for stock in result.all()]
    return StockListResponse(stocks=stocks)


@router.get("/{ticker}", response_model=StockDetailResponse)
async def get_stock(ticker: str, session: SessionDep) -> StockDetailResponse:
    normalized_ticker = ticker.upper()
    stock = await session.get(Stock, normalized_ticker)
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")

    latest_fundamental = await _get_latest_fundamental(session, normalized_ticker)
    return StockDetailResponse(
        stock=StockSchema.model_validate(stock),
        latest_fundamentals=(
            FundamentalSchema.model_validate(latest_fundamental)
            if latest_fundamental is not None
            else None
        ),
    )


@router.get("/{ticker}/dividends", response_model=DividendHistoryResponse)
async def get_dividend_history(ticker: str, session: SessionDep) -> DividendHistoryResponse:
    normalized_ticker = ticker.upper()
    stock = await session.get(Stock, normalized_ticker)
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")

    result = await session.scalars(
        select(DividendHistory)
        .where(DividendHistory.ticker == normalized_ticker)
        .order_by(desc(DividendHistory.ex_date))
    )
    dividends = [DividendHistorySchema.model_validate(row) for row in result.all()]
    return DividendHistoryResponse(ticker=normalized_ticker, dividends=dividends)


async def _get_latest_fundamental(session: AsyncSession, ticker: str) -> Fundamental | None:
    return await session.scalar(
        select(Fundamental)
        .where(Fundamental.ticker == ticker)
        .order_by(desc(Fundamental.as_of_date))
        .limit(1)
    )
