from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...contracts import SegmentReport, NextBestAction
from ...intelligence import segments
from ...ingestion import analytics
from ..db import get_db

router = APIRouter()


@router.get("/fans/segments", response_model=SegmentReport)
def get_segments(match_id: Optional[str] = None, db: Session = Depends(get_db)):
    report = segments.get_segments()
    if match_id:
        # Live overlay: which segments are loudest right now, from the real
        # country-volume distribution of ingested messages (contract §B.9).
        volumes = analytics.get_country_volumes(db, match_id)
        if volumes:
            overlay = segments.get_active_overlay(volumes)
            for seg in report["segments"]:
                seg["activity_share_pct"] = round(overlay.get(seg["segment_id"], 0.0), 1)
    return report


@router.get("/fans/next-best-actions")
def get_nba(industry: Optional[str] = None):
    actions = segments.get_next_best_actions(industry)
    return {"actions": [NextBestAction(**a).model_dump() for a in actions]}
