import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..models_db import Match as DBMatch
from ...contracts import (
    MatchListResponse, Match, KpiSnapshot, Emotion, TimelineResponse,
    TimelinePoint, HeatmapPayload, TopicsResponse, TopicItem, FeedResponse,
    ClassifiedMessage, MomentsResponse, MomentEvent,
)
from ...ingestion import analytics
from ...intelligence import forecast

logger = logging.getLogger(__name__)
router = APIRouter()


def match_features(m: DBMatch) -> dict:
    dt = datetime.fromisoformat(m.kickoff_time.replace("Z", "+00:00"))
    return {
        "stage": m.stage,
        "rank_gap": abs((m.home_rank or 50) - (m.away_rank or 50)),
        "host_involved": m.host_involved or 0,
        "rivalry_flag": m.rivalry_flag or 0,
        "venue_capacity": m.venue_capacity,
        "home_rank": m.home_rank or 50,
        "away_rank": m.away_rank or 50,
        "city_population_m": m.city_population_m or 1.0,
        "day_of_week": dt.weekday(),
        "kickoff_hour_local": dt.hour,
    }


def _to_match(m: DBMatch) -> Match:
    # Real model prediction per match — never a hardcoded demand figure.
    demand_index = sellout = None
    try:
        res = forecast.predict_audience(match_features(m))
        demand_index = res["demand_index"]
        sellout = res["sellout_probability"]
    except Exception as e:
        logger.warning(f"Forecast unavailable for {m.id}: {e}")
    return Match(
        match_id=m.id, home_team=m.home_team, away_team=m.away_team,
        kickoff_time=m.kickoff_time, stage=m.stage, venue_capacity=m.venue_capacity,
        city=m.city, status=m.status,
        demand_index=demand_index, sellout_probability=sellout,
    )


@router.get("/matches", response_model=MatchListResponse)
def list_matches(db: Session = Depends(get_db)):
    return MatchListResponse(matches=[_to_match(m) for m in db.query(DBMatch).all()])


@router.get("/matches/{match_id}", response_model=Match)
def get_match(match_id: str, db: Session = Depends(get_db)):
    m = db.query(DBMatch).filter(DBMatch.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    return _to_match(m)


@router.get("/matches/{match_id}/kpis", response_model=KpiSnapshot)
def get_kpis(match_id: str, db: Session = Depends(get_db)):
    res = analytics.get_kpis(db, match_id)
    if not res:  # no messages yet — honest zeros with a real timestamp
        return KpiSnapshot(
            match_id=match_id, total_mentions=0, positive_pct=0, negative_pct=0,
            neutral_pct=0, top_emotion=Emotion.neutral, excitement_score=0,
            most_active_region="Unknown", mentions_per_min=0,
            computed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
    return KpiSnapshot(**res)


@router.get("/matches/{match_id}/sentiment-timeline", response_model=TimelineResponse)
def get_timeline(match_id: str, db: Session = Depends(get_db)):
    pts = analytics.get_timeline(db, match_id)
    return TimelineResponse(match_id=match_id, points=[TimelinePoint(**p) for p in pts])


@router.get("/matches/{match_id}/heatmap", response_model=HeatmapPayload)
def get_heatmap(match_id: str, db: Session = Depends(get_db)):
    res = analytics.get_heatmap(db, match_id)
    if not res:
        return HeatmapPayload(
            match_id=match_id,
            computed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            countries=[],
        )
    return HeatmapPayload(**res)


@router.get("/matches/{match_id}/topics", response_model=TopicsResponse)
def get_topics(match_id: str, db: Session = Depends(get_db)):
    return TopicsResponse(topics=[TopicItem(**t) for t in analytics.get_topics(db, match_id)])


@router.get("/matches/{match_id}/feed", response_model=FeedResponse)
def get_feed(match_id: str, limit: int = 50, db: Session = Depends(get_db)):
    limit = min(limit, 200)
    rows = db.execute(text(
        "SELECT * FROM messages WHERE match_id = :match_id ORDER BY id DESC LIMIT :lim"
    ), {"match_id": match_id, "lim": limit}).fetchall()
    messages = [
        ClassifiedMessage(
            message_id=r.id, match_id=r.match_id, source=r.source, text=r.text,
            author=r.author, country=r.country,
            sentiment=r.sentiment, sentiment_score=r.sentiment_score,
            emotion=r.emotion, emotion_score=r.emotion_score,
            topics=json.loads(r.topics_json), created_at=r.created_at,
        ) for r in rows
    ]
    return FeedResponse(messages=messages)


@router.get("/matches/{match_id}/moments", response_model=MomentsResponse)
def get_moments(match_id: str, db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT * FROM moments WHERE match_id = :match_id ORDER BY detected_at DESC LIMIT 20"
    ), {"match_id": match_id}).fetchall()
    moments = [
        MomentEvent(
            moment_id=r.id, match_id=r.match_id, event_tag=r.event_tag,
            detected_at=r.detected_at, momentum=json.loads(r.momentum_json),
            description=r.description or "",
        ) for r in rows
    ]
    return MomentsResponse(moments=moments)
