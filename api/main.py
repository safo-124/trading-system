from __future__ import annotations
from pathlib import Path as _Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import (
    API_TITLE, API_DESCRIPTION, API_VERSION,
    DIVIDEND_PICKS_PATH, PREDICTIONS_PATH, BACKTEST_RESULTS_PATH,
)
from api.schemas import HealthResponse
from api.routers import dividend, swing, swing_eu, swing_africa


app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
)

# CORS for future frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
def health():
    eu_dir = _Path(__file__).resolve().parent.parent / "data_eu"
    return {
        "status": "ok",
        "api_version": API_VERSION,
        "data_files": {
            "dividend_picks": DIVIDEND_PICKS_PATH.exists(),
            "swing_us_predictions": PREDICTIONS_PATH.exists(),
            "swing_us_backtest": BACKTEST_RESULTS_PATH.exists(),
            "swing_us_model": (eu_dir.parent / "data" / "model_production.txt").exists(),
            "swing_eu_predictions": (eu_dir / "predictions.parquet").exists(),
            "swing_eu_backtest": (eu_dir / "backtest_results.csv").exists(),
            "swing_eu_model": (eu_dir / "model_production.txt").exists(),
            "swing_africa_predictions": (_Path(__file__).resolve().parent.parent / "data_africa" / "predictions.parquet").exists(),
            "swing_africa_backtest": (_Path(__file__).resolve().parent.parent / "data_africa" / "backtest_results.csv").exists(),
            "swing_africa_model": (_Path(__file__).resolve().parent.parent / "data_africa" / "model_production.txt").exists(),
        },
    }


app.include_router(dividend.router)
app.include_router(swing.router)
app.include_router(swing_eu.router)
app.include_router(swing_africa.router)
