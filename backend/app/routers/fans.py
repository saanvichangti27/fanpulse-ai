from fastapi import APIRouter
from ...contracts import SegmentReport
from ..stubs_intelligence import get_segments_stub

router = APIRouter()

@router.get("/fans/segments", response_model=SegmentReport)
def get_segments(match_id: str = None):
    return get_segments_stub()

@router.get("/fans/next-best-actions")
def get_nba(industry: str = None):
    return {"actions": []}
