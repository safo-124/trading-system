from __future__ import annotations

import argparse
import asyncio
import logging

from app.db.session import dispose_engine
from app.services.ingestion import IngestionService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest market data from yfinance.")
    parser.add_argument(
        "--tickers",
        required=True,
        help="Comma-separated ticker list, for example: JNJ,KO,PG,MMM,WMT",
    )
    return parser.parse_args()


async def run(tickers: list[str]) -> int:
    service = IngestionService()
    try:
        result = await service.ingest_tickers(tickers)
    finally:
        await dispose_engine()

    print(f"Ingested {len(result.processed)} ticker(s): {', '.join(result.processed) or 'none'}")
    if result.skipped:
        print("Skipped ticker(s):")
        for ticker, reason in result.skipped.items():
            print(f"  {ticker}: {reason}")

    return 0


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s [%(name)s] %(message)s",
    )
    args = parse_args()
    tickers = [ticker.strip() for ticker in args.tickers.split(",")]
    raise SystemExit(asyncio.run(run(tickers)))


if __name__ == "__main__":
    main()
