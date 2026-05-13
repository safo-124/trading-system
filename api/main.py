from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import (
    API_TITLE, API_DESCRIPTION, API_VERSION,
    DIVIDEND_PICKS_PATH, PREDICTIONS_PATH, BACKTEST_RESULTS_PATH,
)
from api.schemas import HealthResponse
from api.routers import dividend, swing


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
    return {
        "status": "ok",
        "api_version": API_VERSION,
        "data_files": {
            "dividend_picks": DIVIDEND_PICKS_PATH.exists(),
            "swing_predictions": PREDICTIONS_PATH.exists(),
            "backtest_results": BACKTEST_RESULTS_PATH.exists(),
        },
    }


app.include_router(dividend.router)
app.include_router(swing.router)
