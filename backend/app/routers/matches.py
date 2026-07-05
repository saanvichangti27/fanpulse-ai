from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models_db import Match as DBMatch
from ...contracts import MatchListResponse, Match, KpiSnapshot, Emotion, TimelineResponse, TimelinePoint, HeatmapPayload, CountryHeatmap, TopicsResponse, TopicItem, FeedResponse, MomentsResponse

router = APIRouter()

@router.get("/matches", response_model=MatchListResponse)
def list_matches(db: Session = Depends(get_db)):
    db_matches = db.query(DBMatch).all()
    matches = [
        Match(
            match_id=m.id, home_team=m.home_team, away_team=m.away_team, 
            kickoff_time=m.kickoff_time, stage=m.stage, venue_capacity=m.venue_capacity, 
            city=m.city, status=m.status, demand_index=87.4, sellout_probability=0.91
        ) for m in db_matches
    ]
    return MatchListResponse(matches=matches)

@router.get("/matches/{match_id}", response_model=Match)
def get_match(match_id: str, db: Session = Depends(get_db)):
    m = db.query(DBMatch).filter(DBMatch.id == match_id).first()
    return Match(
        match_id=m.id, home_team=m.home_team, away_team=m.away_team, 
        kickoff_time=m.kickoff_time, stage=m.stage, venue_capacity=m.venue_capacity, 
        city=m.city, status=m.status, demand_index=87.4, sellout_probability=0.91
    )

@router.get("/matches/{match_id}/kpis", response_model=KpiSnapshot)
def get_kpis(match_id: str):
    # Stub for W1 analytics
    return KpiSnapshot(
        match_id=match_id, total_mentions=48213, positive_pct=71.4, negative_pct=9.8, neutral_pct=18.8,
        top_emotion=Emotion.joy, excitement_score=92.0, most_active_region="BR", mentions_per_min=1240, computed_at="2026-07-05T12:00:00Z"
    )

@router.get("/matches/{match_id}/sentiment-timeline", response_model=TimelineResponse)
def get_timeline(match_id: str):
    return TimelineResponse(
        match_id=match_id,
        points=[
            TimelinePoint(ts="2026-07-05T12:00:00Z", positive_pct=65.0, negative_pct=12.0, neutral_pct=23.0, mentions=1200, top_emotion=Emotion.joy, event_tag=None)
        ]
    )

@router.get("/matches/{match_id}/heatmap", response_model=HeatmapPayload)
def get_heatmap(match_id: str):
    return HeatmapPayload(
        match_id=match_id, computed_at="2026-07-05T12:00:00Z",
        countries=[CountryHeatmap(country_code="BR", avg_sentiment=0.94, dominant_emotion=Emotion.joy, mentions=12000)]
    )

@router.get("/matches/{match_id}/topics", response_model=TopicsResponse)
def get_topics(match_id: str):
    return TopicsResponse(topics=[TopicItem(label="messi", mentions=8210, trend="up")])

@router.get("/matches/{match_id}/feed", response_model=FeedResponse)
def get_feed(match_id: str):
    return FeedResponse(messages=[])

@router.get("/matches/{match_id}/moments", response_model=MomentsResponse)
def get_moments(match_id: str):
    return MomentsResponse(moments=[])
