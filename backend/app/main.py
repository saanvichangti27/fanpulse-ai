from fastapi import FastAPI
import os
import asyncio
from .routers import matches, fans, campaigns, predictions, roi, replay
from .seed import seed_db
from .db import engine, SessionLocal
from .models_db import Base
from .automation import on_moment
from ..ingestion.service import run_ingestion
from dotenv import load_dotenv
load_dotenv("backend/.env")

app = FastAPI(title="FanPulse AI API", version="3.0.0")

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    seed_db()
    # Start ingestion loop
    sources = os.environ.get("SOURCES", "replay").split(",")
    asyncio.create_task(run_ingestion(SessionLocal, sources, on_moment))

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "db": True, "ingestion_alive": True, "version": "3.0.0"}

@app.get("/api/v1/industries")
def get_industries():
    return {"industries": [
        {"slug": "food_delivery", "display_name": "Food Delivery", "starred": True, "compliance_flag": False},
        {"slug": "merch_apparel", "display_name": "Merch & Apparel", "starred": True, "compliance_flag": False},
        {"slug": "beverages", "display_name": "Beverages", "starred": True, "compliance_flag": False},
        {"slug": "streaming_ott", "display_name": "Streaming OTT", "starred": True, "compliance_flag": False},
        {"slug": "content_creator", "display_name": "Content Creator", "starred": True, "compliance_flag": False}
    ]}

app.include_router(matches.router, prefix="/api/v1")
app.include_router(fans.router, prefix="/api/v1")
app.include_router(campaigns.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")
app.include_router(roi.router, prefix="/api/v1")
app.include_router(replay.router, prefix="/api/v1")
