from sqlalchemy import text

from .db import SessionLocal, engine
from .models_db import Base, Match

# Real FIFA World Cup 2026 knockout schedule around the current date
# (2026-07-07), per FIFA/Al Jazeera/ESPN published fixtures & results:
#   R16 Jul 4: France 1-0 Paraguay (Philadelphia)
#   R16 Jul 7: Argentina vs Egypt (Atlanta, 16:00Z) — the live demo match
#   R16 Jul 7: Switzerland vs Colombia (Vancouver, 20:00Z)
#   QF  Jul 9: France vs Morocco (Boston) | Jul 10: Belgium vs Spain (LA)
#   QF  Jul 11: Norway vs England (Miami)
# stage ints: 2 = Round of 16, 3 = Quarter-Final (ui_meta.STAGE_LABELS).
# home/away ranks are the teams' FIFA rankings (approx, mid-2026); rivalry
# flags mark storied rematches (FRA-MAR: 2022 semi). Venue capacities real.
FIXTURES = [
    dict(id="m_001", home_team="Argentina", away_team="Egypt",
         kickoff_time="2026-07-07T16:00:00Z", stage=2, venue_capacity=71000,
         city="Atlanta", city_population_m=0.5, home_rank=1, away_rank=36,
         rivalry_flag=0, host_involved=0, status="upcoming"),
    dict(id="m_002", home_team="Switzerland", away_team="Colombia",
         kickoff_time="2026-07-07T20:00:00Z", stage=2, venue_capacity=54500,
         city="Vancouver", city_population_m=0.7, home_rank=20, away_rank=14,
         rivalry_flag=0, host_involved=1, status="upcoming"),
    dict(id="m_003", home_team="France", away_team="Morocco",
         kickoff_time="2026-07-09T20:00:00Z", stage=3, venue_capacity=65878,
         city="Boston", city_population_m=0.7, home_rank=2, away_rank=12,
         rivalry_flag=1, host_involved=0, status="upcoming"),
    dict(id="m_004", home_team="Belgium", away_team="Spain",
         kickoff_time="2026-07-10T16:00:00Z", stage=3, venue_capacity=70240,
         city="Los Angeles", city_population_m=3.9, home_rank=8, away_rank=3,
         rivalry_flag=0, host_involved=0, status="upcoming"),
    dict(id="m_005", home_team="Norway", away_team="England",
         kickoff_time="2026-07-11T21:00:00Z", stage=3, venue_capacity=65326,
         city="Miami", city_population_m=0.4, home_rank=28, away_rank=4,
         rivalry_flag=0, host_involved=0, status="upcoming"),
    dict(id="m_006", home_team="France", away_team="Paraguay",
         kickoff_time="2026-07-04T21:00:00Z", stage=2, venue_capacity=69796,
         city="Philadelphia", city_population_m=1.6, home_rank=2, away_rank=43,
         rivalry_flag=0, host_involved=0, status="finished",
         home_score=1, away_score=0),   # real final score
]


def seed_db():
    # Base.metadata.create_all handles table creation without migrations
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Reseed when the fixture list changed (compares id+teams+kickoff), so
        # schedule updates land without hand-deleting the sqlite file.
        existing = {(m.id, m.home_team, m.away_team, m.kickoff_time)
                    for m in db.query(Match).all()}
        desired = {(f["id"], f["home_team"], f["away_team"], f["kickoff_time"])
                   for f in FIXTURES}
        if existing == desired:
            print("Database already seeded (fixtures current).")
            return

        if existing:
            print("Fixture list changed — reseeding matches and dependent data.")
            for table in ("messages", "moments", "campaigns", "content_ideas", "forecasts"):
                db.execute(text(f"DELETE FROM {table}"))
            db.query(Match).delete()
            db.commit()

        db.add_all([Match(**f) for f in FIXTURES])
        db.commit()
        print(f"Database seeded with {len(FIXTURES)} real WC2026 fixtures.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()
