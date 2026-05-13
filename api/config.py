"""API configuration — paths, settings."""
from __future__ import annotations
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data files (existing artifacts from research and swing pipelines)
DATA_DIR = PROJECT_ROOT / "data"
PREDICTIONS_PATH = DATA_DIR / "predictions.parquet"
BACKTEST_RESULTS_PATH = DATA_DIR / "backtest_results.csv"
FEATURES_PATH = DATA_DIR / "features.parquet"

# Dividend screener output
RESEARCH_DIR = PROJECT_ROOT / "research"
DIVIDEND_PICKS_PATH = RESEARCH_DIR / "latest_picks.csv"

# API metadata
API_TITLE = "Trading System API"
API_DESCRIPTION = "Dividend screener + cross-sectional mean-reversion strategy"
API_VERSION = "0.1.0"
