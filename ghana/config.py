from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data_ghana"
DATA_DIR.mkdir(exist_ok=True)

# afx.kwayisi.org hosts a semi-structured GSE listings page
GSE_LISTINGS_URL = "https://afx.kwayisi.org/gse/"

# Manual fallback CSV path -- used if scraping fails
MANUAL_CSV_PATH = DATA_DIR / "gse_manual.csv"
