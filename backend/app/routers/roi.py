from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from ...contracts import ROIResult, MediaPlan, Industry, Channel
from ..stubs_intelligence import get_roi_stub

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
    return get_roi_stub(req.industry, req.channel, req.budget_usd)

@router.post("/roi/media-plan", response_model=MediaPlan)
def generate_media_plan(req: MediaPlanRequest):
    # returning empty for now
    return MediaPlan(
        total_budget_usd=req.budget_usd,
        industry=req.industry,
        allocations=[],
        expected_total_roas=0.0
    )
