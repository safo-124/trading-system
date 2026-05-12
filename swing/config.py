import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Alpaca credentials kept around for later (paper trading uses them).
# Not used for data ingestion anymore — we use Stooq for that.
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

BARS_DIR = DATA_DIR / "bars_daily"
BARS_DIR.mkdir(exist_ok=True)

# Stooq has data back to 2000+ for most S&P names
START_DATE = "2010-01-01"
END_DATE = None

UNIVERSE_SIZE = 500
