"""
Download daily OHLCV bars from yfinance for the universe and save to parquet.
"""

from __future__ import annotations
import argparse
import sys
import time
import pandas as pd
from tqdm import tqdm

from swing.config import BARS_DIR, START_DATE, END_DATE, UNIVERSE_SIZE
from swing.universe import get_universe
from swing.yf_client import fetch_daily_bars


REQUEST_DELAY_SEC = 0.1  # yfinance is fine with light pacing


def ingest_one(ticker: str, start: str, end: str | None) -> int:
    """Fetch and save one ticker. Returns row count or 0 on failure."""
    try:
        df = fetch_daily_bars(ticker, start=start, end=end)
        if df.empty:
            return 0
        out_path = BARS_DIR / f"{ticker.replace('.', '_').replace('-', '_')}.parquet"
        df.to_parquet(out_path, index=False)
        return len(df)
    except Exception as e:
        print(f"  [skip {ticker}: {type(e).__name__}: {e}]", file=sys.stderr)
        return 0


def ingest_universe(tickers: list[str], start: str, end: str | None) -> dict:
    succeeded = []
    failed = []
    total_rows = 0
    
    for ticker in tqdm(tickers, desc="Ingesting"):
        n = ingest_one(ticker, start, end)
        if n > 0:
            succeeded.append((ticker, n))
            total_rows += n
        else:
            failed.append(ticker)
        time.sleep(REQUEST_DELAY_SEC)
    
    return {
        "succeeded": succeeded,
        "failed": failed,
        "total_rows": total_rows,
        "n_succeeded": len(succeeded),
        "n_failed": len(failed),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=UNIVERSE_SIZE)
    parser.add_argument("--start", default=START_DATE)
    parser.add_argument("--end", default=END_DATE)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--test", action="store_true",
                        help="Quick test: fetch only AAPL")
    args = parser.parse_args()
    
    if args.test:
        tickers = ["AAPL"]
    elif args.full:
        tickers = get_universe(None)
    else:
        tickers = get_universe(args.size)
    
    print(f"Ingesting {len(tickers)} tickers from yfinance")
    print(f"Date range: {args.start} to {args.end or 'today'}")
    print(f"Output: {BARS_DIR}")
    
    result = ingest_universe(tickers, args.start, args.end)
    
    print()
    print(f"  Succeeded: {result['n_succeeded']}/{len(tickers)}")
    print(f"  Failed:    {result['n_failed']}")
    if result["failed"]:
        print(f"  Failed tickers: {result['failed']}")
    print(f"  Total rows: {result['total_rows']:,}")
    
    return 0 if result["n_succeeded"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
