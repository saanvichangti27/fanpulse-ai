"""Live match state (score / clock / status) derived from replay-engine moments.

The synthetic replay world is the source of truth for the demo match: its
markers become moments (ingestion/service.py), and every moment flows through
automation.on_moment -> apply_moment() here:

- kickoff      -> status "live", clock starts (wall-clock of the moment);
- goal         -> score increments; the scoring team is attributed to whichever
                  side's fan country dominates the live 1-minute window
                  (momentum.top_countries[0]) — celebrating fans mark the
                  scorer. When neither side's fans dominate, home is credited
                  (documented default; the replay fixture doesn't encode the
                  scorer explicitly);
- full_time    -> status "finished";
- goal/red_card/var_controversy/full_time additionally trigger a REAL model
  reforecast from live momentum, persisted to the forecasts table (this powers
  the UI's "re-forecast live when the match turns").

The match minute is wall-clock elapsed since kickoff scaled by
REPLAY_TIME_SCALE: the dev fixture compresses a 90' match into ~800s, so one
real second ≈ 6.75 match seconds by default.
"""
import os
import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..contracts import MomentEvent
from .models_db import Match, Forecast as DBForecast
from .ui_meta import TEAM_REF

logger = logging.getLogger(__name__)

# 90 match-minutes / (800 s fixture / 60) ≈ 6.75 match-seconds per real second
REPLAY_TIME_SCALE = float(os.getenv("REPLAY_TIME_SCALE", "6.75"))

_REFORECAST_TAGS = {"goal", "red_card", "var_controversy", "full_time"}


def current_minute(match: Match) -> int:
    """Scaled match minute for a live/finished match; 0 before kickoff."""
    if match.status == "finished":
        return 90
    if match.status != "live" or not match.clock_started_at:
        return 0
    started = datetime.fromisoformat(match.clock_started_at.replace("Z", "+00:00"))
    elapsed_s = (datetime.now(timezone.utc) - started).total_seconds()
    return int(min(90, max(0, elapsed_s * REPLAY_TIME_SCALE / 60.0)))


def _attribute_goal(match: Match, momentum) -> str:
    top_countries = list(getattr(momentum, "top_countries", None) or [])
    home_fans = TEAM_REF.get(match.home_team, {}).get("fan_country")
    away_fans = TEAM_REF.get(match.away_team, {}).get("fan_country")
    for c in top_countries:
        if c == home_fans:
            return "home"
        if c == away_fans:
            return "away"
    return "home"


def apply_moment(db: Session, moment: MomentEvent) -> None:
    match = db.query(Match).filter(Match.id == moment.match_id).first()
    if not match:
        return

    tag = moment.event_tag.value if hasattr(moment.event_tag, "value") else moment.event_tag

    if tag == "kickoff":
        match.status = "live"
        match.clock_started_at = (moment.detected_at.isoformat().replace("+00:00", "Z")
                                  if hasattr(moment.detected_at, "isoformat")
                                  else str(moment.detected_at))
        match.home_score = match.home_score or 0
        match.away_score = match.away_score or 0
    elif tag == "goal":
        side = _attribute_goal(match, moment.momentum)
        if side == "home":
            match.home_score = (match.home_score or 0) + 1
        else:
            match.away_score = (match.away_score or 0) + 1
        logger.info(f"Goal attributed to {side} — {match.home_team} "
                    f"{match.home_score}-{match.away_score} {match.away_team}")
    elif tag == "full_time":
        match.status = "finished"

    db.commit()

    if tag in _REFORECAST_TAGS:
        _reforecast(db, match, moment)


def _reforecast(db: Session, match: Match, moment: MomentEvent) -> None:
    """Persist a real momentum-driven reforecast (same path as the manual
    /forecast/reforecast endpoint)."""
    try:
        from ..intelligence import forecast
        from .routers.matches import match_features

        momentum = moment.momentum.model_dump(mode="json") \
            if hasattr(moment.momentum, "model_dump") else dict(moment.momentum)
        res = forecast.predict_audience(match_features(match), momentum=momentum)

        payload = {
            "match_id": match.id,
            "demand_index": res["demand_index"],
            "predicted_attendance_pct": res["predicted_pct"],
            "sellout_probability": res["sellout_probability"],
            "feature_importance": res["feature_importances"],
            "is_reforecast": True,
            "baseline_demand_index": res.get("baseline_demand_index"),
            "delta_vs_baseline_pct": res.get("delta_vs_baseline_pct"),
            "trigger_description": (f"recomputed after {moment.event_tag.value if hasattr(moment.event_tag, 'value') else moment.event_tag} "
                                    f"moment {moment.moment_id} — {res.get('trigger_description')}"),
            "model_mae": res["model_mae"],
            "computed_at": res["computed_at"],
        }
        db.add(DBForecast(
            match_id=match.id, is_reforecast=1,
            forecast_json=json.dumps(payload),
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        ))
        db.commit()
        logger.info(f"Auto-reforecast for {match.id} on {moment.moment_id}: "
                    f"demand {res['demand_index']} (Δ {res.get('delta_vs_baseline_pct')}%)")
    except Exception as e:
        logger.error(f"Auto-reforecast failed for {match.id}: {e}")
