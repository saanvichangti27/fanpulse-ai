import os
import asyncio
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from dotenv import load_dotenv

# Load backend/.env regardless of the current working directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from .routers import matches, fans, campaigns, predictions, roi, replay, ui
from .seed import seed_db
from .db import engine, SessionLocal
from .models_db import Base
from .automation import on_moment
from ..ingestion import service as ingestion_service
from ..ingestion.service import run_ingestion
from ..contracts import Industry

app = FastAPI(title="FanPulse AI API", version="3.0.0")

# The frontend dev server (locked emergent-ui build, craco on :3000) fetches
# /api/v1/ui/bootstrap cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STARRED = {"food_delivery", "merch_apparel", "beverages", "streaming_ott", "content_creator"}
DISPLAY = {
    "food_delivery": "Food Delivery & QSR", "merch_apparel": "Sports Merch & Apparel",
    "beverages": "Beverages", "streaming_ott": "Streaming / OTT",
    "content_creator": "Content Creators", "sportswear_fashion": "Sportswear & Fashion",
    "betting_igaming": "Betting / iGaming", "gaming_esports": "Gaming & Esports",
    "retail_ecommerce": "Retail & E-commerce", "telecom": "Telecom & Mobile",
    "consumer_electronics": "Consumer Electronics", "fintech": "Financial / Fintech",
    "travel_hospitality": "Travel & Hospitality", "pubs_venues": "Bars, Pubs & Venues",
    "automotive": "Automotive",
}


def _migrate_columns():
    """SQLite additive migration for the live match-state columns
    (create_all does not ALTER existing tables)."""
    with engine.connect() as conn:
        cols = {r[1] for r in conn.execute(text("PRAGMA table_info(matches)"))}
        for name, ddl in (("home_score", "INTEGER DEFAULT 0"),
                          ("away_score", "INTEGER DEFAULT 0"),
                          ("clock_started_at", "VARCHAR")):
            if name not in cols:
                conn.execute(text(f"ALTER TABLE matches ADD COLUMN {name} {ddl}"))
        conn.commit()


def _reset_demo_match():
    """Fresh demo story per boot (REPLAY_RESET_ON_START, default true): wipe
    the replay match's synthetic messages/moments/campaigns/forecasts and
    reset its live state so the replay engine retells the match from zero."""
    demo = os.environ.get("DEMO_MATCH_ID", "m_001")
    with SessionLocal() as session:
        for table in ("messages", "moments", "campaigns", "content_ideas", "forecasts"):
            session.execute(text(f"DELETE FROM {table} WHERE match_id = :m"), {"m": demo})
        session.execute(text(
            "UPDATE matches SET status = 'upcoming', home_score = 0, away_score = 0, "
            "clock_started_at = NULL WHERE id = :m"), {"m": demo})
        session.commit()


async def _autostart_replay():
    """Kick the fake replay engine automatically (REPLAY_AUTOSTART, default
    true) so the app is end-to-end alive without a manual /replay/control.

    REPLAY_FILE accepts a comma-separated list so several streams replay
    CONCURRENTLY for the demo match (e.g. a YouTube capture + the simulated
    Twitter stream). Each entry may carry its own speed as "file:speed";
    entries without one use REPLAY_SPEED. Different-length recordings can be
    paced to span the same wall-clock time."""
    files = [f.strip() for f in os.environ.get(
        "REPLAY_FILE", "replay_dev_fixture.json").split(",") if f.strip()]
    default_speed = float(os.environ.get("REPLAY_SPEED", "1.0"))
    loop = os.environ.get("REPLAY_LOOP", "false").lower() == "true"
    demo = os.environ.get("DEMO_MATCH_ID", "m_001")

    for _ in range(100):  # wait for run_ingestion to publish its queue
        if ingestion_service.INGESTION_QUEUE is not None:
            for entry in files:
                name, _, spd = entry.partition(":")
                speed = float(spd) if spd else default_speed
                replay.replay_ctrl.start(demo, name, speed,
                                         ingestion_service.INGESTION_QUEUE, loop=loop)
            return
        await asyncio.sleep(0.1)


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    _migrate_columns()
    seed_db()
    if os.environ.get("REPLAY_RESET_ON_START", "true").lower() == "true":
        _reset_demo_match()
    sources = [s.strip() for s in os.environ.get("SOURCES", "replay").split(",") if s.strip()]
    asyncio.create_task(run_ingestion(SessionLocal, sources, on_moment))
    if os.environ.get("REPLAY_AUTOSTART", "true").lower() == "true":
        asyncio.create_task(_autostart_replay())


@app.get("/api/v1/health")
def health():
    db_ok = ingestion_alive = False
    try:
        with SessionLocal() as session:
            db_ok = True
            latest = session.execute(text("SELECT MAX(created_at) AS m FROM messages")).fetchone()
            if latest and latest.m:
                last = datetime.fromisoformat(latest.m.replace("Z", "+00:00"))
                ingestion_alive = datetime.now(timezone.utc) - last < timedelta(seconds=60)
    except Exception:
        pass
    return {"status": "ok" if db_ok else "degraded", "db": db_ok,
            "ingestion_alive": ingestion_alive, "version": "3.0.0"}


@app.get("/api/v1/industries")
def get_industries():
    return {"industries": [
        {"slug": ind.value,
         "display_name": DISPLAY[ind.value],
         "starred": ind.value in STARRED,
         "compliance_flag": ind.value == "betting_igaming"}
        for ind in Industry
    ]}


app.include_router(matches.router, prefix="/api/v1")
app.include_router(fans.router, prefix="/api/v1")
app.include_router(campaigns.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")
app.include_router(roi.router, prefix="/api/v1")
app.include_router(replay.router, prefix="/api/v1")
app.include_router(ui.router, prefix="/api/v1")
