import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...contracts import AudienceForecast
from ..models_db import Match, Forecast as DBForecast
from ..db import get_db
from ...intelligence import forecast
from ...ingestion import analytics
from .matches import match_features

router = APIRouter()


class ReforecastRequest(BaseModel):
    match_id: str


def _build(match_id: str, res: dict) -> AudienceForecast:
    return AudienceForecast(
        match_id=match_id,
        demand_index=res["demand_index"],
        predicted_attendance_pct=res["predicted_pct"],
        sellout_probability=res["sellout_probability"],
        feature_importance=res["feature_importances"],
        is_reforecast=res["is_reforecast"],
        baseline_demand_index=res.get("baseline_demand_index"),
        delta_vs_baseline_pct=res.get("delta_vs_baseline_pct"),
        trigger_description=res.get("trigger_description"),
        model_mae=res["model_mae"],
        computed_at=res["computed_at"],
    )


@router.get("/matches/{match_id}/forecast", response_model=AudienceForecast)
def get_forecast(match_id: str, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Latest persisted reforecast wins (contract §B.6); else compute baseline.
    latest = (db.query(DBForecast)
              .filter(DBForecast.match_id == match_id, DBForecast.is_reforecast == 1)
              .order_by(DBForecast.id.desc()).first())
    if latest:
        return AudienceForecast(**json.loads(latest.forecast_json))

    return _build(match_id, forecast.predict_audience(match_features(match)))


@router.post("/forecast/reforecast", response_model=AudienceForecast)
def reforecast(req: ReforecastRequest, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == req.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # LIVE momentum measured from real ingested messages — not client-supplied.
    momentum = analytics.get_momentum(db, req.match_id)
    if momentum is None:
        raise HTTPException(
            status_code=409,
            detail="INSUFFICIENT_DATA: no live momentum for this match "
                   "(fewer than 10 messages in the last 5 minutes)",
        )

    res = forecast.predict_audience(match_features(match), momentum=momentum)
    card = _build(req.match_id, res)

    db.add(DBForecast(
        match_id=req.match_id, is_reforecast=1,
        forecast_json=card.model_dump_json(),
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    ))
    db.commit()
    return card
