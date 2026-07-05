import os
import json
import pickle
import pandas as pd
import numpy as np
from typing import Dict, Any

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

def compute_live_buzz(momentum: float, host_involved: int, rivalry_flag: int) -> float:
    """Computes live buzz index based on live momentum ratio."""
    return np.clip(
        0.35 + 0.45 * momentum + 0.10 * host_involved + 0.10 * rivalry_flag,
        0.0,
        1.0
    )

def predict_audience(features: Dict[str, Any], momentum: float = None) -> Dict[str, Any]:
    """
    Predicts attendance percentage.
    If momentum is provided, computes live buzz and applies momentum adjustment.
    """
    _load_artifacts()
    
    # Calculate buzz_index
    if momentum is not None:
        buzz = compute_live_buzz(momentum, features['host_involved'], features['rivalry_flag'])
        is_reforecast = True
    else:
        # Default baseline buzz for pre-match if no momentum
        buzz = np.clip(
            0.40 * (features['stage'] / 5.0) +
            0.25 * features['rivalry_flag'] +
            0.20 * (1 - features['rank_gap'] / 80.0) +
            0.15 * features['host_involved'],
            0.0, 1.0
        )
        is_reforecast = False

    # Prepare DataFrame for model
    df_features = pd.DataFrame([{
        'stage': features['stage'],
        'buzz_index_train': buzz,
        'rank_gap': features['rank_gap'],
        'host_involved': features['host_involved'],
        'rivalry_flag': features['rivalry_flag'],
        'venue_capacity': features['venue_capacity'],
        'home_rank': features['home_rank'],
        'away_rank': features['away_rank'],
        'city_population_m': features['city_population_m'],
        'day_of_week': features['day_of_week'],
        'kickoff_hour_local': features['kickoff_hour_local']
    }])
    
    X_processed = _ENCODER.transform(df_features)
    
    # Predict percentage
    pred_pct = _MODEL.predict(X_processed)[0]
    baseline_pct = pred_pct
    
    trigger_desc = None
    delta = 0.0
    
    # Apply live adjustment if momentum is provided
    if momentum is not None:
        if momentum >= 0.90:
            adj = 0.05
        elif momentum >= 0.75:
            adj = 0.04
        elif momentum >= 0.60:
            adj = 0.03
        elif momentum >= 0.40:
            adj = 0.02
        elif momentum >= 0.20:
            adj = 0.01
        else:
            adj = 0.0
            
        pred_pct += adj
        delta = adj * 100.0
        trigger_desc = f"Live momentum {momentum:.2f} added +{adj*100:.1f}pp."
        
    # Clip between 0 and 1.05
    pred_pct = np.clip(pred_pct, 0.0, 1.05)
    
    predicted_attendance = int(pred_pct * features['venue_capacity'])
    
    # Confidence from MAE
    mae = _METRICS.get("MAE", 0.05)
    confidence = max(0.0, 1.0 - (mae * 2.0))
    
    demand_index = min(100.0, pred_pct * 100.0)
    sellout_prob = min(1.0, max(0.0, (pred_pct - 0.70) / 0.30))  # Scale probability to approach 1.0 near 100%
    
    result = {
        "predicted_attendance": predicted_attendance,
        "predicted_pct": pred_pct * 100.0,
        "demand_index": demand_index,
        "sellout_probability": sellout_prob,
        "confidence": confidence,
        "feature_importances": _IMPORTANCE[:5],  # top 5
        "model_mae": mae,
        "is_reforecast": is_reforecast
    }
    
    if is_reforecast:
        result["baseline_demand_index"] = baseline_pct * 100.0
        result["delta_vs_baseline_pct"] = delta
        result["trigger_description"] = trigger_desc
        
    return result

if __name__ == "__main__":
    # Test script functionality
    test_match = {
        'stage': 4,
        'rank_gap': 5,
        'host_involved': 1,
        'rivalry_flag': 1,
        'venue_capacity': 80000,
        'home_rank': 2,
        'away_rank': 7,
        'city_population_m': 5.0,
        'day_of_week': 5,
        'kickoff_hour_local': 18
    }
    
    print("Baseline Forecast (No momentum):")
    res_base = predict_audience(test_match)
    for k, v in res_base.items():
        print(f"  {k}: {v}")
        
    print("\nLive Reforecast (Momentum 0.95):")
    res_live = predict_audience(test_match, momentum=0.95)
    for k, v in res_live.items():
        print(f"  {k}: {v}")
