import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# European data lives in a separate directory from US
DATA_DIR = PROJECT_ROOT / "data_eu"
DATA_DIR.mkdir(exist_ok=True)
BARS_DIR = DATA_DIR / "bars_daily"
BARS_DIR.mkdir(exist_ok=True)

# European data: most major names go back to 2010-2012 reliably
START_DATE = "2012-01-01"
END_DATE = None
UNIVERSE_SIZE = 500
