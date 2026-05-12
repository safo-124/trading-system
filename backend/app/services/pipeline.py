from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.paths import ensure_project_root_on_path
from app.models.schemas import PipelineRunResponse, RankedPickResponse
from app.models.tables import DividendHistory, Fundamental, Prediction, Stock

ensure_project_root_on_path()

from shared.pipeline import (  # noqa: E402
    DEFAULT_MODEL_VERSION,
    DividendPayment,
    FundamentalSnapshot,
    build_feature_frame,
    rank_dividend_stocks,
)


class PipelineService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def run(self) -> PipelineRunResponse:
        records = await self._load_universe_records()
        feature_frame = build_feature_frame(records)
        ranked_picks = rank_dividend_stocks(feature_frame, top_n=10)
        predicted_at = datetime.now(timezone.utc)

        prediction_rows = [
            Prediction(
                ticker=pick.ticker,
                model_version=pick.model_version,
                predicted_at=predicted_at,
                cut_probability=_decimal(pick.cut_probability),
                composite_score=_decimal(pick.composite_score),
                recommendation=pick.recommendation,
            )
            for pick in ranked_picks
        ]

        self.session.add_all(prediction_rows)
        await self.session.commit()

        picks = [
            RankedPickResponse(
                rank=pick.rank,
                ticker=pick.ticker,
                model_version=pick.model_version,
                predicted_at=predicted_at,
                cut_probability=_decimal(pick.cut_probability),
                composite_score=_decimal(pick.composite_score),
                recommendation=pick.recommendation,
            )
            for pick in ranked_picks
        ]
        return PipelineRunResponse(
            model_version=DEFAULT_MODEL_VERSION,
            predicted_at=predicted_at,
            picks=picks,
        )

    async def _load_universe_records(self) -> list[FundamentalSnapshot]:
        latest_fundamentals = (
            select(
                Fundamental.ticker,
                func.max(Fundamental.as_of_date).label("as_of_date"),
            )
            .group_by(Fundamental.ticker)
            .subquery()
        )
        result = await self.session.execute(
            select(Stock, Fundamental)
            .join(latest_fundamentals, Stock.ticker == latest_fundamentals.c.ticker)
            .join(
                Fundamental,
                and_(
                    Fundamental.ticker == latest_fundamentals.c.ticker,
                    Fundamental.as_of_date == latest_fundamentals.c.as_of_date,
                ),
            )
            .order_by(Stock.ticker)
        )
        rows = result.all()
        if not rows:
            return []

        tickers = [stock.ticker for stock, _ in rows]
        dividends_by_ticker = await self._load_dividends(tickers)

        return [
            FundamentalSnapshot(
                ticker=stock.ticker,
                name=stock.name,
                sector=stock.sector,
                market_cap=stock.market_cap,
                as_of_date=fundamental.as_of_date,
                dividend_yield=fundamental.dividend_yield,
                payout_ratio=fundamental.payout_ratio,
                fcf=fundamental.fcf,
                debt_to_equity=fundamental.debt_to_equity,
                roe=fundamental.roe,
                profit_margin=fundamental.profit_margin,
                dividends=tuple(dividends_by_ticker[stock.ticker]),
            )
            for stock, fundamental in rows
        ]

    async def _load_dividends(
        self,
        tickers: list[str],
    ) -> dict[str, list[DividendPayment]]:
        dividends_by_ticker: dict[str, list[DividendPayment]] = defaultdict(list)
        result = await self.session.scalars(
            select(DividendHistory)
            .where(DividendHistory.ticker.in_(tickers))
            .order_by(DividendHistory.ticker, DividendHistory.ex_date)
        )

        for dividend in result.all():
            dividends_by_ticker[dividend.ticker].append(
                DividendPayment(
                    ex_date=dividend.ex_date,
                    amount=dividend.amount,
                    currency=dividend.currency,
                )
            )

        return dividends_by_ticker


def _decimal(value: float) -> Decimal:
    return Decimal(str(round(value, 6)))
