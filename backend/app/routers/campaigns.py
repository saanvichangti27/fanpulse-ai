import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...contracts import (
    CampaignsResponse, CampaignCard, ContentIdeaCard, Industry, SegmentId,
    Channel, MomentEvent, BenchmarkNotFound,
)
from ..strategy.engine import generate_campaign_brief, build_evidence
from ..gemini_client import generate_copy, generate_content_idea
from ..db import get_db
from ..models_db import Campaign as DBCampaign, ContentIdea as DBContentIdea
from ...ingestion import analytics
from ...intelligence import segments as segments_engine

logger = logging.getLogger(__name__)
router = APIRouter()


class GenerateCampaignRequest(BaseModel):
    match_id: str
    industry: Industry
    target_segment: Optional[SegmentId] = None
    channel: Optional[Channel] = None
    trigger: str = "manual"
    moment_id: Optional[str] = None
    budget_usd: float = 100000.0


class GenerateContentRequest(BaseModel):
    match_id: str
    platform: str = "instagram"
    creator_niche: Optional[str] = "football_reactions"


def _load_moment(db: Session, match_id: str, moment_id: Optional[str]) -> Optional[MomentEvent]:
    """Explicit moment if given; otherwise the latest moment from the last 30
    minutes so a manual generate during a hot window uses the live context."""
    if moment_id:
        row = db.execute(text("SELECT * FROM moments WHERE id = :id"), {"id": moment_id}).fetchone()
    else:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat().replace("+00:00", "Z")
        row = db.execute(text(
            "SELECT * FROM moments WHERE match_id = :m AND detected_at >= :c "
            "ORDER BY detected_at DESC LIMIT 1"
        ), {"m": match_id, "c": cutoff}).fetchone()
    if not row:
        return None
    return MomentEvent(
        moment_id=row.id, match_id=row.match_id, event_tag=row.event_tag,
        detected_at=row.detected_at, momentum=json.loads(row.momentum_json),
        description=row.description or "",
    )


def build_campaign_card(db: Session, match_id: str, industry: Industry,
                        budget_usd: float, trigger: str,
                        moment: Optional[MomentEvent] = None,
                        requested_segment: Optional[SegmentId] = None,
                        requested_channel: Optional[Channel] = None) -> CampaignCard:
    """Shared by the manual endpoint and the auto-moment path (automation.py)."""
    # Live segment-activity overlay from real country volumes
    volumes = analytics.get_country_volumes(db, match_id)
    overlay = segments_engine.get_active_overlay(volumes) if volumes else None

    brief = generate_campaign_brief(
        match_id=match_id, industry=industry, budget_usd=budget_usd,
        moment=moment, requested_segment=requested_segment,
        requested_channel=requested_channel, activity_overlay=overlay,
    )
    copy, llm_fallback = generate_copy(brief)

    now = datetime.now(timezone.utc)
    now_s = now.isoformat().replace("+00:00", "Z")
    window_end = (now + timedelta(minutes=brief.window_minutes)).isoformat().replace("+00:00", "Z")

    card = CampaignCard(
        campaign_id=f"cmp_{uuid.uuid4().hex[:8]}",
        match_id=match_id,
        industry=brief.industry,
        target_segment=brief.target_segment,
        channel=brief.channel,
        archetype=brief.archetype,
        window_minutes=brief.window_minutes,
        window_ends_at=window_end,
        status="draft",
        trigger=trigger,
        moment_id=moment.moment_id if moment else None,
        copy=copy,
        roi=brief.roi,
        evidence=build_evidence(brief),
        confidence=brief.roi.confidence,  # contract §F.3 data-support score
        llm_fallback=llm_fallback,
        created_at=now_s,
    )

    db.add(DBCampaign(
        id=card.campaign_id, match_id=card.match_id, industry=card.industry.value,
        archetype=card.archetype.value, target_segment=card.target_segment.value,
        channel=card.channel.value, trigger=card.trigger, moment_id=card.moment_id,
        window_minutes=card.window_minutes,
        copy_json=card.copy_content.model_dump_json(),
        roi_json=card.roi.model_dump_json(),
        evidence_json=json.dumps(card.evidence),
        confidence=card.confidence, llm_fallback=1 if card.llm_fallback else 0,
        created_at=card.created_at,
    ))
    db.commit()
    return card


@router.post("/campaigns/generate", response_model=CampaignCard)
def generate_campaign(req: GenerateCampaignRequest, db: Session = Depends(get_db)):
    try:
        moment = _load_moment(db, req.match_id, req.moment_id)
        return build_campaign_card(
            db, req.match_id, req.industry, req.budget_usd, req.trigger,
            moment=moment, requested_segment=req.target_segment,
            requested_channel=req.channel,
        )
    except BenchmarkNotFound as e:
        raise HTTPException(status_code=400, detail=f"VALIDATION_ERROR: {e}")


@router.get("/matches/{match_id}/campaigns", response_model=CampaignsResponse)
def get_campaigns(match_id: str, db: Session = Depends(get_db)):
    rows = (db.query(DBCampaign).filter(DBCampaign.match_id == match_id)
            .order_by(DBCampaign.created_at.desc()).all())
    cards = []
    for c in rows:
        end = (datetime.fromisoformat(c.created_at.replace("Z", "+00:00"))
               + timedelta(minutes=c.window_minutes or 0)).isoformat().replace("+00:00", "Z")
        cards.append(CampaignCard(
            campaign_id=c.id, match_id=c.match_id, industry=c.industry,
            archetype=c.archetype, target_segment=c.target_segment, channel=c.channel,
            window_minutes=c.window_minutes, window_ends_at=end, status="draft",
            trigger=c.trigger, moment_id=c.moment_id,
            copy=json.loads(c.copy_json), roi=json.loads(c.roi_json),
            evidence=json.loads(c.evidence_json), confidence=c.confidence,
            llm_fallback=bool(c.llm_fallback), created_at=c.created_at,
        ))
    return CampaignsResponse(campaigns=cards)


@router.post("/content/generate", response_model=ContentIdeaCard)
def generate_content(req: GenerateContentRequest, db: Session = Depends(get_db)):
    if req.platform not in ("instagram", "youtube"):
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR: platform must be instagram or youtube")

    # Real live context: trending topics + momentum from ingested messages
    topics = [t["label"] for t in analytics.get_topics(db, req.match_id)][:5]
    momentum = analytics.get_momentum(db, req.match_id)
    emotion = momentum["dominant_emotion"] if momentum else "neutral"
    countries = momentum["top_countries"] if momentum else []

    idea, llm_fallback = generate_content_idea(
        req.match_id, req.platform, req.creator_niche or "football_reactions",
        topics, emotion, countries,
    )

    # Data-support confidence (same shape as contract §F.3; recency/segment
    # terms are 1.0 because content ideas need neither a moment nor a segment)
    if momentum:
        confidence = round(min(1.0, 0.4 * min(momentum["volume_5m"] / 500.0, 1.0) + 0.6), 2)
    else:
        confidence = 0.75

    now_s = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    evidence = {
        "trending": (f"'{topics[0]}' leads live topics" if topics else "no live topics yet"),
        "emotion": f"dominant live emotion: {emotion}",
        "regional": f"peak audiences {', '.join(countries)}" if countries else "no regional signal",
        "timing": "engagement windows decay ~20 min post-moment",
    }
    card = ContentIdeaCard(
        content_id=f"ci_{uuid.uuid4().hex[:8]}", match_id=req.match_id,
        platform=req.platform, archetype="content_idea", idea=idea,
        evidence=evidence, confidence=confidence, llm_fallback=llm_fallback,
        created_at=now_s,
    )
    db.add(DBContentIdea(
        id=card.content_id, match_id=card.match_id, platform=card.platform,
        idea_json=card.idea.model_dump_json(), evidence_json=json.dumps(evidence),
        confidence=confidence, llm_fallback=1 if llm_fallback else 0, created_at=now_s,
    ))
    db.commit()
    return card
