"""
Universe management.

Strategy: try multiple sources in order, fall back gracefully.
  1. Wikipedia (with browser-like User-Agent)
  2. GitHub-hosted CSV (datasets/s-and-p-500-companies)
  3. Hardcoded SP100 list (last resort)
"""

from __future__ import annotations
import io
import sys
from typing import Optional

import pandas as pd
import requests


BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


# Last-resort fallback (S&P 100)
SP100_FALLBACK = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "BRK.B", "TSLA",
    "AVGO", "JPM", "LLY", "V", "WMT", "XOM", "MA", "UNH", "PG", "JNJ",
    "HD", "COST", "ABBV", "BAC", "ORCL", "KO", "NFLX", "CVX", "MRK", "ADBE",
    "PEP", "CRM", "TMO", "ACN", "LIN", "MCD", "WFC", "ABT", "CSCO", "DHR",
    "AMD", "TXN", "PM", "DIS", "VZ", "INTU", "IBM", "QCOM", "GE", "CAT",
    "AXP", "ISRG", "GS", "NOW", "T", "RTX", "BKNG", "SPGI", "AMGN", "MS",
    "PFE", "UBER", "BLK", "NEE", "PLD", "ELV", "HON", "TJX", "SYK", "CMCSA",
    "C", "LOW", "MDT", "BMY", "ADP", "VRTX", "GILD", "REGN", "MMC", "DE",
    "AMT", "BSX", "ETN", "CB", "SCHW", "BX", "MU", "LMT", "SBUX", "ADI",
    "PGR", "ZTS", "TMUS", "CI", "DUK", "SO", "SLB", "MO", "USB", "BDX",
]


def _normalize_ticker(t: str) -> str:
    """Normalize ticker format: strip whitespace, replace hyphens with dots."""
    t = str(t).strip().replace("\u00a0", "")
    if "." not in t and "-" in t:
        t = t.replace("-", ".")
    return t


def _fetch_from_wikipedia() -> list[str]:
    """Fetch S&P 500 from Wikipedia using browser-like headers."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    r = requests.get(url, headers=BROWSER_HEADERS, timeout=30)
    r.raise_for_status()
    tables = pd.read_html(io.StringIO(r.text))
    df = tables[0]
    if "Symbol" not in df.columns:
        raise RuntimeError(f"Unexpected Wikipedia table format: {list(df.columns)}")
    tickers = [_normalize_ticker(t) for t in df["Symbol"].astype(str)]
    return sorted(set(tickers))


def _fetch_from_github() -> list[str]:
    """
    Fetch S&P 500 from a public GitHub-hosted CSV.
    This is the datasets/s-and-p-500-companies repo (well-maintained).
    """
    url = (
        "https://raw.githubusercontent.com/datasets/"
        "s-and-p-500-companies/main/data/constituents.csv"
    )
    r = requests.get(url, headers=BROWSER_HEADERS, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    # Column is usually 'Symbol'
    col = "Symbol" if "Symbol" in df.columns else df.columns[0]
    tickers = [_normalize_ticker(t) for t in df[col].astype(str)]
    return sorted(set(tickers))


def fetch_sp500() -> tuple[list[str], str]:
    """
    Try multiple sources in order. Returns (tickers, source_used).
    """
    sources = [
        ("wikipedia", _fetch_from_wikipedia),
        ("github_datasets", _fetch_from_github),
    ]
    for name, fn in sources:
        try:
            tickers = fn()
            if len(tickers) >= 400:  # sanity check
                return tickers, name
            else:
                print(f"[warn] {name} returned only {len(tickers)} tickers; trying next.",
                      file=sys.stderr)
        except Exception as e:
            print(f"[warn] {name} fetch failed: {type(e).__name__}: {e}",
                  file=sys.stderr)
    # All sources failed
    print("[warn] All S&P 500 sources failed; using SP100 fallback.", file=sys.stderr)
    return SP100_FALLBACK, "sp100_fallback"


def get_universe(n: Optional[int] = None, source: str = "sp500") -> list[str]:
    """
    Return the development universe.
    
    source="sp500": Try Wikipedia, then GitHub, then SP100 fallback.
    source="sp100": Force the hardcoded SP100 list.
    """
    if source == "sp100":
        tickers = SP100_FALLBACK
    elif source == "sp500":
        tickers, used = fetch_sp500()
        print(f"[info] Universe source: {used} ({len(tickers)} tickers)",
              file=sys.stderr)
    else:
        raise ValueError(f"Unknown source: {source}")
    
    if n is None:
        return tickers
    return tickers[:n]
