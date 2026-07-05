import os
import json
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def train_forecast():
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_path = os.path.join(repo_root, "data", "historical", "matches_history.csv")
    
    print(f"Loading historical data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Features per API Contract
    numeric_features = [
        'stage', 'buzz_index_train', 'rank_gap', 'host_involved', 
        'rivalry_flag', 'venue_capacity', 'home_rank', 'away_rank', 
        'city_population_m', 'kickoff_hour_local'
    ]
    categorical_features = ['day_of_week']
    
    X = df[numeric_features + categorical_features]
    y = df['attendance_pct']
    
    # Preprocessing
    # We will one-hot encode day_of_week to have an encoder to save (as requested by user)
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ],
        remainder='passthrough'
    )
    
    X_processed = preprocessor.fit_transform(X)
    
    # Train-test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X_processed, y, test_size=0.20, random_state=42)
    
    print("Training GradientBoostingRegressor...")
    model = GradientBoostingRegressor(random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    print(f"Metrics - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R2: {r2:.4f}")
    
    # Feature importances
    cat_feature_names = preprocessor.named_transformers_['cat'].get_feature_names_out(categorical_features)
    feature_names = list(cat_feature_names) + numeric_features
    importances = model.feature_importances_
    
    feature_importance_list = [
        {"feature": name, "importance": float(imp)}
        for name, imp in zip(feature_names, importances)
    ]
    # Sort descending
    feature_importance_list = sorted(feature_importance_list, key=lambda x: x["importance"], reverse=True)
    
    # Save artifacts
    artifacts_dir = os.path.join(os.path.dirname(__file__), "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    
    with open(os.path.join(artifacts_dir, "forecast_model.pkl"), "wb") as f:
        pickle.dump(model, f)
        
    with open(os.path.join(artifacts_dir, "forecast_encoder.pkl"), "wb") as f:
        pickle.dump(preprocessor, f)
        
    metrics = {
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    }
    with open(os.path.join(artifacts_dir, "forecast_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
        
    with open(os.path.join(artifacts_dir, "feature_importance.json"), "w") as f:
        json.dump(feature_importance_list, f, indent=2)
        
    print(f"Artifacts saved to {artifacts_dir}")

if __name__ == "__main__":
    train_forecast()
