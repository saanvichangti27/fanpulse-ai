import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from scipy.stats import rankdata

def compute_engagement_score(df):
    """Computes engagement score (0-100) using RFM-D percentiles."""
    recency = -df['days_since_last_engagement']
    frequency = df['tickets_bought_24m'] + df['merch_purchases_12m']
    monetary = (df['tickets_bought_24m'] * df['avg_ticket_spend_usd']) + df['merch_spend_usd_12m']
    digital = df['app_sessions_30d'] + df['streaming_minutes_30d'] + df['social_shares_30d']

    r_pct = rankdata(recency) / len(recency) * 100
    f_pct = rankdata(frequency) / len(frequency) * 100
    m_pct = rankdata(monetary) / len(monetary) * 100
    d_pct = rankdata(digital) / len(digital) * 100

    return (r_pct + f_pct + m_pct + d_pct) / 4.0

def assign_personas(centroids_df):
    """
    Assigns the 5 persona slugs to the best matching clusters based on centroid profiles.
    Personas: superfans, traveling_ultras, casual_streamers, deal_seekers, lapsed_fans
    """
    personas = ['superfans', 'traveling_ultras', 'casual_streamers', 'deal_seekers', 'lapsed_fans']
    assignments = {}
    
    scores = pd.DataFrame(index=centroids_df.index, columns=personas)
    
    for i, row in centroids_df.iterrows():
        scores.loc[i, 'superfans'] = row['merch_purchases_12m'] + row['social_shares_30d']
        scores.loc[i, 'traveling_ultras'] = row['matches_attended'] + row['tickets_bought_24m']
        scores.loc[i, 'casual_streamers'] = row['streaming_minutes_30d'] - row['matches_attended']
        scores.loc[i, 'deal_seekers'] = row['app_sessions_30d'] + (row['push_opt_in'] * 10)
        scores.loc[i, 'lapsed_fans'] = row['days_since_last_engagement']
    
    for p in personas:
        scores[p] = (scores[p] - scores[p].min()) / (scores[p].max() - scores[p].min() + 1e-9)
    
    available_clusters = list(centroids_df.index)
    
    for p in personas:
        if not available_clusters:
            break
        best_cluster = None
        best_score = -1
        for c in available_clusters:
            if scores.loc[c, p] > best_score:
                best_score = scores.loc[c, p]
                best_cluster = c
        assignments[best_cluster] = p
        available_clusters.remove(best_cluster)
        
    for c in available_clusters:
        best_p = scores.loc[c].astype(float).idxmax()
        assignments[c] = best_p
        
    return assignments

def train_segments():
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_path = os.path.join(repo_root, "data", "synthetic", "fans.csv")
    
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    features = [
        'age', 'matches_attended', 'tickets_bought_24m', 'avg_ticket_spend_usd',
        'merch_purchases_12m', 'merch_spend_usd_12m', 'app_sessions_30d',
        'email_open_rate', 'push_opt_in', 'days_since_last_engagement',
        'streaming_minutes_30d', 'social_shares_30d'
    ]
    
    X = df[features]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    best_k = 0
    best_score = -1
    best_model = None
    
    print("Evaluating KMeans for k=3 to 8...")
    np.random.seed(42)
    sample_indices = np.random.choice(len(X_scaled), size=10000, replace=False)
    X_sample = X_scaled[sample_indices]
    
    for k in range(3, 9):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        score = silhouette_score(X_sample, labels[sample_indices])
        print(f"k={k}, Silhouette Score: {score:.4f}")
        if score > best_score:
            best_score = score
            best_k = k
            best_model = kmeans
            
    print(f"Selected best k={best_k} with score {best_score:.4f}")
    
    df['cluster'] = best_model.labels_
    df['engagement_score'] = compute_engagement_score(df)
    
    centroids_df = df.groupby('cluster')[features].mean()
    
    cluster_to_persona = assign_personas(centroids_df)
    df['segment_id'] = df['cluster'].map(cluster_to_persona)
    
    profiles = {
        "silhouette_score": best_score,
        "n_fans": len(df),
        "segments": []
    }
    
    # We must aggregate in case multiple clusters map to the same persona (if k > 5)
    for persona in ['superfans', 'traveling_ultras', 'casual_streamers', 'deal_seekers', 'lapsed_fans']:
        segment_df = df[df['segment_id'] == persona]
        if len(segment_df) == 0:
            continue
        
        size = len(segment_df)
        top_countries = segment_df['country_code'].value_counts().head(3).index.tolist()
        pref_channel = segment_df['preferred_channel'].mode()[0]
        avg_engagement = segment_df['engagement_score'].mean()
        
        annual_val = ((segment_df['tickets_bought_24m'] * segment_df['avg_ticket_spend_usd']) / 2.0) + segment_df['merch_spend_usd_12m']
        avg_annual_value = annual_val.mean()
        
        churn_risk = (segment_df['days_since_last_engagement'] / 365.0).clip(0, 1).mean()
        
        # Calculate true centroid across potentially multiple clusters
        centroid = segment_df[features].mean().to_dict()
        
        profiles["segments"].append({
            "segment_id": persona,
            "size": size,
            "share_pct": (size / len(df)) * 100,
            "avg_engagement_score": avg_engagement,
            "avg_annual_value_usd": avg_annual_value,
            "top_countries": top_countries,
            "preferred_channel": pref_channel,
            "churn_risk_pct": churn_risk * 100,
            "centroid": centroid
        })
        
    artifacts_dir = os.path.join(os.path.dirname(__file__), "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    
    with open(os.path.join(artifacts_dir, "kmeans_model.pkl"), "wb") as f:
        pickle.dump(best_model, f)
    with open(os.path.join(artifacts_dir, "scaler.pkl"), "wb") as f:
        pickle.dump(scaler, f)
        
    with open(os.path.join(artifacts_dir, "segment_profiles.json"), "w") as f:
        json.dump(profiles, f, indent=2)
        
    print(f"Artifacts saved to {artifacts_dir}")
    
if __name__ == "__main__":
    train_segments()
