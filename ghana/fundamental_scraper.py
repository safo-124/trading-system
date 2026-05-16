"""
Full GSE fundamental scraper.

For each stock on the exchange, fetches the per-stock page at
afx.kwayisi.org/gse/<TICKER> and extracts:
  - Fundamentals (EPS, P/E, dividend per share, and any other rows in
    the "Growth & Valuation" table)
  - Return windows (1WK, 4WK, 3MO, 6MO, 1YR, YTD)
  - Most recent close + volume from the 10-day history table

Combines with the snapshot scrape (ticker/name/price/volume) into a single
gse_fundamentals.csv.

Polite: 1 second between requests, single pass, ~40 requests total.
"""

from __future__ import annotations
import io
import sys
import time
import re
from pathlib import Path

import requests
import pandas as pd

from ghana.config import GSE_LISTINGS_URL, DATA_DIR
from ghana.scraper import scrape_gse_listings, listings_to_dataframe


BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

BASE = "https://afx.kwayisi.org/gse/"
REQUEST_DELAY_SEC = 2.5  # afx.kwayisi.org rate-limits aggressively below ~2s


def _parse_pct(val) -> float | None:
    """Parse a percentage string like '+12.3%' or '-3.99%' into a float (0.123)."""
    if val is None:
        return None
    s = str(val).strip().replace("%", "").replace("+", "")
    if s in ("", "nan", "NaN", "\u2014", "-"):
        return None
    try:
        return float(s) / 100.0
    except ValueError:
        return None


def _parse_num(val) -> float | None:
    """Parse a numeric string, handling commas and currency markers."""
    if val is None:
        return None
    s = str(val).strip().replace(",", "").replace("GHS", "").strip()
    if s in ("", "nan", "NaN", "\u2014", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def scrape_stock_detail(ticker: str) -> dict:
    """
    Fetch one stock's detail page and extract fundamentals + returns.
    Returns a dict of fields. Missing fields are None -- never raises for
    a single stock (returns dict with 'error' key instead).
    """
    url = f"{BASE}{ticker}"
    result: dict = {"ticker": ticker, "error": None}

    # Retry with exponential backoff, specifically for 429 rate-limiting
    resp = None
    max_attempts = 4
    for attempt in range(max_attempts):
        try:
            resp = requests.get(url, headers=BROWSER_HEADERS, timeout=30)
            if resp.status_code == 429:
                # Rate limited -- back off and retry
                backoff = 5 * (attempt + 1)  # 5s, 10s, 15s, 20s
                if attempt < max_attempts - 1:
                    print(f"    (429 on {ticker}, backing off {backoff}s...)")
                    time.sleep(backoff)
                    continue
                else:
                    result["error"] = "HTTP 429 after retries"
                    return result
            resp.raise_for_status()
            break  # success
        except requests.HTTPError as e:
            if resp is not None and resp.status_code == 429 and attempt < max_attempts - 1:
                continue  # already slept above
            result["error"] = f"{type(e).__name__}: {e}"
            return result
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {e}"
            return result

    if resp is None:
        result["error"] = "no response"
        return result

    try:
        tables = pd.read_html(io.StringIO(resp.text))
    except Exception as e:
        result["error"] = f"table parse failed: {e}"
        return result

    # --- Growth & Valuation table: find the table whose first column
    #     header contains "Growth & Valuation" ---
    for tbl in tables:
        col0 = str(tbl.columns[0]).lower()
        if "growth" in col0 and "valuation" in col0 and tbl.shape[1] >= 2:
            # It's a 2-col key/value table
            for _, row in tbl.iterrows():
                key = str(row.iloc[0]).strip().lower()
                val = row.iloc[1]
                if "earnings per share" in key:
                    result["eps"] = _parse_num(val)
                elif "price/earning" in key or "p/e" in key:
                    result["pe_ratio"] = _parse_num(val)
                elif "dividend per share" in key:
                    result["div_per_share"] = _parse_num(val)
                elif "dividend yield" in key:
                    result["div_yield"] = _parse_pct(val)
                elif "return on equity" in key or "roe" in key:
                    result["roe"] = _parse_pct(val)
                elif "book value" in key:
                    result["book_value"] = _parse_num(val)
                elif "market cap" in key:
                    result["market_cap_raw"] = str(val).strip()
            break

    # --- Return-window tables: 1WK/4WK/3MO and 6MO/1YR/YTD ---
    for tbl in tables:
        cols = [str(c).strip().upper() for c in tbl.columns]
        if cols == ["1WK", "4WK", "3MO"] and len(tbl) >= 1:
            r = tbl.iloc[0]
            result["ret_1wk"] = _parse_pct(r.iloc[0])
            result["ret_4wk"] = _parse_pct(r.iloc[1])
            result["ret_3mo"] = _parse_pct(r.iloc[2])
        elif cols == ["6MO", "1YR", "YTD"] and len(tbl) >= 1:
            r = tbl.iloc[0]
            result["ret_6mo"] = _parse_pct(r.iloc[0])
            result["ret_1yr"] = _parse_pct(r.iloc[1])
            result["ret_ytd"] = _parse_pct(r.iloc[2])

    # --- 10-day history table: Date/Volume/Close/Change/Change% ---
    #     We extract: most recent close, and a rough volatility proxy
    #     (std of the available daily Change% values).
    for tbl in tables:
        cols = [str(c).strip().lower() for c in tbl.columns]
        if "date" in cols and "close" in cols and "volume" in cols:
            tbl2 = tbl.copy()
            tbl2.columns = cols
            closes = pd.to_numeric(tbl2["close"], errors="coerce").dropna()
            if len(closes) > 0:
                result["recent_close"] = float(closes.iloc[0])
            # Volatility proxy from daily changes (only ~10 days, very rough)
            if "change%" in cols:
                chgs = tbl2["change%"].apply(_parse_pct).dropna()
                if len(chgs) >= 3:
                    result["vol_proxy_10d"] = float(chgs.std())
            # Average daily volume over the window
            vols = pd.to_numeric(tbl2["volume"], errors="coerce").dropna()
            if len(vols) > 0:
                result["avg_volume_10d"] = float(vols.mean())
            break

    return result


def main() -> int:
    print("GSE Full Fundamental Scraper")
    print("=" * 60)

    # First get the snapshot (ticker / name / price / volume)
    print("\nStep 1: scraping the listings snapshot...")
    try:
        listings = scrape_gse_listings()
    except Exception as e:
        print(f"FAILED to scrape listings: {e}", file=sys.stderr)
        return 1
    snapshot_df = listings_to_dataframe(listings)
    print(f"  Got {len(snapshot_df)} listings.")

    tickers = snapshot_df["ticker"].tolist()

    # Now walk each stock's detail page
    print(f"\nStep 2: scraping {len(tickers)} per-stock detail pages...")
    print(f"  (1 second between requests -- this takes ~{len(tickers)} seconds)")
    details = []
    for i, ticker in enumerate(tickers, 1):
        detail = scrape_stock_detail(ticker)
        details.append(detail)
        status = "OK" if detail.get("error") is None else f"ERROR: {detail['error']}"
        print(f"  [{i:2d}/{len(tickers)}] {ticker:10s} {status}")
        time.sleep(REQUEST_DELAY_SEC)

    detail_df = pd.DataFrame(details)

    # Merge snapshot + details on ticker
    merged = snapshot_df.merge(detail_df, on="ticker", how="left")

    # Save
    out_path = DATA_DIR / "gse_fundamentals.csv"
    merged.to_csv(out_path, index=False)
    print(f"\nSaved merged fundamentals to: {out_path}")

    # Quality report
    print("\n" + "=" * 60)
    print("QUALITY REPORT")
    print("=" * 60)
    print(f"Total stocks: {len(merged)}")
    n_errors = merged["error"].notna().sum() if "error" in merged.columns else 0
    print(f"Detail-page errors: {n_errors}")
    for col in ["eps", "pe_ratio", "div_per_share", "ret_1yr", "ret_ytd",
                "recent_close", "avg_volume_10d", "vol_proxy_10d"]:
        if col in merged.columns:
            n = merged[col].notna().sum()
            print(f"  {col:20s}: {n}/{len(merged)} populated")
        else:
            print(f"  {col:20s}: COLUMN MISSING")

    # Show the full merged table
    print("\n" + "=" * 60)
    print("FULL MERGED DATA")
    print("=" * 60)
    # Pick the most useful columns to display
    display_cols = ["ticker", "name", "price_ghs", "volume", "eps",
                    "pe_ratio", "div_per_share", "ret_1yr", "ret_ytd"]
    display_cols = [c for c in display_cols if c in merged.columns]
    print(merged[display_cols].to_string(index=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
