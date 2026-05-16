"""
GSE data scraper -- risk-gate version.

Attempts to scrape current GSE listings (ticker, name, price) from
afx.kwayisi.org/gse. This is a free aggregator of Ghana Stock Exchange data.

IMPORTANT: This is a polite, low-volume scraper for personal research.
It fetches ONE page, ONCE. It does not hammer the server. If afx.kwayisi.org
changes its layout or blocks requests, the scrape fails gracefully and the
caller should fall back to manual CSV entry.
"""

from __future__ import annotations
import io
import sys
from dataclasses import dataclass
from typing import Optional

import requests
import pandas as pd

from ghana.config import GSE_LISTINGS_URL, DATA_DIR


BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


@dataclass
class GSEListing:
    ticker: str
    name: str
    price: float | None   # in Ghana cedis (GHS); None = didn't trade
    volume: float | None  # shares traded that session; None = didn't trade


def scrape_gse_listings() -> list[GSEListing]:
    """
    Fetch and parse the GSE listings table from afx.kwayisi.org.

    The page has 4 tables; the listings table is identified by having the
    columns ['Ticker', 'Name', 'Volume', 'Price', 'Change']. We read the
    NAMED 'Price' column (not positional) to avoid grabbing Volume.

    Returns a list of GSEListing. Raises on network/parse failure.
    """
    resp = requests.get(GSE_LISTINGS_URL, headers=BROWSER_HEADERS, timeout=30)
    resp.raise_for_status()

    tables = pd.read_html(io.StringIO(resp.text))
    if not tables:
        raise RuntimeError("No HTML tables found on the GSE listings page.")

    # Find the listings table: it has Ticker, Name, and Price columns
    chosen = None
    for tbl in tables:
        cols = [str(c).strip().lower() for c in tbl.columns]
        if "ticker" in cols and "name" in cols and "price" in cols:
            chosen = tbl
            break

    if chosen is None:
        raise RuntimeError(
            f"Could not find listings table with Ticker/Name/Price columns. "
            f"Found {len(tables)} tables with columns: "
            f"{[list(t.columns) for t in tables]}"
        )

    # Normalize column names to lowercase for safe access
    chosen = chosen.copy()
    chosen.columns = [str(c).strip().lower() for c in chosen.columns]

    listings = []
    for _, row in chosen.iterrows():
        ticker = str(row["ticker"]).strip()
        if not ticker or ticker.lower() in ("nan", "ticker"):
            continue
        name = str(row["name"]).strip()
        # Price: parse defensively. NaN means the stock didn't trade.
        raw_price = row["price"]
        try:
            price = float(str(raw_price).replace(",", "").replace("GHS", "").strip())
            if price <= 0:
                price = None
        except (ValueError, AttributeError, TypeError):
            price = None
        raw_volume = row.get("volume")
        try:
            volume = float(str(raw_volume).replace(",", "").strip())
        except (ValueError, AttributeError, TypeError):
            volume = None
        listings.append(GSEListing(
            ticker=ticker, name=name, price=price, volume=volume
        ))

    return listings


def listings_to_dataframe(listings: list[GSEListing]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "ticker": l.ticker,
            "name": l.name,
            "price_ghs": l.price,
            "volume": l.volume,
        }
        for l in listings
    ])


def main() -> int:
    print(f"Attempting to scrape GSE listings from {GSE_LISTINGS_URL}")
    try:
        listings = scrape_gse_listings()
    except Exception as e:
        print(f"\nSCRAPE FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        print("\nFall back to manual CSV entry. See ghana/config.py MANUAL_CSV_PATH.")
        return 1

    df = listings_to_dataframe(listings)
    print(f"\nScraped {len(df)} GSE listings.")
    print()
    print(df.to_string(index=False))
    print()

    # Save raw scrape for inspection
    out_path = DATA_DIR / "gse_scraped_raw.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved raw scrape to: {out_path}")

    # Quick quality assessment
    n_with_price = df["price_ghs"].notna().sum()
    print()
    print(f"Quality check:")
    print(f"  Total rows: {len(df)}")
    print(f"  Rows with a parseable price: {n_with_price}")
    print(f"  Rows missing price: {len(df) - n_with_price}")

    if len(df) < 15:
        print("\n  WARNING: fewer than 15 listings -- scrape may be incomplete.")
        return 1
    if n_with_price < 10:
        print("\n  WARNING: fewer than 10 rows have prices -- parse may be misaligned.")
        return 1

    print("\n  Scrape looks usable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
