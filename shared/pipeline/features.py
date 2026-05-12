from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "dividend_yield",
    "payout_ratio",
    "fcf",
    "debt_to_equity",
    "roe",
    "profit_margin",
    "market_cap_log",
    "annual_dividend",
    "dividend_count_ltm",
    "dividend_growth_ltm",
    "dividend_streak_years",
    "dividend_volatility",
]


@dataclass(frozen=True)
class DividendPayment:
    ex_date: date
    amount: Decimal | float | int
    currency: str = "USD"


@dataclass(frozen=True)
class FundamentalSnapshot:
    ticker: str
    as_of_date: date
    name: str | None = None
    sector: str | None = None
    market_cap: int | None = None
    dividend_yield: Decimal | float | int | None = None
    payout_ratio: Decimal | float | int | None = None
    fcf: Decimal | float | int | None = None
    debt_to_equity: Decimal | float | int | None = None
    roe: Decimal | float | int | None = None
    profit_margin: Decimal | float | int | None = None
    dividends: Sequence[DividendPayment] = field(default_factory=tuple)


def build_feature_frame(records: Sequence[FundamentalSnapshot]) -> pd.DataFrame:
    rows = [_snapshot_to_row(record) for record in records]
    if not rows:
        return pd.DataFrame(columns=["ticker", *FEATURE_COLUMNS])

    frame = pd.DataFrame(rows)
    for column in FEATURE_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    return frame


def _snapshot_to_row(snapshot: FundamentalSnapshot) -> dict[str, Any]:
    dividend_metrics = _dividend_metrics(snapshot.dividends, snapshot.as_of_date)
    market_cap = _as_float(snapshot.market_cap)
    debt_to_equity = _normalize_debt_to_equity(_as_float(snapshot.debt_to_equity))

    return {
        "ticker": snapshot.ticker,
        "name": snapshot.name,
        "sector": snapshot.sector,
        "as_of_date": snapshot.as_of_date,
        "dividend_yield": _as_float(snapshot.dividend_yield),
        "payout_ratio": _as_float(snapshot.payout_ratio),
        "fcf": _as_float(snapshot.fcf),
        "debt_to_equity": debt_to_equity,
        "roe": _as_float(snapshot.roe),
        "profit_margin": _as_float(snapshot.profit_margin),
        "market_cap_log": np.log1p(market_cap) if market_cap is not None and market_cap > 0 else np.nan,
        **dividend_metrics,
    }


def _dividend_metrics(
    dividends: Sequence[DividendPayment],
    as_of_date: date,
) -> dict[str, float]:
    valid_payments = sorted(
        (
            (payment.ex_date, _as_float(payment.amount))
            for payment in dividends
            if _as_float(payment.amount) is not None and payment.ex_date <= as_of_date
        ),
        key=lambda item: item[0],
    )

    if not valid_payments:
        return {
            "annual_dividend": 0.0,
            "dividend_count_ltm": 0.0,
            "dividend_growth_ltm": np.nan,
            "dividend_streak_years": 0.0,
            "dividend_volatility": np.nan,
        }

    ltm_start = as_of_date - timedelta(days=365)
    previous_start = as_of_date - timedelta(days=730)
    ltm_amounts = [amount for ex_date, amount in valid_payments if ltm_start < ex_date <= as_of_date]
    previous_amounts = [
        amount for ex_date, amount in valid_payments if previous_start < ex_date <= ltm_start
    ]

    annual_dividend = float(sum(ltm_amounts))
    previous_annual_dividend = float(sum(previous_amounts))
    if previous_annual_dividend > 0:
        dividend_growth = (annual_dividend - previous_annual_dividend) / previous_annual_dividend
    else:
        dividend_growth = np.nan

    recent_amounts = [amount for _, amount in valid_payments[-8:]]
    mean_recent = float(np.mean(recent_amounts)) if recent_amounts else 0.0
    volatility = (
        float(np.std(recent_amounts) / mean_recent)
        if len(recent_amounts) > 1 and mean_recent > 0
        else 0.0
    )

    return {
        "annual_dividend": annual_dividend,
        "dividend_count_ltm": float(len(ltm_amounts)),
        "dividend_growth_ltm": dividend_growth,
        "dividend_streak_years": float(_dividend_streak_years(valid_payments, as_of_date)),
        "dividend_volatility": volatility,
    }


def _dividend_streak_years(
    payments: Sequence[tuple[date, float]],
    as_of_date: date,
) -> int:
    paid_years = {ex_date.year for ex_date, amount in payments if amount > 0}
    streak = 0

    for year in range(as_of_date.year, as_of_date.year - 100, -1):
        if year not in paid_years:
            break
        streak += 1

    return streak


def _normalize_debt_to_equity(value: float | None) -> float | None:
    if value is None:
        return None
    return value / 100 if abs(value) > 10 else value


def _as_float(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None
