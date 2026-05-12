from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class StockSchema(ORMModel):
    ticker: str
    name: str | None = None
    sector: str | None = None
    market_cap: int | None = None
    last_updated: datetime | None = None


class DividendHistorySchema(ORMModel):
    id: int | None = None
    ticker: str
    ex_date: date
    amount: Decimal
    currency: str


class FundamentalSchema(ORMModel):
    id: int | None = None
    ticker: str
    as_of_date: date
    yield_: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("yield", "dividend_yield"),
        serialization_alias="yield",
    )
    payout_ratio: Decimal | None = None
    fcf: Decimal | None = None
    debt_to_equity: Decimal | None = None
    roe: Decimal | None = None
    profit_margin: Decimal | None = None


class PredictionSchema(ORMModel):
    id: int | None = None
    ticker: str
    model_version: str
    predicted_at: datetime
    cut_probability: Decimal | None = None
    composite_score: Decimal | None = None
    recommendation: str | None = None
