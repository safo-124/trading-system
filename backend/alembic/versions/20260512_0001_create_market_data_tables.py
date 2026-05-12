"""create market data tables

Revision ID: 20260512_0001
Revises:
Create Date: 2026-05-12 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260512_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    op.create_table(
        "stocks",
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("sector", sa.String(length=255), nullable=True),
        sa.Column("market_cap", sa.BigInteger(), nullable=True),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("ticker"),
    )

    op.create_table(
        "dividend_history",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("ex_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 6), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.ForeignKeyConstraint(["ticker"], ["stocks.ticker"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "ex_date", name="uq_dividend_history_ticker_ex_date"),
    )
    op.create_index("ix_dividend_history_ticker", "dividend_history", ["ticker"])

    op.create_table(
        "fundamentals",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("yield", sa.Numeric(10, 6), nullable=True),
        sa.Column("payout_ratio", sa.Numeric(10, 6), nullable=True),
        sa.Column("fcf", sa.Numeric(20, 2), nullable=True),
        sa.Column("debt_to_equity", sa.Numeric(12, 6), nullable=True),
        sa.Column("roe", sa.Numeric(10, 6), nullable=True),
        sa.Column("profit_margin", sa.Numeric(10, 6), nullable=True),
        sa.ForeignKeyConstraint(["ticker"], ["stocks.ticker"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", "as_of_date"),
        sa.UniqueConstraint("ticker", "as_of_date", name="uq_fundamentals_ticker_as_of_date"),
    )
    op.create_index("ix_fundamentals_ticker", "fundamentals", ["ticker"])
    op.execute("SELECT create_hypertable('fundamentals', 'as_of_date', if_not_exists => TRUE)")

    op.create_table(
        "predictions",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("predicted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cut_probability", sa.Numeric(10, 6), nullable=True),
        sa.Column("composite_score", sa.Numeric(10, 6), nullable=True),
        sa.Column("recommendation", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["ticker"], ["stocks.ticker"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_predictions_ticker_predicted_at",
        "predictions",
        ["ticker", "predicted_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_predictions_ticker_predicted_at", table_name="predictions")
    op.drop_table("predictions")
    op.drop_index("ix_fundamentals_ticker", table_name="fundamentals")
    op.drop_table("fundamentals")
    op.drop_index("ix_dividend_history_ticker", table_name="dividend_history")
    op.drop_table("dividend_history")
    op.drop_table("stocks")
