"""Audience/demand forecast (Feature 3) — sklearn GradientBoostingRegressor
trained by train_forecast.py on data/historical/matches_history.csv.

buzz_index is a model feature (top importance ~0.80):
- TRAINING buzz (documented synthetic formula, matching gen_match_history.py):
      buzz = clip(0.40*stage/5 + 0.25*rivalry + 0.20*(1 - rank_gap/80) + 0.15*host, 0, 1)
- LIVE buzz at inference (spec §6.4 / contract §F.1), computed from the real
  momentum measured by ingestion/analytics.get_momentum():
      buzz_live = clip(0.6 * min(volume_5m / 500, 1) + 0.4 * clip(volume_ratio / 3, 0, 1), 0, 1)

The reforecast is HONEST: it re-predicts with the model using buzz_live and
reports the delta vs. the same model's baseline-buzz prediction. There is no
additive fudge term.
"""
import os
import json
import pickle
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd

_MODEL = None
_ENCODER = None
_METRICS = None
_IMPORTANCE = None


def _load_artifacts():
    global _MODEL, _ENCODER, _METRICS, _IMPORTANCE
    if _MODEL is None:
        artifacts_dir = os.path.join(os.path.dirname(__file__), "artifacts")
        with open(os.path.join(artifacts_dir, "forecast_model.pkl"), "rb") as f:
            _MODEL = pickle.load(f)
        with open(os.path.join(artifacts_dir, "forecast_encoder.pkl"), "rb") as f:
            _ENCODER = pickle.load(f)
        with open(os.path.join(artifacts_dir, "forecast_metrics.json"), "r") as f:
            _METRICS = json.load(f)
        with open(os.path.join(artifacts_dir, "feature_importance.json"), "r") as f:
            _IMPORTANCE = json.load(f)


def baseline_buzz(features: Dict[str, Any]) -> float:
    """Pre-match buzz — same formula the training data generator used."""
    return float(np.clip(
        0.40 * (features["stage"] / 5.0)
        + 0.25 * features["rivalry_flag"]
        + 0.20 * (1 - features["rank_gap"] / 80.0)
        + 0.15 * features["host_involved"],
        0.0, 1.0,
    ))


def compute_live_buzz(momentum: dict) -> float:
    """Live buzz from a real analytics momentum dict (contract §F.1)."""
    volume_support = min(momentum.get("volume_5m", 0) / 500.0, 1.0)
    strength = float(np.clip(momentum.get("volume_ratio", 1.0) / 3.0, 0.0, 1.0))
    return float(np.clip(0.6 * volume_support + 0.4 * strength, 0.0, 1.0))


def _predict_pct(features: Dict[str, Any], buzz: float) -> float:
    df = pd.DataFrame([{
        "stage": features["stage"],
        "buzz_index_train": buzz,
        "rank_gap": features["rank_gap"],
        "host_involved": features["host_involved"],
        "rivalry_flag": features["rivalry_flag"],
        "venue_capacity": features["venue_capacity"],
        "home_rank": features["home_rank"],
        "away_rank": features["away_rank"],
        "city_population_m": features["city_population_m"],
        "day_of_week": features["day_of_week"],
        "kickoff_hour_local": features["kickoff_hour_local"],
    }])
    pred = float(_MODEL.predict(_ENCODER.transform(df))[0])
    return float(np.clip(pred, 0.0, 1.05))


def predict_audience(features: Dict[str, Any],
                     momentum: Optional[dict] = None) -> Dict[str, Any]:
    """Baseline forecast, or live reforecast when a real momentum dict is given.

    momentum is the dict returned by ingestion.analytics.get_momentum() — the
    caller (W2) is responsible for fetching it; this package stays DB-free.
    """
    _load_artifacts()

    base_pct = _predict_pct(features, baseline_buzz(features))

    if momentum is not None:
        buzz_live = compute_live_buzz(momentum)
        pred_pct = _predict_pct(features, buzz_live)
        is_reforecast = True
        trigger_desc = (
            f"Live buzz {buzz_live:.2f} (volume_5m={momentum.get('volume_5m')}, "
            f"volume_ratio={momentum.get('volume_ratio')}, "
            f"dominant emotion {momentum.get('dominant_emotion')})"
        )
    else:
        pred_pct = base_pct
        is_reforecast = False
        trigger_desc = None

    mae = _METRICS.get("MAE", 0.05)
    demand_index = min(100.0, pred_pct * 100.0)
    sellout_prob = float(np.clip((pred_pct - 0.70) / 0.30, 0.0, 1.0))

    result = {
        "predicted_attendance": int(pred_pct * features["venue_capacity"]),
        "predicted_pct": pred_pct * 100.0,
        "demand_index": round(demand_index, 1),
        "sellout_probability": round(sellout_prob, 3),
        "confidence": round(max(0.0, 1.0 - mae * 2.0), 3),
        "feature_importances": _IMPORTANCE[:5],
        "model_mae": round(mae, 4),
        "is_reforecast": is_reforecast,
        "computed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    if is_reforecast:
        result["baseline_demand_index"] = round(min(100.0, base_pct * 100.0), 1)
        result["delta_vs_baseline_pct"] = round((pred_pct - base_pct) * 100.0, 1)
        result["trigger_description"] = trigger_desc
    return result


if __name__ == "__main__":
    test_match = {
        "stage": 4, "rank_gap": 5, "host_involved": 1, "rivalry_flag": 1,
        "venue_capacity": 80000, "home_rank": 2, "away_rank": 7,
        "city_population_m": 5.0, "day_of_week": 5, "kickoff_hour_local": 18,
    }
    print("Baseline:", predict_audience(test_match))
    goal_momentum = {"volume_5m": 600, "volume_ratio": 4.2, "dominant_emotion": "joy"}
    print("Reforecast:", predict_audience(test_match, momentum=goal_momentum))
