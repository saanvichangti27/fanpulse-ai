import numpy as np
import pandas as pd
import os
import uuid

# Set seed for reproducibility
np.random.seed(42)

NUM_MATCHES = 2500

TEAMS = [
    "Brazil", "Argentina", "France", "England", "USA", "India", "Mexico",
    "Germany", "Spain", "Italy", "Portugal", "Netherlands", "Belgium",
    "Colombia", "Uruguay", "Croatia", "Morocco", "Japan", "Senegal"
]

def generate_matches():
    print(f"Generating {NUM_MATCHES} historical matches...")
    
    df = pd.DataFrame()
    df['match_id'] = [f"m_{uuid.uuid4().hex[:8]}" for _ in range(NUM_MATCHES)]
    
    # Contract fields
    df['stage'] = np.random.randint(0, 6, size=NUM_MATCHES)  # 0 to 5
    
    # Teams
    home_teams = []
    away_teams = []
    for _ in range(NUM_MATCHES):
        t1, t2 = np.random.choice(TEAMS, size=2, replace=False)
        home_teams.append(t1)
        away_teams.append(t2)
    df['home_team'] = home_teams
    df['away_team'] = away_teams
    
    # Ranks (1 to 100 realistically for these teams)
    df['home_rank'] = np.random.randint(1, 101, size=NUM_MATCHES)
    df['away_rank'] = np.random.randint(1, 101, size=NUM_MATCHES)
    df['rank_gap'] = np.abs(df['home_rank'] - df['away_rank'])
    
    df['rivalry_flag'] = np.random.binomial(n=1, p=0.15, size=NUM_MATCHES)
    df['host_involved'] = np.random.binomial(n=1, p=0.08, size=NUM_MATCHES)
    df['city_population_m'] = np.random.uniform(0.5, 10.0, size=NUM_MATCHES).round(2)
    df['venue_capacity'] = np.random.choice([40000, 60000, 80000, 90000], size=NUM_MATCHES)
    df['day_of_week'] = np.random.randint(0, 7, size=NUM_MATCHES)
    df['kickoff_hour_local'] = np.random.randint(12, 23, size=NUM_MATCHES)
    
    # Formulas
    stage_norm = df['stage'] / 5.0
    rank_gap_norm = df['rank_gap'] / 80.0
    
    buzz_noise = np.random.normal(0, 0.05, size=NUM_MATCHES)
    df['buzz_index_train'] = (
        0.40 * stage_norm +
        0.25 * df['rivalry_flag'] +
        0.20 * (1 - rank_gap_norm) +
        0.15 * df['host_involved'] +
        buzz_noise
    ).clip(0, 1)
    
    attendance_noise = np.random.normal(0, 0.05, size=NUM_MATCHES)
    df['attendance_pct'] = (
        0.30 +
        0.30 * stage_norm +
        0.20 * df['rivalry_flag'] +
        0.15 * df['host_involved'] +
        0.05 * (1 - rank_gap_norm) +
        attendance_noise
    ).clip(0.35, 1.05)
    
    # Schema validation
    expected_cols = [
        "match_id", "stage", "home_team", "away_team", "home_rank", "away_rank",
        "rank_gap", "rivalry_flag", "host_involved", "city_population_m",
        "venue_capacity", "day_of_week", "kickoff_hour_local", "buzz_index_train",
        "attendance_pct"
    ]
    
    # Ensure correct column order
    df = df[expected_cols]
    
    assert len(df) == NUM_MATCHES, f"Expected {NUM_MATCHES} rows, got {len(df)}"
    assert set(df.columns) == set(expected_cols), f"Schema mismatch."
    assert df.isnull().sum().sum() == 0, "Dataset contains missing values"
    
    # Save
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    out_dir = os.path.join(repo_root, "data", "historical")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "matches_history.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved historical matches to {out_path}")

if __name__ == "__main__":
    generate_matches()
