from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from shared.pipeline.features import FEATURE_COLUMNS

DEFAULT_MODEL_VERSION = "heuristic-safety-v1"


def train_cut_classifier(
    training_frame: pd.DataFrame,
    target_column: str = "cut_next_period",
) -> Pipeline:
    if target_column not in training_frame.columns:
        raise ValueError(f"Missing target column: {target_column}")

    y = training_frame[target_column].astype(int)
    if y.nunique() < 2:
        raise ValueError("Training data must contain both cut and non-cut examples")

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                FEATURE_COLUMNS,
            )
        ],
        remainder="drop",
    )
    classifier = LogisticRegression(class_weight="balanced", max_iter=1000)
    model = Pipeline(steps=[("preprocessor", preprocessor), ("classifier", classifier)])
    return model.fit(training_frame, y)


def predict_cut_probability(
    feature_frame: pd.DataFrame,
    model: Any | None = None,
) -> pd.Series:
    if feature_frame.empty:
        return pd.Series(dtype=float)

    if model is not None:
        probabilities = model.predict_proba(feature_frame)[:, 1]
        return pd.Series(probabilities, index=feature_frame.index, dtype=float).clip(0.01, 0.99)

    return _heuristic_cut_probability(feature_frame)


def _heuristic_cut_probability(feature_frame: pd.DataFrame) -> pd.Series:
    payout = _series(feature_frame, "payout_ratio", 0.60).clip(lower=0.0, upper=2.5)
    debt = _series(feature_frame, "debt_to_equity", 0.8).clip(lower=0.0, upper=4.0)
    roe = _series(feature_frame, "roe", 0.10).clip(lower=-0.5, upper=0.7)
    margin = _series(feature_frame, "profit_margin", 0.10).clip(lower=-0.5, upper=0.7)
    fcf = _series(feature_frame, "fcf", 0.0)
    dividend_yield = _series(feature_frame, "dividend_yield", 0.03).clip(lower=0.0, upper=0.20)
    growth = _series(feature_frame, "dividend_growth_ltm", 0.0).clip(lower=-1.0, upper=1.0)
    volatility = _series(feature_frame, "dividend_volatility", 0.0).clip(lower=0.0, upper=2.0)

    payout_pressure = ((payout - 0.65) / 0.65).clip(lower=0.0)
    debt_pressure = ((debt - 1.0) / 1.5).clip(lower=0.0)
    yield_pressure = ((dividend_yield - 0.06) / 0.06).clip(lower=0.0)
    fcf_support = (fcf > 0).astype(float)

    raw_score = (
        -1.65
        + 1.85 * payout_pressure
        + 0.90 * debt_pressure
        + 0.75 * yield_pressure
        + 0.45 * volatility
        - 1.10 * roe
        - 0.85 * margin
        - 0.55 * fcf_support
        - 0.30 * growth
    )
    probabilities = 1 / (1 + np.exp(-raw_score))
    return pd.Series(probabilities, index=feature_frame.index, dtype=float).clip(0.01, 0.99)


def _series(frame: pd.DataFrame, column: str, default: float) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default).astype(float)
