import os
import asyncio
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from sqlalchemy import text
from dotenv import load_dotenv

# Load backend/.env regardless of the current working directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from .routers import matches, fans, campaigns, predictions, roi, replay
from .seed import seed_db
from .db import engine, SessionLocal
from .models_db import Base
from .automation import on_moment
from ..ingestion.service import run_ingestion
<<<<<<< HEAD
from ..contracts import Industry
=======
from ..ingestion.nlp import get_sentiment_pipeline, get_emotion_pipeline
from dotenv import load_dotenv
load_dotenv()
>>>>>>> 5e3cf5d6ad24a48fc2c67b1e4005162bbf9db5bb

app = FastAPI(title="FanPulse AI API", version="3.0.0")

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


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    seed_db()
<<<<<<< HEAD
    sources = [s.strip() for s in os.environ.get("SOURCES", "replay").split(",") if s.strip()]
=======
    
    # Preload NLP models so they don't block the first ingestion batch
    print("Preloading NLP models...")
    get_sentiment_pipeline()
    get_emotion_pipeline()
    print("NLP models loaded.")
    
    # Start ingestion loop
    sources = os.environ.get("SOURCES", "replay").split(",")
>>>>>>> 5e3cf5d6ad24a48fc2c67b1e4005162bbf9db5bb
    asyncio.create_task(run_ingestion(SessionLocal, sources, on_moment))


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
