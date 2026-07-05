from .db import SessionLocal, engine
from .models_db import Base, Match

def seed_db():
    # Base.metadata.create_all handles table creation without migrations
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    if db.query(Match).first():
        print("Database already seeded.")
        db.close()
        return

    # Seed 6 matches for testing
    matches = [
        Match(id="m_001", home_team="Brazil", away_team="Argentina", kickoff_time="2026-07-04T18:00:00Z", stage=4, venue_capacity=88000, city="Dallas", city_population_m=1.3, home_rank=1, away_rank=2, rivalry_flag=1, status="live"),
        Match(id="m_002", home_team="France", away_team="England", kickoff_time="2026-07-05T18:00:00Z", stage=4, venue_capacity=80000, city="New York", city_population_m=8.4, home_rank=3, away_rank=4, rivalry_flag=1, status="upcoming"),
        Match(id="m_003", home_team="Spain", away_team="Germany", kickoff_time="2026-07-06T18:00:00Z", stage=4, venue_capacity=70000, city="Miami", city_population_m=0.4, home_rank=5, away_rank=6, rivalry_flag=1, status="upcoming"),
        Match(id="m_004", home_team="USA", away_team="Mexico", kickoff_time="2026-07-07T18:00:00Z", stage=4, venue_capacity=90000, city="Los Angeles", city_population_m=3.9, home_rank=11, away_rank=15, rivalry_flag=1, host_involved=1, status="upcoming"),
        Match(id="m_005", home_team="Japan", away_team="South Korea", kickoff_time="2026-07-08T18:00:00Z", stage=4, venue_capacity=65000, city="Seattle", city_population_m=0.7, home_rank=20, away_rank=22, rivalry_flag=1, status="upcoming"),
        Match(id="m_006", home_team="Senegal", away_team="Morocco", kickoff_time="2026-07-09T18:00:00Z", stage=4, venue_capacity=72000, city="Atlanta", city_population_m=0.5, home_rank=18, away_rank=13, rivalry_flag=0, status="upcoming"),
    ]
    
    db.add_all(matches)
    db.commit()
    db.close()
    print("Database seeded with 6 matches.")

if __name__ == "__main__":
    seed_db()
