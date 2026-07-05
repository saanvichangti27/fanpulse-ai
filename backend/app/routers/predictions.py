from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from ...contracts import AudienceForecast
from ..models_db import Match
from ..db import get_db
from ...intelligence import forecast

router = APIRouter()

class ReforecastRequest(BaseModel):
    match_id: str
    momentum: float = None

def get_match_features(match: Match) -> dict:
    dt = datetime.fromisoformat(match.kickoff_time.replace("Z", "+00:00"))
    return {
        'stage': match.stage,
        'rank_gap': abs((match.home_rank or 0) - (match.away_rank or 0)),
        'host_involved': match.host_involved,
        'rivalry_flag': match.rivalry_flag,
        'venue_capacity': match.venue_capacity,
        'home_rank': match.home_rank or 0,
        'away_rank': match.away_rank or 0,
        'city_population_m': match.city_population_m or 1.0,
        'day_of_week': dt.weekday(),
        'kickoff_hour_local': dt.hour
    }

@router.get("/matches/{match_id}/forecast", response_model=AudienceForecast)
def get_forecast(match_id: str, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    features = get_match_features(match)
    # W3 real ML prediction
    res = forecast.predict_audience(features)
    
    return AudienceForecast(
        match_id=match_id,
        demand_index=res["demand_index"],
        predicted_attendance_pct=res["predicted_pct"],
        sellout_probability=res["sellout_probability"],
        feature_importance=res["feature_importances"],
        is_reforecast=res["is_reforecast"],
        model_mae=res["model_mae"],
        computed_at=datetime.utcnow().isoformat() + "Z"
    )

@router.post("/forecast/reforecast", response_model=AudienceForecast)
def reforecast(req: ReforecastRequest, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == req.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    features = get_match_features(match)
    # W3 real ML prediction with momentum delta
    res = forecast.predict_audience(features, momentum=req.momentum)
    
    return AudienceForecast(
        match_id=req.match_id,
        demand_index=res["demand_index"],
        predicted_attendance_pct=res["predicted_pct"],
        sellout_probability=res["sellout_probability"],
        feature_importance=res["feature_importances"],
        is_reforecast=res["is_reforecast"],
        baseline_demand_index=res.get("baseline_demand_index"),
        delta_vs_baseline_pct=res.get("delta_vs_baseline_pct"),
        trigger_description=res.get("trigger_description"),
        model_mae=res["model_mae"],
        computed_at=datetime.utcnow().isoformat() + "Z"
    )
