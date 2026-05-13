"""
Train a SINGLE production LightGBM model on the entire training set.

Unlike swing/train.py (walk-forward validation), this trains on every
available row and saves the model + feature metadata to disk for live 
inference.

Output:
  data/model_production.txt       — LightGBM model file
  data/model_metadata.json        — features list, target, training stats
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import lightgbm as lgb
import pandas as pd

from swing_eu.config import DATA_DIR


# Match the feature list from swing/train.py exactly
MR_FEATURES = [
    "ret_5d", "ret_20d", "ret_60d", "ret_120d",
    "logret_5d", "logret_20d",
    "kalman_deviation",
]
XS_FEATURES = ["ret_120d_xs_rank"]
VOL_FEATURES = ["vol_regime_z"]
VOL_FEAT = ["volume_zscore_20d"]
FEATURES = MR_FEATURES + XS_FEATURES + VOL_FEATURES + VOL_FEAT

TARGET = "fwd_ret_5d_xs_rank"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path",
                        default=str(DATA_DIR / "training_set.parquet"))
    parser.add_argument("--out-model",
                        default=str(DATA_DIR / "model_production.txt"))
    parser.add_argument("--out-meta",
                        default=str(DATA_DIR / "model_metadata.json"))
    args = parser.parse_args()

    in_path = Path(args.in_path)
    if not in_path.exists():
        print(f"ERROR: {in_path} not found. Run swing/labels.py first.")
        return 1

    print(f"Loading training set from {in_path}")
    df = pd.read_parquet(in_path)
    print(f"  shape: {df.shape}")
    print(f"  date range: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")

    # Drop rows missing features or target
    before = len(df)
    df = df.dropna(subset=FEATURES + [TARGET])
    print(f"  dropped {before - len(df):,} rows with missing features/target")
    print(f"  training rows: {len(df):,}")

    X = df[FEATURES]
    y = df[TARGET]

    print("\nTraining LightGBM on all data...")
    model = lgb.LGBMRegressor(
        n_estimators=300,
        learning_rate=0.03,
        max_depth=6,
        num_leaves=31,
        min_child_samples=200,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=42,
        verbose=-1,
        n_jobs=-1,
    )
    model.fit(X, y)

    # Save model
    out_model = Path(args.out_model)
    model.booster_.save_model(str(out_model))
    print(f"\n  Model saved to: {out_model}")

    # Save metadata
    metadata = {
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "features": FEATURES,
        "target": TARGET,
        "training_rows": int(len(df)),
        "training_start": df["timestamp"].min().date().isoformat(),
        "training_end": df["timestamp"].max().date().isoformat(),
        "model_params": {
            "n_estimators": 300,
            "learning_rate": 0.03,
            "max_depth": 6,
            "num_leaves": 31,
            "min_child_samples": 200,
            "reg_alpha": 0.1,
            "reg_lambda": 0.1,
        },
        "feature_importance": dict(
            zip(FEATURES, [int(x) for x in model.feature_importances_])
        ),
    }
    out_meta = Path(args.out_meta)
    out_meta.write_text(json.dumps(metadata, indent=2))
    print(f"  Metadata saved to: {out_meta}")

    print("\n  Top features:")
    importance = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
    print(importance.head(8).to_string())

    return 0


if __name__ == "__main__":
    sys.exit(main())
