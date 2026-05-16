"""
Diagnostic: dump the raw structure of the afx.kwayisi.org GSE table
so we can see which column is actually the price.
"""
import io
import requests
import pandas as pd
from ghana.config import GSE_LISTINGS_URL

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

resp = requests.get(GSE_LISTINGS_URL, headers=HEADERS, timeout=30)
resp.raise_for_status()

tables = pd.read_html(io.StringIO(resp.text))
print(f"Found {len(tables)} HTML tables on the page.\n")

for i, tbl in enumerate(tables):
    print(f"=== TABLE {i} - shape {tbl.shape} ===")
    print(f"Columns: {list(tbl.columns)}")
    print("First 5 rows:")
    print(tbl.head(5).to_string())
    print()

# Also dump a snippet of raw HTML around the first <table> so we can see
# column headers that pandas might have mangled
html = resp.text
table_start = html.lower().find("<table")
if table_start >= 0:
    snippet = html[table_start:table_start + 2000]
    print("=== RAW HTML SNIPPET (first table, 2000 chars) ===")
    print(snippet)
