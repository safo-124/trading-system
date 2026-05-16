"""
Risk gate: does afx.kwayisi.org expose per-stock price history?

afx.kwayisi.org has per-stock pages at URLs like:
  https://afx.kwayisi.org/gse/MTNGH
  https://afx.kwayisi.org/gse/GCB

This script fetches a few of those pages and dumps their table structure
so we can see whether historical prices are available, and how far back.

We test 5 stocks across the liquidity spectrum:
  MTNGH  - most liquid
  GCB    - liquid bank
  TOTAL  - liquid industrial
  EGH    - mid liquidity
  FML    - Fan Milk, consumer
"""

import io
import sys
import time
import requests
import pandas as pd

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

BASE = "https://afx.kwayisi.org/gse/"
TEST_TICKERS = ["MTNGH", "GCB", "TOTAL", "EGH", "FML"]


def inspect_stock_page(ticker: str) -> None:
    url = f"{BASE}{ticker}"
    print(f"\n{'=' * 65}")
    print(f"TICKER: {ticker}  ->  {url}")
    print("=" * 65)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        print(f"HTTP status: {resp.status_code}")
        resp.raise_for_status()
    except Exception as e:
        print(f"FETCH FAILED: {type(e).__name__}: {e}")
        return

    # Try to find tables
    try:
        tables = pd.read_html(io.StringIO(resp.text))
    except Exception as e:
        print(f"No tables parseable: {type(e).__name__}: {e}")
        tables = []

    print(f"Tables found: {len(tables)}")
    for i, tbl in enumerate(tables):
        print(f"\n  --- Table {i}: shape {tbl.shape} ---")
        print(f"  Columns: {list(tbl.columns)}")
        # Show first and last 3 rows so we can see date range
        print("  First 3 rows:")
        for line in tbl.head(3).to_string().split("\n"):
            print(f"    {line}")
        if len(tbl) > 6:
            print("  Last 3 rows:")
            for line in tbl.tail(3).to_string().split("\n"):
                print(f"    {line}")

    # Also check raw HTML for any date-like patterns or chart data
    html = resp.text
    print(f"\n  Raw HTML length: {len(html):,} chars")
    # Look for signs of historical data: dates, "history", chart JSON
    for keyword in ["history", "historical", "chart", "2025", "2024", "2023"]:
        count = html.lower().count(keyword.lower())
        if count > 0:
            print(f"  '{keyword}' appears {count} times in HTML")


def main() -> int:
    print("RISK GATE: Testing afx.kwayisi.org per-stock history availability")
    for ticker in TEST_TICKERS:
        inspect_stock_page(ticker)
        time.sleep(1.0)  # be polite - 1 second between requests

    print(f"\n{'=' * 65}")
    print("ASSESSMENT GUIDANCE:")
    print("  - If a table has 50+ rows with dates and prices -> usable history")
    print("  - If only 1-5 rows -> just current quote, no history")
    print("  - If 'chart' keyword appears a lot -> history may be in JS, harder")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
