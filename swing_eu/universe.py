"""
European universe management — Euro STOXX 600.

Sources in priority order:
  1. Wikipedia STOXX 600 page (with browser User-Agent)
  2. Hardcoded fallback of ~50 largest European stocks (last resort)

yfinance ticker format for European exchanges requires an exchange suffix:
  ASML.AS    Amsterdam
  SAP.DE     Xetra
  NESN.SW    Swiss
  AZN.L      London
  MC.PA      Paris
  ENEL.MI    Milan
  NOVO-B.CO  Copenhagen
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


COUNTRY_TO_SUFFIX = {
    "Austria": ".VI",
    "Belgium": ".BR",
    "Czech Republic": ".PR",
    "Denmark": ".CO",
    "Finland": ".HE",
    "France": ".PA",
    "Germany": ".DE",
    "Ireland": ".IR",
    "Italy": ".MI",
    "Luxembourg": ".LU",
    "Netherlands": ".AS",
    "Norway": ".OL",
    "Poland": ".WA",
    "Portugal": ".LS",
    "Spain": ".MC",
    "Sweden": ".ST",
    "Switzerland": ".SW",
    "United Kingdom": ".L",
}


EUROPEAN_FALLBACK = [
    "ASML.AS", "SAP.DE", "SIE.DE", "AIR.PA", "MC.PA", "SHEL.L", "AZN.L",
    "ULVR.L", "BP.L", "HSBA.L", "RIO.L", "GLEN.L",
    "NOVO-B.CO", "ROG.SW", "NESN.SW", "NOVN.SW", "SAN.PA", "OR.PA",
    "RMS.PA", "CDI.PA", "EL.PA", "DG.PA",
    "BNP.PA", "ACA.PA", "ALV.DE", "DBK.DE", "ING.AS", "ISP.MI", "UCG.MI",
    "TTE.PA", "ENI.MI", "ENEL.MI", "IBE.MC", "BAS.DE", "BAYN.DE",
    "MBG.DE", "BMW.DE", "VOW3.DE", "STLAM.MI", "RNO.PA",
    "TEF.MC", "DTE.DE", "VOD.L",
    "INGA.AS", "PHIA.AS", "AD.AS", "ASM.AS", "REL.L",
    "BARC.L", "LLOY.L", "GSK.L", "DGE.L",
]


def _normalize_for_yfinance(ticker: str, country: str | None) -> str | None:
    if not ticker or not isinstance(ticker, str):
        return None
    t = ticker.strip().replace("\u00a0", "")
    if "." in t and len(t.split(".")[-1]) <= 3:
        return t
    if country is None:
        return None
    suffix = COUNTRY_TO_SUFFIX.get(str(country).strip())
    if not suffix:
        return None
    return t + suffix


def _fetch_from_wikipedia() -> list[str]:
    url = "https://en.wikipedia.org/wiki/STOXX_Europe_600"
    r = requests.get(url, headers=BROWSER_HEADERS, timeout=30)
    r.raise_for_status()
    tables = pd.read_html(io.StringIO(r.text))
    
    chosen = None
    for tbl in tables:
        cols = [str(c).strip() for c in tbl.columns]
        has_ticker = any("ticker" in c.lower() or "symbol" in c.lower() for c in cols)
        has_country = any("country" in c.lower() for c in cols)
        if has_ticker and has_country and len(tbl) > 100:
            chosen = tbl
            break
    
    if chosen is None:
        raise RuntimeError("STOXX 600 constituents table not found on Wikipedia.")
    
    ticker_col = next(c for c in chosen.columns
                      if "ticker" in str(c).lower() or "symbol" in str(c).lower())
    country_col = next(c for c in chosen.columns if "country" in str(c).lower())
    
    out = []
    for _, row in chosen.iterrows():
        normalized = _normalize_for_yfinance(row[ticker_col], row.get(country_col))
        if normalized:
            out.append(normalized)
    return sorted(set(out))


def fetch_european_universe() -> tuple[list[str], str]:
    try:
        tickers = _fetch_from_wikipedia()
        if len(tickers) >= 300:
            return tickers, "wikipedia_stoxx600"
        print(f"[warn] wikipedia returned only {len(tickers)} tickers; using fallback.",
              file=sys.stderr)
    except Exception as e:
        print(f"[warn] wikipedia STOXX 600 fetch failed: {type(e).__name__}: {e}",
              file=sys.stderr)
    return EUROPEAN_FALLBACK, "european_fallback"


def get_universe(n: Optional[int] = None) -> list[str]:
    tickers, source = fetch_european_universe()
    print(f"[info] EU universe source: {source} ({len(tickers)} tickers)",
          file=sys.stderr)
    if n is None:
        return tickers
    return tickers[:n]
