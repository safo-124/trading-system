import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data_africa"
DATA_DIR.mkdir(exist_ok=True)
BARS_DIR = DATA_DIR / "bars_daily"
BARS_DIR.mkdir(exist_ok=True)

# JSE history via yfinance generally goes back to ~2005-2010 for major names.
# Start in 2012 to match swing_eu config — clean comparison.
START_DATE = "2012-01-01"
END_DATE = None
UNIVERSE_SIZE = 80
