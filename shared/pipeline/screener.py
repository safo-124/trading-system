from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from shared.pipeline.safety_model import DEFAULT_MODEL_VERSION, predict_cut_probability


@dataclass(frozen=True)
class RankedPick:
    rank: int
    ticker: str
    cut_probability: float
    composite_score: float
    recommendation: str
    model_version: str = DEFAULT_MODEL_VERSION


def rank_dividend_stocks(
    feature_frame: pd.DataFrame,
    top_n: int = 10,
    model: Any | None = None,
    model_version: str = DEFAULT_MODEL_VERSION,
) -> list[RankedPick]:
    if feature_frame.empty:
        return []

    frame = feature_frame.copy()
    frame["cut_probability"] = predict_cut_probability(frame, model=model)
    frame["composite_score"] = _composite_score(frame)
    frame["recommendation"] = frame.apply(_recommendation, axis=1)
    ranked = frame.sort_values(
        by=["composite_score", "cut_probability", "ticker"],
        ascending=[False, True, True],
    ).head(top_n)

    return [
        RankedPick(
            rank=rank,
            ticker=str(row.ticker),
            cut_probability=round(float(row.cut_probability), 6),
            composite_score=round(float(row.composite_score), 6),
            recommendation=str(row.recommendation),
            model_version=model_version,
        )
        for rank, row in enumerate(ranked.itertuples(index=False), start=1)
    ]


def _composite_score(frame: pd.DataFrame) -> pd.Series:
    safety_score = 1.0 - _series(frame, "cut_probability", 0.5)
    yield_score = (_series(frame, "dividend_yield", 0.0) / 0.05).clip(lower=0.0, upper=1.0)
    payout_score = (1.0 - ((_series(frame, "payout_ratio", 0.65) - 0.45).abs() / 0.65)).clip(
        lower=0.0,
        upper=1.0,
    )
    debt_score = (1.0 - (_series(frame, "debt_to_equity", 1.0) / 2.0)).clip(
        lower=0.0,
        upper=1.0,
    )
    roe_score = (_series(frame, "roe", 0.0) / 0.25).clip(lower=0.0, upper=1.0)
    margin_score = (_series(frame, "profit_margin", 0.0) / 0.25).clip(lower=0.0, upper=1.0)
    fcf_score = (_series(frame, "fcf", 0.0) > 0).astype(float)
    growth_score = ((_series(frame, "dividend_growth_ltm", 0.0) + 0.10) / 0.30).clip(
        lower=0.0,
        upper=1.0,
    )

    quality_score = (debt_score + roe_score + margin_score + fcf_score) / 4.0
    composite = (
        0.35 * safety_score
        + 0.25 * quality_score
        + 0.20 * yield_score
        + 0.10 * payout_score
        + 0.10 * growth_score
    )
    return (100.0 * composite).clip(lower=0.0, upper=100.0)


def _recommendation(row: pd.Series) -> str:
    score = float(row["composite_score"])
    cut_probability = float(row["cut_probability"])
    if score >= 75 and cut_probability <= 0.25:
        return "BUY"
    if score >= 60 and cut_probability <= 0.40:
        return "WATCH"
    return "AVOID"


def _series(frame: pd.DataFrame, column: str, default: float) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    values = pd.to_numeric(frame[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
    return values.fillna(default).astype(float)
