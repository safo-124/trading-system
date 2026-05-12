from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
import yfinance as yf
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import get_sessionmaker
from app.models.tables import DividendHistory, Fundamental, Stock

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DividendRow:
    ex_date: date
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class TickerSnapshot:
    ticker: str
    name: str | None
    sector: str | None
    market_cap: int | None
    as_of_date: date
    last_updated: datetime
    dividend_yield: Decimal | None
    payout_ratio: Decimal | None
    fcf: Decimal | None
    debt_to_equity: Decimal | None
    roe: Decimal | None
    profit_margin: Decimal | None
    dividends: list[DividendRow]


@dataclass(frozen=True)
class IngestionResult:
    processed: list[str]
    skipped: dict[str, str]


class IngestionService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self.session_factory = session_factory or get_sessionmaker()

    async def ingest_tickers(self, tickers: Iterable[str]) -> IngestionResult:
        processed: list[str] = []
        skipped: dict[str, str] = {}

        for ticker in _normalize_tickers(tickers):
            try:
                snapshot = await asyncio.to_thread(_fetch_ticker_snapshot, ticker)
                async with self.session_factory() as session:
                    async with session.begin():
                        await _upsert_stock(session, snapshot)
                        await _upsert_dividends(session, snapshot)
                        await _upsert_fundamentals(session, snapshot)
                processed.append(ticker)
                logger.info("Ingested %s", ticker)
            except Exception as exc:
                skipped[ticker] = str(exc)
                logger.exception("Skipping %s after ingestion error", ticker)

        return IngestionResult(processed=processed, skipped=skipped)


def _normalize_tickers(tickers: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()

    for raw_ticker in tickers:
        ticker = raw_ticker.strip().upper()
        if not ticker or ticker in seen:
            continue
        if len(ticker) > 16:
            logger.warning("Skipping %s because it exceeds 16 characters", ticker)
            continue
        normalized.append(ticker)
        seen.add(ticker)

    return normalized


def _fetch_ticker_snapshot(ticker: str) -> TickerSnapshot:
    ticker_client = yf.Ticker(ticker)
    info = _fetch_info(ticker_client)
    dividends = _fetch_dividends(ticker_client, info)

    name = _string_or_none(_first_present(info, ("longName", "shortName", "displayName")))
    sector = _string_or_none(_first_present(info, ("sector",)))
    market_cap = _int_or_none(_first_present(info, ("marketCap",)))

    dividend_yield = _decimal_or_none(
        _first_present(info, ("dividendYield", "trailingAnnualDividendYield"))
    )
    payout_ratio = _decimal_or_none(_first_present(info, ("payoutRatio",)))
    fcf = _decimal_or_none(_first_present(info, ("freeCashflow", "freeCashFlow")))
    debt_to_equity = _decimal_or_none(_first_present(info, ("debtToEquity",)))
    roe = _decimal_or_none(_first_present(info, ("returnOnEquity",)))
    profit_margin = _decimal_or_none(_first_present(info, ("profitMargins",)))

    has_fundamentals = any(
        value is not None
        for value in (
            name,
            sector,
            market_cap,
            dividend_yield,
            payout_ratio,
            fcf,
            debt_to_equity,
            roe,
            profit_margin,
        )
    )
    if not has_fundamentals and not dividends:
        raise ValueError("No usable yfinance data returned")

    now = datetime.now(timezone.utc)
    return TickerSnapshot(
        ticker=ticker,
        name=name,
        sector=sector,
        market_cap=market_cap,
        as_of_date=now.date(),
        last_updated=now,
        dividend_yield=dividend_yield,
        payout_ratio=payout_ratio,
        fcf=fcf,
        debt_to_equity=debt_to_equity,
        roe=roe,
        profit_margin=profit_margin,
        dividends=dividends,
    )


def _fetch_info(ticker_client: yf.Ticker) -> dict[str, Any]:
    try:
        info = ticker_client.get_info()
    except Exception:
        logger.debug("Ticker.get_info failed; falling back to info property", exc_info=True)
        try:
            info = ticker_client.info
        except Exception:
            logger.debug("Ticker.info failed", exc_info=True)
            return {}

    return info if isinstance(info, dict) else {}


def _fetch_dividends(ticker_client: yf.Ticker, info: dict[str, Any]) -> list[DividendRow]:
    try:
        dividends = ticker_client.dividends
    except Exception:
        logger.debug("Ticker.dividends failed; falling back to get_dividends", exc_info=True)
        try:
            dividends = ticker_client.get_dividends()
        except Exception:
            logger.debug("Ticker.get_dividends failed", exc_info=True)
            return []

    if dividends is None or getattr(dividends, "empty", False):
        return []

    currency = _string_or_none(_first_present(info, ("currency", "financialCurrency"))) or "USD"
    currency = currency.upper()[:8]
    rows: list[DividendRow] = []

    for ex_date, amount in dividends.items():
        amount_decimal = _decimal_or_none(amount)
        if amount_decimal is None:
            continue
        rows.append(
            DividendRow(
                ex_date=_date_from_index(ex_date),
                amount=amount_decimal,
                currency=currency,
            )
        )

    return rows


async def _upsert_stock(session: AsyncSession, snapshot: TickerSnapshot) -> None:
    table = Stock.__table__
    statement = insert(table).values(
        ticker=snapshot.ticker,
        name=snapshot.name,
        sector=snapshot.sector,
        market_cap=snapshot.market_cap,
        last_updated=snapshot.last_updated,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[table.c.ticker],
        set_={
            "name": statement.excluded.name,
            "sector": statement.excluded.sector,
            "market_cap": statement.excluded.market_cap,
            "last_updated": statement.excluded.last_updated,
        },
    )
    await session.execute(statement)


async def _upsert_dividends(session: AsyncSession, snapshot: TickerSnapshot) -> None:
    if not snapshot.dividends:
        return

    table = DividendHistory.__table__
    values = [
        {
            "ticker": snapshot.ticker,
            "ex_date": dividend.ex_date,
            "amount": dividend.amount,
            "currency": dividend.currency,
        }
        for dividend in snapshot.dividends
    ]
    statement = insert(table).values(values)
    statement = statement.on_conflict_do_update(
        index_elements=[table.c.ticker, table.c.ex_date],
        set_={
            "amount": statement.excluded.amount,
            "currency": statement.excluded.currency,
        },
    )
    await session.execute(statement)


async def _upsert_fundamentals(session: AsyncSession, snapshot: TickerSnapshot) -> None:
    table = Fundamental.__table__
    statement = insert(table).values(
        {
            "ticker": snapshot.ticker,
            "as_of_date": snapshot.as_of_date,
            "yield": snapshot.dividend_yield,
            "payout_ratio": snapshot.payout_ratio,
            "fcf": snapshot.fcf,
            "debt_to_equity": snapshot.debt_to_equity,
            "roe": snapshot.roe,
            "profit_margin": snapshot.profit_margin,
        }
    )
    statement = statement.on_conflict_do_update(
        index_elements=[table.c.ticker, table.c.as_of_date],
        set_={
            "yield": statement.excluded["yield"],
            "payout_ratio": statement.excluded.payout_ratio,
            "fcf": statement.excluded.fcf,
            "debt_to_equity": statement.excluded.debt_to_equity,
            "roe": statement.excluded.roe,
            "profit_margin": statement.excluded.profit_margin,
        },
    )
    await session.execute(statement)


def _first_present(info: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = info.get(key)
        if not _is_missing(value):
            return value
    return None


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _string_or_none(value: Any) -> str | None:
    if _is_missing(value):
        return None
    text = str(value).strip()
    return text or None


def _int_or_none(value: Any) -> int | None:
    if _is_missing(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _decimal_or_none(value: Any) -> Decimal | None:
    if _is_missing(value):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _date_from_index(value: Any) -> date:
    if hasattr(value, "date"):
        return value.date()
    if isinstance(value, date):
        return value
    return pd.Timestamp(value).date()
