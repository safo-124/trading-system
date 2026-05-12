"""
Dividend Strategy Pipeline
==========================
End-to-end system for picking dividend stocks:
  1. Data layer        — pull fundamentals & dividend history
  2. Safety model      — predict dividend cuts (classification)
  3. Screening layer   — rank stocks by quality+yield composite
  4. Backtest          — simulate strategy returns honestly

Requirements:
    pip install yfinance pandas numpy scikit-learn matplotlib

NOTE: yfinance gives us free data but NOT point-in-time fundamentals.
For real money, replace the data layer with Sharadar / Refinitiv / etc.
"""

import numpy as np
import pandas as pd
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")


# ---------------------------------------------------------------
# STAGE 1: DATA LAYER
# ---------------------------------------------------------------

def fetch_stock_data(ticker: str) -> dict | None:
    """Pull everything we need for one stock. Returns None on failure."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        dividends = t.dividends  # full history
        price_hist = t.history(period="10y")["Close"]

        if dividends.empty or price_hist.empty:
            return None

        return {
            "ticker": ticker,
            "info": info,
            "dividends": dividends,
            "prices": price_hist,
        }
    except Exception as e:
        print(f"  [skip {ticker}: {e}]")
        return None


def build_features(data: dict) -> dict | None:
    """Compute the features the model will see."""
    info = data["info"]
    divs = data["dividends"]
    prices = data["prices"]

    if divs.empty:
        return None

    # Annual dividends (sum per calendar year)
    divs_naive = divs.copy()
    divs_naive.index = divs_naive.index.tz_localize(None)
    annual_div = divs_naive.groupby(divs_naive.index.year).sum()
    if len(annual_div) < 5:
        return None

    # Drop the current/most-recent year if it's a partial year.
    # Heuristic: if last year is less than 60% of the prior 3-year median,
    # treat it as partial (not yet fully paid out) and exclude.
    annual_div_complete = annual_div.copy()
    if len(annual_div_complete) >= 4:
        prior_median = annual_div_complete.iloc[-4:-1].median()
        if prior_median > 0 and annual_div_complete.iloc[-1] < 0.6 * prior_median:
            annual_div_complete = annual_div_complete.iloc[:-1]

    if len(annual_div_complete) < 5:
        return None

    # 5-year dividend growth (CAGR) using COMPLETE years only
    recent = annual_div_complete.iloc[-1]
    five_ago = (
        annual_div_complete.iloc[-6]
        if len(annual_div_complete) >= 6
        else annual_div_complete.iloc[0]
    )
    n_years = min(5, len(annual_div_complete) - 1)
    if five_ago <= 0 or n_years == 0:
        div_cagr_5y = 0.0
    else:
        div_cagr_5y = (recent / five_ago) ** (1 / n_years) - 1

    # Years of consecutive increases (using COMPLETE years only)
    consec_increases = 0
    for i in range(len(annual_div_complete) - 1, 0, -1):
        if annual_div_complete.iloc[i] > annual_div_complete.iloc[i - 1]:
            consec_increases += 1
        else:
            break

    # Yield: prefer trailingAnnualDividendYield (returned as fraction).
    # Fall back to dividendYield (returned as percent, divide by 100).
    yld = info.get("trailingAnnualDividendYield")
    if yld is None or yld == 0:
        raw = info.get("dividendYield", 0) or 0
        # If raw > 1, it's almost certainly a percentage (e.g. 2.7 for 2.7%).
        yld = raw / 100 if raw > 1 else raw

    features = {
        "ticker": data["ticker"],
        "yield": yld,
        "payout_ratio": info.get("payoutRatio", 0) or 0,
        "debt_to_equity": (info.get("debtToEquity", 0) or 0) / 100,
        "fcf": info.get("freeCashflow", 0) or 0,
        "market_cap": info.get("marketCap", 0) or 0,
        "earnings_growth": info.get("earningsGrowth", 0) or 0,
        "revenue_growth": info.get("revenueGrowth", 0) or 0,
        "profit_margin": info.get("profitMargins", 0) or 0,
        "current_ratio": info.get("currentRatio", 0) or 0,
        "roe": info.get("returnOnEquity", 0) or 0,
        "div_cagr_5y": div_cagr_5y,
        "consec_increases": consec_increases,
        "annual_div_now": float(recent),
        "annual_div_history": annual_div_complete,
    }

    shares = info.get("sharesOutstanding", 0) or 0
    total_div_paid = features["annual_div_now"] * shares
    features["fcf_coverage"] = (
        features["fcf"] / total_div_paid if total_div_paid > 0 else 0
    )
    return features


# ---------------------------------------------------------------
# STAGE 2: SAFETY SCORING (rules-based, no ML)
# ---------------------------------------------------------------

def compute_safety_score(row: pd.Series) -> float:
    """
    Transparent 0.0-1.0 safety score. Higher = safer dividend.
    Replaces the ML model. Each component is documented.
    """
    score = 0.0
    
    # Payout ratio: 30-60% is healthy. Above 90% is risky. Below 0 is bad data.
    payout = row.get("payout_ratio", 0)
    if 0.0 < payout <= 0.60:
        score += 0.25
    elif 0.60 < payout <= 0.80:
        score += 0.15
    elif 0.80 < payout <= 1.00:
        score += 0.05
    # else: 0 points (payout > 100% or non-positive)
    
    # FCF coverage: can free cash flow cover the dividend?
    coverage = row.get("fcf_coverage", 0)
    if coverage >= 2.0:
        score += 0.25
    elif coverage >= 1.5:
        score += 0.18
    elif coverage >= 1.0:
        score += 0.10
    # else: 0 points
    
    # Dividend growth: consistent growth signals safety
    growth = row.get("div_cagr_5y", 0)
    if growth >= 0.08:
        score += 0.20
    elif growth >= 0.04:
        score += 0.15
    elif growth >= 0.00:
        score += 0.08
    # else: negative growth = 0 points
    
    # Consecutive increases: streak as evidence of commitment
    consec = row.get("consec_increases", 0)
    if consec >= 10:
        score += 0.15
    elif consec >= 5:
        score += 0.10
    elif consec >= 2:
        score += 0.05
    
    # Debt-to-equity: lower is safer (capped at extreme values)
    de = row.get("debt_to_equity", 0)
    if 0 < de <= 0.5:
        score += 0.15
    elif 0.5 < de <= 1.0:
        score += 0.10
    elif 1.0 < de <= 2.0:
        score += 0.05
    
    return min(score, 1.0)


# ---------------------------------------------------------------
# STAGE 3: SCREENING — rank surviving stocks
# ---------------------------------------------------------------

def composite_score(row: pd.Series) -> float:
    """
    Combine yield + quality, MULTIPLIED by safety so unsafe stocks 
    can't rank high regardless of yield.
    """
    y = min(row.get("yield", 0), 0.08)
    growth = max(row.get("div_cagr_5y", 0), 0)
    payout = row.get("payout_ratio", 0)
    payout_score = 1 - abs(payout - 0.5) if 0 < payout < 1 else 0
    
    coverage_raw = row.get("fcf_coverage", 0)
    # Banks don't report FCF the same way. If coverage is 0 or negative
    # AND it's a financial-ish stock (no FCF reported), give partial credit.
    # Heuristic: if fcf is 0 in raw features, treat coverage as neutral (0.5).
    if coverage_raw <= 0:
        coverage = 0.5
    else:
        coverage = min(coverage_raw, 3) / 3
    
    consec = min(row.get("consec_increases", 0), 25) / 25
    
    # Quality component (additive)
    quality = (
        0.30 * y * 12
        + 0.25 * growth * 5
        + 0.15 * payout_score
        + 0.20 * coverage
        + 0.10 * consec
    )
    
    # Multiply by safety score so unsafe stocks get heavily penalized.
    # Apply a floor of 0.3 on safety so we don't completely zero out 
    # borderline-safe stocks.
    safety = max(row.get("safety_score", 0.5), 0.3)
    
    return quality * safety


def screen_stocks(features_df: pd.DataFrame, top_n=10, verbose=True) -> pd.DataFrame:
    """
    Rules-based screening with diagnostic output.
    No ML model needed.
    """
    df = features_df.copy()
    n_start = len(df)
    
    # Compute safety score for everyone (for visibility, even rejected ones)
    df["safety_score"] = df.apply(compute_safety_score, axis=1)
    df["composite_score"] = df.apply(composite_score, axis=1)
    
    if verbose:
        print(f"    Starting universe: {n_start} stocks")
    
    # Filter 1: yield must be reasonable (not zero, not a yield trap)
    before = len(df)
    df = df[(df["yield"] > 0.005) & (df["yield"] < 0.10)]
    if verbose:
        print(f"    After yield filter (0.5%-10%):     {len(df)} stocks ({before - len(df)} dropped)")
    
    # Filter 2: payout ratio must be sustainable
    before = len(df)
    df = df[(df["payout_ratio"] > 0) & (df["payout_ratio"] < 0.90)]
    if verbose:
        print(f"    After payout filter (<90%):        {len(df)} stocks ({before - len(df)} dropped)")
    
    # Filter 3: minimum market cap (avoid micro-caps)
    before = len(df)
    df = df[df["market_cap"] > 1e9]
    if verbose:
        print(f"    After market cap filter (>$1B):    {len(df)} stocks ({before - len(df)} dropped)")
    
    # Filter 4: minimum safety score
    before = len(df)
    df = df[df["safety_score"] >= 0.35]
    if verbose:
        print(f"    After safety score filter (>=0.35): {len(df)} stocks ({before - len(df)} dropped)")
    
    if df.empty:
        if verbose:
            print("    WARNING: No stocks passed all filters. Showing top by safety score anyway.")
        # Fallback: show top safety scores from the original universe so user 
        # can see what's happening
        return features_df.assign(
            safety_score=features_df.apply(compute_safety_score, axis=1),
            composite_score=features_df.apply(composite_score, axis=1),
        ).sort_values("safety_score", ascending=False).head(top_n)
    
    return df.sort_values("composite_score", ascending=False).head(top_n)


# ---------------------------------------------------------------
# STAGE 4: BACKTEST (simplified)
# ---------------------------------------------------------------

def simple_backtest(picks: pd.DataFrame, lookback_years=3) -> pd.DataFrame:
    """NOT a true point-in-time backtest. Logs errors instead of silently skipping."""
    if picks is None or picks.empty:
        print(f"    (no picks to backtest)")
        return pd.DataFrame()
    
    results = []
    end = pd.Timestamp.today()
    start = end - pd.DateOffset(years=lookback_years)

    print(f"    Backtesting {len(picks)} picks from {start.date()} to {end.date()}...")
    for ticker in picks["ticker"]:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(start=start, end=end, auto_adjust=True)["Close"]
            if hist.empty:
                print(f"      [skip {ticker}: no price history]")
                continue
            
            divs = t.dividends
            if not divs.empty:
                divs_idx = divs.index.tz_localize(None) if divs.index.tz is not None else divs.index
                divs = pd.Series(divs.values, index=divs_idx)
                start_naive = pd.Timestamp(start).tz_localize(None)
                end_naive = pd.Timestamp(end).tz_localize(None)
                divs = divs[(divs.index >= start_naive) & (divs.index <= end_naive)]

            price_return = hist.iloc[-1] / hist.iloc[0] - 1
            div_return = (divs.sum() / hist.iloc[0]) if not divs.empty else 0.0
            total_return = price_return + div_return

            results.append({
                "ticker": ticker,
                "price_return": price_return,
                "div_return": div_return,
                "total_return": total_return,
            })
        except Exception as e:
            print(f"      [skip {ticker}: {type(e).__name__}: {e}]")
            continue

    return pd.DataFrame(results)


# ---------------------------------------------------------------
# DRIVER
# ---------------------------------------------------------------

UNIVERSE = [
    "JNJ", "PG", "KO", "PEP", "MMM", "CL", "WMT", "MCD", "CVX", "XOM",
    "ABBV", "ABT", "MDT", "VZ", "T", "IBM", "HD", "LOW", "TGT", "CSCO",
    "MO", "BTI", "PFE", "WBA", "INTC", "F", "KMI", "EPD", "MPW", "O",
    "JPM", "BAC", "WFC", "C", "USB", "PNC", "BLK", "MS", "GS",
    "MSFT", "AAPL", "TXN", "AVGO", "QCOM",
]


def run_pipeline():
    print("=" * 60)
    print("DIVIDEND STRATEGY PIPELINE (rules-based)")
    print("=" * 60)

    print(f"\n[1] Fetching data for {len(UNIVERSE)} stocks...")
    features_list = []
    for tkr in UNIVERSE:
        data = fetch_stock_data(tkr)
        if not data:
            continue
        feats = build_features(data)
        if not feats:
            continue
        features_list.append(feats)

    print(f"    Got clean data for {len(features_list)} stocks")

    print(f"\n[2] Computing safety scores and screening...")
    df = pd.DataFrame([
        {k: v for k, v in f.items() if k != "annual_div_history"}
        for f in features_list
    ])

    picks = screen_stocks(df, top_n=10, verbose=True)

    print(f"\n[3] Top 10 picks:")
    if picks.empty:
        print("    (no picks produced)")
    else:
        display_cols = ["ticker", "yield", "div_cagr_5y", "payout_ratio",
                        "consec_increases", "fcf_coverage", "safety_score",
                        "composite_score"]
        # Only include columns that exist (defensive)
        display_cols = [c for c in display_cols if c in picks.columns]
        print(picks[display_cols].to_string(index=False, formatters={
            "yield": "{:.2%}".format,
            "div_cagr_5y": "{:.2%}".format,
            "payout_ratio": "{:.2%}".format,
            "fcf_coverage": "{:.2f}x".format,
            "safety_score": "{:.2f}".format,
            "composite_score": "{:.3f}".format,
        }))

    print(f"\n[4] 3-year lookback returns (NOT a true backtest):")
    bt = simple_backtest(picks, lookback_years=3)
    if not bt.empty:
        print(bt.to_string(index=False, formatters={
            "price_return": "{:.1%}".format,
            "div_return": "{:.1%}".format,
            "total_return": "{:.1%}".format,
        }))
        print(f"\n    Equal-weighted portfolio total return: "
              f"{bt['total_return'].mean():.1%}")

        try:
            spy = yf.Ticker("SPY").history(
                start=pd.Timestamp.today() - pd.DateOffset(years=3)
            )["Close"]
            spy_return = spy.iloc[-1] / spy.iloc[0] - 1
            print(f"    SPY benchmark over same period:      {spy_return:.1%}")
        except Exception as e:
            print(f"    (SPY benchmark fetch failed: {e})")
    else:
        print("    (no backtest results)")

    print("\n" + "=" * 60)
    print("WARNINGS:")
    print(" - Backtest uses current fundamentals on past prices (look-ahead bias)")
    print(" - Universe is hand-picked; real systems use index membership")
    print(" - yfinance data is best-effort; production needs paid feeds")
    print(" - Past returns are NOT a guarantee of future results")
    print("=" * 60)

    # Save picks for later inspection / FastAPI integration
    if not picks.empty:
        out_path = "latest_picks.csv"
        picks_to_save = picks.drop(columns=["annual_div_history"], errors="ignore")
        picks_to_save.to_csv(out_path, index=False)
        print(f"\n    Picks saved to: {out_path}")

    return picks, bt


if __name__ == "__main__":
    run_pipeline()
