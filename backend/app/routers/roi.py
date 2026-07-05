from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from ...contracts import ROIResult, MediaPlan, Industry, Channel
from ...intelligence import roi as roi_engine

router = APIRouter()

class SimulateROIRequest(BaseModel):
    match_id: str
    industry: Industry
    channel: Channel
    budget_usd: float
    timing: str = "now"

class MediaPlanRequest(BaseModel):
    budget_usd: float
    industry: Industry
    match_ids: List[str]

@router.post("/roi/simulate", response_model=ROIResult)
def simulate_roi(req: SimulateROIRequest):
    roi_dict = roi_engine.simulate_roi(
        industry=req.industry.value,
        channel=req.channel.value,
        budget_usd=req.budget_usd,
        is_baseline=True
    )
    return ROIResult(**roi_dict)

@router.post("/roi/media-plan", response_model=MediaPlan)
def generate_media_plan(req: MediaPlanRequest):
    forecasts = [{"match_id": m, "demand_index": 50.0} for m in req.match_ids]
    plan_dict = roi_engine.plan_media(
        budget_usd=req.budget_usd,
        industry=req.industry.value,
        forecasts=forecasts
    )
    return MediaPlan(**plan_dict)
