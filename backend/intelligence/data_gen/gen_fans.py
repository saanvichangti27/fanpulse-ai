import numpy as np
import pandas as pd
import os
import uuid

# Set seed for reproducibility
np.random.seed(42)

NUM_FANS = 50000

# Constants for Generation
COUNTRIES = ["BR", "AR", "FR", "UK", "US", "IN", "MX", "DE", "ES", "IT"]
TEAMS = ["Brazil", "Argentina", "France", "England", "USA", "India", "Mexico", "Germany", "Spain", "Italy"]

def generate_fans():
    print(f"Generating {NUM_FANS} synthetic fans...")
    
    # 1. Persona-First Sampling
    # Superfan (8%), Traveling Ultra (7%), Casual Streamer (35%), Deal-Seeker (30%), Lapsed Fan (20%)
    personas = ["Superfan", "Traveling Ultra", "Casual Streamer", "Deal-Seeker", "Lapsed Fan"]
    probs = [0.08, 0.07, 0.35, 0.30, 0.20]
    
    # Generate the hidden persona column
    sampled_personas = np.random.choice(personas, size=NUM_FANS, p=probs)
    
    df = pd.DataFrame({'_persona': sampled_personas})
    df['fan_id'] = [f"f_{uuid.uuid4().hex[:8]}" for _ in range(NUM_FANS)]
    df['age'] = np.random.randint(16, 71, size=NUM_FANS)
    df['country_code'] = np.random.choice(COUNTRIES, size=NUM_FANS)
    df['favourite_team'] = np.random.choice(TEAMS, size=NUM_FANS)
    
    # Initialize columns
    df['matches_attended'] = 0.0
    df['tickets_bought_24m'] = 0.0
    df['avg_ticket_spend_usd'] = 0.0
    df['merch_purchases_12m'] = 0.0
    df['merch_spend_usd_12m'] = 0.0
    df['app_sessions_30d'] = 0.0
    df['email_open_rate'] = 0.0
    df['push_opt_in'] = 0.0
    df['days_since_last_engagement'] = 0.0
    df['streaming_minutes_30d'] = 0.0
    df['social_shares_30d'] = 0.0
    df['preferred_channel'] = 'email'
    
    # 2. Apply Distributions Based on Persona
    for persona in personas:
        mask = df['_persona'] == persona
        n_p = mask.sum()
        
        if persona == "Superfan":
            df.loc[mask, 'matches_attended'] = np.random.poisson(lam=4, size=n_p)
            df.loc[mask, 'tickets_bought_24m'] = np.random.poisson(lam=5, size=n_p)
            df.loc[mask, 'avg_ticket_spend_usd'] = np.random.lognormal(mean=np.log(150), sigma=0.4, size=n_p)
            df.loc[mask, 'merch_purchases_12m'] = np.random.poisson(lam=3, size=n_p)
            df.loc[mask, 'merch_spend_usd_12m'] = np.random.lognormal(mean=np.log(200), sigma=0.5, size=n_p)
            df.loc[mask, 'app_sessions_30d'] = np.random.negative_binomial(n=10, p=0.3, size=n_p)
            df.loc[mask, 'email_open_rate'] = np.random.beta(a=7, b=3, size=n_p)
            df.loc[mask, 'push_opt_in'] = np.random.binomial(n=1, p=0.85, size=n_p)
            df.loc[mask, 'days_since_last_engagement'] = np.random.exponential(scale=3, size=n_p)
            df.loc[mask, 'streaming_minutes_30d'] = np.random.gamma(shape=10, scale=30, size=n_p)
            df.loc[mask, 'social_shares_30d'] = np.random.poisson(lam=8, size=n_p)
            df.loc[mask, 'preferred_channel'] = np.random.choice(["push", "instagram"], size=n_p, p=[0.6, 0.4])
            
        elif persona == "Traveling Ultra":
            df.loc[mask, 'matches_attended'] = np.random.poisson(lam=8, size=n_p)
            df.loc[mask, 'tickets_bought_24m'] = np.random.poisson(lam=12, size=n_p)
            df.loc[mask, 'avg_ticket_spend_usd'] = np.random.lognormal(mean=np.log(300), sigma=0.3, size=n_p)
            df.loc[mask, 'merch_purchases_12m'] = np.random.poisson(lam=2, size=n_p)
            df.loc[mask, 'merch_spend_usd_12m'] = np.random.lognormal(mean=np.log(100), sigma=0.5, size=n_p)
            df.loc[mask, 'app_sessions_30d'] = np.random.negative_binomial(n=8, p=0.4, size=n_p)
            df.loc[mask, 'email_open_rate'] = np.random.beta(a=5, b=5, size=n_p)
            df.loc[mask, 'push_opt_in'] = np.random.binomial(n=1, p=0.7, size=n_p)
            df.loc[mask, 'days_since_last_engagement'] = np.random.exponential(scale=5, size=n_p)
            df.loc[mask, 'streaming_minutes_30d'] = np.random.gamma(shape=2, scale=20, size=n_p)
            df.loc[mask, 'social_shares_30d'] = np.random.poisson(lam=2, size=n_p)
            df.loc[mask, 'preferred_channel'] = np.random.choice(["email", "push"], size=n_p, p=[0.7, 0.3])
            
        elif persona == "Casual Streamer":
            df.loc[mask, 'matches_attended'] = np.random.poisson(lam=0.2, size=n_p)
            df.loc[mask, 'tickets_bought_24m'] = np.random.poisson(lam=0.2, size=n_p)
            df.loc[mask, 'avg_ticket_spend_usd'] = np.random.lognormal(mean=np.log(50), sigma=0.5, size=n_p)
            df.loc[mask, 'merch_purchases_12m'] = np.random.poisson(lam=0.5, size=n_p)
            df.loc[mask, 'merch_spend_usd_12m'] = np.random.lognormal(mean=np.log(40), sigma=0.8, size=n_p)
            df.loc[mask, 'app_sessions_30d'] = np.random.negative_binomial(n=3, p=0.3, size=n_p)
            df.loc[mask, 'email_open_rate'] = np.random.beta(a=3, b=7, size=n_p)
            df.loc[mask, 'push_opt_in'] = np.random.binomial(n=1, p=0.4, size=n_p)
            df.loc[mask, 'days_since_last_engagement'] = np.random.exponential(scale=15, size=n_p)
            df.loc[mask, 'streaming_minutes_30d'] = np.random.gamma(shape=15, scale=40, size=n_p)
            df.loc[mask, 'social_shares_30d'] = np.random.poisson(lam=3, size=n_p)
            df.loc[mask, 'preferred_channel'] = np.random.choice(["youtube", "instagram"], size=n_p, p=[0.8, 0.2])
            
        elif persona == "Deal-Seeker":
            df.loc[mask, 'matches_attended'] = np.random.poisson(lam=1, size=n_p)
            df.loc[mask, 'tickets_bought_24m'] = np.random.poisson(lam=1, size=n_p)
            df.loc[mask, 'avg_ticket_spend_usd'] = np.random.lognormal(mean=np.log(60), sigma=0.3, size=n_p)
            df.loc[mask, 'merch_purchases_12m'] = np.random.poisson(lam=1.5, size=n_p)
            df.loc[mask, 'merch_spend_usd_12m'] = np.random.lognormal(mean=np.log(35), sigma=0.4, size=n_p)
            df.loc[mask, 'app_sessions_30d'] = np.random.negative_binomial(n=15, p=0.4, size=n_p)
            df.loc[mask, 'email_open_rate'] = np.random.beta(a=8, b=2, size=n_p)
            df.loc[mask, 'push_opt_in'] = np.random.binomial(n=1, p=0.95, size=n_p)
            df.loc[mask, 'days_since_last_engagement'] = np.random.exponential(scale=2, size=n_p)
            df.loc[mask, 'streaming_minutes_30d'] = np.random.gamma(shape=4, scale=20, size=n_p)
            df.loc[mask, 'social_shares_30d'] = np.random.poisson(lam=1, size=n_p)
            df.loc[mask, 'preferred_channel'] = np.random.choice(["push", "email"], size=n_p, p=[0.8, 0.2])
            
        elif persona == "Lapsed Fan":
            df.loc[mask, 'matches_attended'] = np.random.poisson(lam=0.5, size=n_p)
            df.loc[mask, 'tickets_bought_24m'] = np.random.poisson(lam=0.5, size=n_p)
            df.loc[mask, 'avg_ticket_spend_usd'] = np.random.lognormal(mean=np.log(80), sigma=0.5, size=n_p)
            df.loc[mask, 'merch_purchases_12m'] = np.random.poisson(lam=0.1, size=n_p)
            df.loc[mask, 'merch_spend_usd_12m'] = np.random.lognormal(mean=np.log(20), sigma=1.0, size=n_p)
            df.loc[mask, 'app_sessions_30d'] = np.random.negative_binomial(n=1, p=0.8, size=n_p)
            df.loc[mask, 'email_open_rate'] = np.random.beta(a=2, b=8, size=n_p)
            df.loc[mask, 'push_opt_in'] = np.random.binomial(n=1, p=0.1, size=n_p)
            df.loc[mask, 'days_since_last_engagement'] = np.random.exponential(scale=200, size=n_p)
            df.loc[mask, 'streaming_minutes_30d'] = np.random.gamma(shape=1, scale=10, size=n_p)
            df.loc[mask, 'social_shares_30d'] = np.random.poisson(lam=0.1, size=n_p)
            df.loc[mask, 'preferred_channel'] = np.random.choice(["email", "youtube"], size=n_p, p=[0.6, 0.4])

    # 3. Add Realistic Cross-Feature Noise
    df.loc[df['tickets_bought_24m'] == 0, 'avg_ticket_spend_usd'] = 0.0
    df.loc[df['merch_purchases_12m'] == 0, 'merch_spend_usd_12m'] = 0.0
    
    df['email_open_rate'] = df['email_open_rate'].clip(0, 1)
    df['streaming_minutes_30d'] = df['streaming_minutes_30d'].round().astype(int)
    df['avg_ticket_spend_usd'] = df['avg_ticket_spend_usd'].round(2)
    df['merch_spend_usd_12m'] = df['merch_spend_usd_12m'].round(2)
    df['days_since_last_engagement'] = df['days_since_last_engagement'].round().astype(int).clip(0, 365*5)
    
    # Validation Step
    assert len(df) == NUM_FANS, f"Expected {NUM_FANS} rows, got {len(df)}"
    
    expected_cols = [
        "fan_id", "age", "country_code", "favourite_team", "matches_attended", 
        "tickets_bought_24m", "avg_ticket_spend_usd", "merch_purchases_12m", 
        "merch_spend_usd_12m", "app_sessions_30d", "email_open_rate", 
        "push_opt_in", "days_since_last_engagement", "streaming_minutes_30d", 
        "social_shares_30d", "preferred_channel"
    ]
    actual_cols = [c for c in df.columns if c != '_persona']
    assert set(actual_cols) == set(expected_cols), f"Schema mismatch. Expected {expected_cols}, got {actual_cols}"
    assert df.isnull().sum().sum() == 0, "Dataset contains missing values"
    
    counts = df['_persona'].value_counts(normalize=True)
    print(f"Persona distribution:\n{counts}")
    
    # Drop hidden persona
    df = df.drop(columns=['_persona'])
    
    # Ensure correct column order
    df = df[expected_cols]
    
    # Save
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    out_dir = os.path.join(repo_root, "data", "synthetic")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "fans.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved synthetic fans to {out_path}")

if __name__ == "__main__":
    generate_fans()
