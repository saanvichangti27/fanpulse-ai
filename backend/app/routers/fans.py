from fastapi import APIRouter
from ...contracts import SegmentReport
from ...intelligence import segments

router = APIRouter()

@router.get("/fans/segments", response_model=SegmentReport)
def get_segments(match_id: str = None):
    # W3 real ML segment profiles
    return segments.get_segments()

@router.get("/fans/next-best-actions")
def get_nba(industry: str = None):
    # W3 real Next Best Action matrix
    return {"actions": segments.get_next_best_actions(industry)}
