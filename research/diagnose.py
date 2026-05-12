import yfinance as yf
import pandas as pd

print("=" * 60)
print("Diagnostic for KO (Coca-Cola)")
print("=" * 60)

t = yf.Ticker("KO")

print("\n--- info['dividendYield'] ---")
print(f"raw value: {t.info.get('dividendYield')}")
print(f"type: {type(t.info.get('dividendYield'))}")

print("\n--- info['payoutRatio'] ---")
print(f"raw value: {t.info.get('payoutRatio')}")

print("\n--- info['trailingAnnualDividendYield'] ---")
print(f"raw value: {t.info.get('trailingAnnualDividendYield')}")

print("\n--- t.dividends (last 20 rows) ---")
divs = t.dividends
print(f"type: {type(divs)}")
print(f"length: {len(divs)}")
print(f"index type: {type(divs.index)}")
print(f"first date: {divs.index[0] if len(divs) > 0 else 'EMPTY'}")
print(f"last date:  {divs.index[-1] if len(divs) > 0 else 'EMPTY'}")
print("\nLast 20 dividend payments:")
print(divs.tail(20))

print("\n--- Annual sums (last 8 years) ---")
divs_naive = divs.copy()
divs_naive.index = divs_naive.index.tz_localize(None)
annual = divs_naive.groupby(divs_naive.index.year).sum()
print(annual.tail(8))

print("\n--- Year-over-year change ---")
print(annual.tail(8).pct_change())
