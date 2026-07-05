from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone

from ...contracts import CampaignsResponse, CampaignCard, ContentIdeaCard, Industry, SegmentId, Channel, Source
from ..strategy.engine import generate_campaign_brief
from ..gemini_client import generate_copy
from ..db import get_db
from ..models_db import Campaign as DBCampaign

router = APIRouter()

class GenerateCampaignRequest(BaseModel):
    match_id: str
    industry: str
    target_segment: Optional[str] = None
    channel: Optional[str] = None
    trigger: str = "manual"
    moment_id: Optional[str] = None
    budget_usd: float

class GenerateContentRequest(BaseModel):
    match_id: str
    platform: str
    creator_niche: Optional[str] = None

@router.post("/campaigns/generate", response_model=CampaignCard)
def generate_campaign(req: GenerateCampaignRequest, db: Session = Depends(get_db)):
    try:
        industry = Industry(req.industry)
        segment = SegmentId(req.target_segment) if req.target_segment else None
        channel = Channel(req.channel) if req.channel else None
        
        brief = generate_campaign_brief(
            match_id=req.match_id,
            industry=industry,
            budget_usd=req.budget_usd,
            requested_segment=segment,
            requested_channel=channel
        )
        
        copy, llm_fallback = generate_copy(brief)
        
        now = datetime.now(timezone.utc).isoformat()
        card = CampaignCard(
            campaign_id=f"cmp_{uuid.uuid4().hex[:8]}",
            match_id=req.match_id,
            industry=brief.industry,
            target_segment=brief.target_segment,
            channel=brief.channel,
            archetype=brief.archetype,
            window_minutes=brief.window_minutes,
            window_ends_at=now, # Demo simplified
            status="draft",
            trigger=req.trigger,
            moment_id=req.moment_id,
            copy=copy,
            roi=brief.roi,
            evidence={
                "emotion": brief.emotion.value,
                "top_topics": brief.top_topics,
                "top_countries": brief.top_countries,
                "segment_traits": brief.segment.defining_traits
            },
            confidence=0.88 if not llm_fallback else 0.5,
            llm_fallback=llm_fallback,
            created_at=now
        )
        
        import json
        db_camp = DBCampaign(
            id=card.campaign_id,
            match_id=card.match_id,
            industry=card.industry.value,
            archetype=card.archetype.value,
            target_segment=card.target_segment.value,
            channel=card.channel.value,
            trigger=card.trigger,
            moment_id=card.moment_id,
            window_minutes=card.window_minutes,
            copy_json=card.copy_content.model_dump_json(),
            roi_json=card.roi.model_dump_json(),
            evidence_json=json.dumps(card.evidence),
            confidence=card.confidence,
            llm_fallback=1 if card.llm_fallback else 0,
            created_at=card.created_at
        )
        db.add(db_camp)
        db.commit()
        return card
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/matches/{match_id}/campaigns", response_model=CampaignsResponse)
def get_campaigns(match_id: str, db: Session = Depends(get_db)):
    db_camps = db.query(DBCampaign).filter(DBCampaign.match_id == match_id).all()
    import json
    cards = []
    for c in db_camps:
        cards.append(CampaignCard(
            campaign_id=c.id,
            match_id=c.match_id,
            industry=c.industry,
            archetype=c.archetype,
            target_segment=c.target_segment,
            channel=c.channel,
            window_minutes=c.window_minutes,
            window_ends_at=c.created_at,
            status="draft",
            trigger=c.trigger,
            moment_id=c.moment_id,
            copy=json.loads(c.copy_json),
            roi=json.loads(c.roi_json),
            evidence=json.loads(c.evidence_json),
            confidence=c.confidence,
            llm_fallback=bool(c.llm_fallback),
            created_at=c.created_at
        ))
    return CampaignsResponse(campaigns=cards)

@router.post("/content/generate", response_model=ContentIdeaCard)
def generate_content(req: GenerateContentRequest):
    raise NotImplementedError("Content generation not fully implemented yet")
