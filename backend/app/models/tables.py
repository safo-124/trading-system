from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Stock(Base):
    __tablename__ = "stocks"

    ticker: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255))
    sector: Mapped[str | None] = mapped_column(String(255))
    market_cap: Mapped[int | None] = mapped_column(BigInteger)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    dividend_history: Mapped[list["DividendHistory"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
    )
    fundamentals: Mapped[list["Fundamental"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
    )


class DividendHistory(Base):
    __tablename__ = "dividend_history"
    __table_args__ = (
        UniqueConstraint("ticker", "ex_date", name="uq_dividend_history_ticker_ex_date"),
        Index("ix_dividend_history_ticker", "ticker"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    ticker: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("stocks.ticker", ondelete="CASCADE"),
        nullable=False,
    )
    ex_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)

    stock: Mapped[Stock] = relationship(back_populates="dividend_history")


class Fundamental(Base):
    __tablename__ = "fundamentals"
    __table_args__ = (
        UniqueConstraint("ticker", "as_of_date", name="uq_fundamentals_ticker_as_of_date"),
        Index("ix_fundamentals_ticker", "ticker"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    ticker: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("stocks.ticker", ondelete="CASCADE"),
        nullable=False,
    )
    as_of_date: Mapped[date] = mapped_column(Date, primary_key=True)
    dividend_yield: Mapped[Decimal | None] = mapped_column("yield", Numeric(10, 6))
    payout_ratio: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    fcf: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    debt_to_equity: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    roe: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    profit_margin: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))

    stock: Mapped[Stock] = relationship(back_populates="fundamentals")


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        Index("ix_predictions_ticker_predicted_at", "ticker", "predicted_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    ticker: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("stocks.ticker", ondelete="CASCADE"),
        nullable=False,
    )
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cut_probability: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    composite_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    recommendation: Mapped[str | None] = mapped_column(String(32))

    stock: Mapped[Stock] = relationship(back_populates="predictions")
