from typing import List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...contracts import ROIResult, MediaPlan, Industry, Channel, BenchmarkNotFound
from ...intelligence import roi as roi_engine
from ...intelligence import forecast
from ...ingestion import analytics
from ..db import get_db
from ..models_db import Match
from .matches import match_features

router = APIRouter()


class SimulateROIRequest(BaseModel):
    match_id: str
    industry: Industry
    channel: Channel
    budget_usd: float
    timing: str = "now"  # "now" (live momentum) | "baseline" (M = 1)


class MediaPlanRequest(BaseModel):
    budget_usd: float
    industry: Industry
    match_ids: List[str]


@router.post("/roi/simulate", response_model=ROIResult)
def simulate_roi(req: SimulateROIRequest, db: Session = Depends(get_db)):
    # timing="now" uses the REAL live momentum measured from ingested messages;
    # when there is no live signal it degrades honestly to baseline (M = 1).
    momentum = analytics.get_momentum(db, req.match_id) if req.timing == "now" else None
    try:
        return ROIResult(**roi_engine.simulate_roi(
            industry=req.industry.value,
            channel=req.channel.value,
            budget_usd=req.budget_usd,
            momentum=momentum,
        ))
    except BenchmarkNotFound as e:
        raise HTTPException(status_code=400, detail=f"VALIDATION_ERROR: {e}")


@router.post("/roi/media-plan", response_model=MediaPlan)
def generate_media_plan(req: MediaPlanRequest, db: Session = Depends(get_db)):
    forecasts, momenta = [], {}
    for mid in req.match_ids:
        match = db.query(Match).filter(Match.id == mid).first()
        if not match:
            raise HTTPException(status_code=404, detail=f"Match not found: {mid}")
        res = forecast.predict_audience(match_features(match))  # real model, per match
        forecasts.append({"match_id": mid, "demand_index": res["demand_index"]})
        momenta[mid] = analytics.get_momentum(db, mid)  # None when quiet
    try:
        return MediaPlan(**roi_engine.plan_media(
            budget_usd=req.budget_usd, industry=req.industry.value,
            forecasts=forecasts, momenta=momenta,
        ))
    except BenchmarkNotFound as e:
        raise HTTPException(status_code=400, detail=f"VALIDATION_ERROR: {e}")
