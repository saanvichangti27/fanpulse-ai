"""BFF endpoint for the locked emergent-ui frontend.

GET /api/v1/ui/bootstrap returns EVERY dataset the frontend renders, in the
exact export shapes of frontend/src/data/mock.js (the UI's single data
module). The integration layer (integration/live-data.js) fetches this once
per page load and re-exports it under the same names — no frontend file is
modified.

Every value is computed from the real engines:
  ingestion/analytics  -> KPIs, heatmap, timeline, topics, momentum
  intelligence/segments-> KMeans fan segments
  intelligence/forecast-> demand index / sellout (GBR model)
  strategy + roi + gemini -> campaign strategy cards (real funnel math)
  match_state          -> scores / clock / status from replay moments
Static lookup tables (names, flags, coords, labels) live in app/ui_meta.py.
"""
import os
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models_db import Match as DBMatch, Campaign as DBCampaign, Forecast as DBForecast
from ..ui_meta import (
    BRAND, NAV_LINKS, FEATURES, SEGMENT_COLORS, INDUSTRY_TO_UI, EVENT_TAG_UI,
    ARCHETYPE_DISPLAY, STAGE_LABELS, COUNTRY_REF, TEAM_REF, DRIVER_LABELS,
)
from .. import match_state
from ..gemini_client import generate_copy  # noqa: F401  (via build_campaign_card)
from ...contracts import Industry
from ...ingestion import analytics
from ...intelligence import segments as segments_engine
from ...intelligence import forecast as forecast_engine
from .matches import match_features

logger = logging.getLogger(__name__)
router = APIRouter()

DEMO_MATCH_ID = os.getenv("DEMO_MATCH_ID", "m_001")
BOOTSTRAP_BASELINE_BUDGET = float(os.getenv("AUTO_CAMPAIGN_BUDGET_USD", "100000"))
STARRED = ["food_delivery", "merch_apparel", "beverages", "streaming_ott", "content_creator"]


# --------------------------------------------------------------- segments
def _fan_segments() -> list[dict]:
    report = segments_engine.get_segments()
    out = []
    for s in report["segments"]:
        out.append({
            "id": s["segment_id"],
            "name": s.get("display_name") or s["segment_id"].replace("_", " ").title(),
            "color": SEGMENT_COLORS.get(s["segment_id"], "#a3e635"),
            "size": int(s["size"]),
            "share": round(s["share_pct"] / 100.0, 4),
            "engagement": round(s["avg_engagement_score"]),
            "annual_value": round(s["avg_annual_value_usd"]),
            "channel": s["preferred_channel"],
            "churn": round(s["churn_risk_pct"], 1),
            "traits": list(s.get("defining_traits") or []),
        })
    return out


def _segment_for_country(iso2: str, profiles: list[dict]) -> str:
    """Attribute a country to the first KMeans segment listing it among its
    top countries (profile order = descending engagement); countries no
    segment claims default to the largest segment."""
    candidates = {iso2}
    if iso2 == "GB":
        candidates.add("UK")
    if iso2 == "UK":
        candidates.add("GB")
    for seg in profiles:
        if candidates & set(seg.get("top_countries") or []):
            return seg["segment_id"]
    return max(profiles, key=lambda s: s["share_pct"])["segment_id"]


# --------------------------------------------------------------- countries
def _countries(db: Session) -> list[dict]:
    heat = analytics.get_heatmap(db, DEMO_MATCH_ID)
    if not heat:
        return []
    profiles = segments_engine.get_segments()["segments"]

    merged: dict[str, dict] = {}  # key: display code3 (merges GB/UK style dupes)
    for row in heat["countries"]:
        ref = COUNTRY_REF.get(row["country_code"])
        if not ref:
            continue  # no reference entry -> not displayable on the map; honest skip
        key = ref["code"]
        cur = merged.setdefault(key, {
            "code": ref["code"], "name": ref["name"], "coords": ref["coords"],
            "volume": 0, "_sent_x_vol": 0.0,
            "emotion": row["dominant_emotion"],
            "segment": _segment_for_country(row["country_code"], profiles),
            "_top_vol": -1,
        })
        cur["volume"] += row["mentions"]
        cur["_sent_x_vol"] += row["avg_sentiment"] * row["mentions"]
        if row["mentions"] > cur["_top_vol"]:
            cur["_top_vol"] = row["mentions"]
            cur["emotion"] = row["dominant_emotion"]

    out = []
    for c in merged.values():
        avg = c["_sent_x_vol"] / c["volume"] if c["volume"] else 0.0
        # analytics avg_sentiment is signed (-1..1); the UI's sentiment field
        # is a 0..1 positivity index -> linear rescale of the same measurement
        c["sentiment"] = round((avg + 1.0) / 2.0, 2)
        c.pop("_sent_x_vol"), c.pop("_top_vol")
        out.append(c)
    out.sort(key=lambda c: -c["volume"])
    return out


# --------------------------------------------------------------- industries
def _industries() -> list[dict]:
    return [{"id": INDUSTRY_TO_UI[slug]["id"], "label": INDUSTRY_TO_UI[slug]["label"],
             "primary": True} for slug in STARRED]


# --------------------------------------------------------------- strategies
def _load_moment_row(db: Session, moment_id: str | None):
    if not moment_id:
        return None
    from sqlalchemy import text
    return db.execute(text("SELECT * FROM moments WHERE id = :id"), {"id": moment_id}).fetchone()


def _ensure_campaigns(db: Session) -> None:
    """The strategies screen needs at least one card (the UI indexes
    STRATEGIES[0]). If nothing has been generated yet — fresh boot, before the
    first moment fires — generate a real baseline card per starred industry
    through the exact same engine path as the manual endpoint."""
    existing = db.query(DBCampaign).filter(DBCampaign.match_id == DEMO_MATCH_ID).count()
    if existing:
        return
    from .campaigns import build_campaign_card, _load_moment
    for slug in STARRED:
        try:
            moment = _load_moment(db, DEMO_MATCH_ID, None)  # latest live moment if any
            build_campaign_card(db, DEMO_MATCH_ID, Industry(slug),
                                BOOTSTRAP_BASELINE_BUDGET, trigger="bootstrap_baseline",
                                moment=moment)
        except Exception as e:
            logger.error(f"Bootstrap baseline campaign failed for {slug}: {e}")


def _strategies(db: Session) -> list[dict]:
    _ensure_campaigns(db)
    rows = (db.query(DBCampaign).filter(DBCampaign.match_id == DEMO_MATCH_ID)
            .order_by(DBCampaign.created_at.desc()).limit(8).all())
    now = datetime.now(timezone.utc)
    out = []
    for c in rows:
        ui_ind = INDUSTRY_TO_UI.get(c.industry)
        if not ui_ind:
            continue  # industry the locked UI has no icon/filter for — reported in docs
        copy = json.loads(c.copy_json)
        roi = json.loads(c.roi_json)
        mult = roi.get("multiplier", {})
        funnel = roi.get("funnel", {})

        created = datetime.fromisoformat(c.created_at.replace("Z", "+00:00"))
        ends_in = (c.window_minutes or 0) - (now - created).total_seconds() / 60.0

        moment_row = _load_moment_row(db, c.moment_id)
        if moment_row is not None:
            momentum = json.loads(moment_row.momentum_json)
            top = (momentum.get("top_countries") or [None])[0]
            location = COUNTRY_REF.get(top, {}).get("name", "Global") if top else "Global"
            trigger = {
                "type": EVENT_TAG_UI.get(moment_row.event_tag, "other surge"),
                "desc": moment_row.description or "",
                "moment_id": c.moment_id,
            }
        else:
            location = "Global"
            trigger = {"type": "kickoff",
                       "desc": "Baseline pre-match volume (no live moment)",
                       "moment_id": None}

        vb = copy.get("variant_b", {})
        out.append({
            "id": c.id,
            "industry": ui_ind["id"],
            "location": location,
            "segment": c.target_segment,
            "channel": c.channel,
            "archetype": ARCHETYPE_DISPLAY.get(c.archetype, c.archetype.replace("_", " ").title()),
            "window_min": c.window_minutes or 0,
            "ends_in_min": max(0, round(ends_in)),
            "confidence": round(c.confidence or 0.0, 2),
            "ai_generated": not bool(c.llm_fallback),
            "trigger": trigger,
            "copy": {
                "headline": copy.get("headline", ""),
                "body": copy.get("body", ""),
                "cta": copy.get("cta", ""),
                "hashtags": copy.get("hashtags", []),
            },
            "variant_b": {
                "headline": vb.get("headline", ""),
                "body": vb.get("body", ""),
                "cta": vb.get("cta", ""),
                "hashtags": vb.get("hashtags", []),
            },
            "multipliers": {
                "arousal": mult.get("arousal", 0.0),
                "emotion_fit": mult.get("emotion_brand_fit", 0.0),
                "moment": mult.get("moment_strength", 0.0),
                "segment": mult.get("segment_match", 0.0),
                "total": mult.get("M", 1.0),
            },
            "roi": {
                "impressions": funnel.get("impressions", 0),
                "reach": funnel.get("reach", 0),
                "clicks": funnel.get("clicks", 0),
                "conv": funnel.get("conversions", 0),
                "revenue": funnel.get("revenue_usd", 0.0),
                "roas": roi.get("roas", 0.0),
            },
            "benchmark": roi.get("benchmark_source", ""),
        })
    return out


# --------------------------------------------------------------- matches
def _latest_reforecast(db: Session, match_id: str) -> dict | None:
    row = (db.query(DBForecast)
           .filter(DBForecast.match_id == match_id, DBForecast.is_reforecast == 1)
           .order_by(DBForecast.id.desc()).first())
    return json.loads(row.forecast_json) if row else None


def _matches(db: Session, demo_kpis: dict | None) -> list[dict]:
    out = []
    for m in db.query(DBMatch).all():
        home_ref = TEAM_REF.get(m.home_team, {})
        away_ref = TEAM_REF.get(m.away_team, {})

        try:
            base = forecast_engine.predict_audience(match_features(m))
            baseline_di = base["demand_index"]
            sellout = base["sellout_probability"]
            importances = base["feature_importances"]
        except Exception as e:
            logger.warning(f"Forecast unavailable for {m.id}: {e}")
            baseline_di, sellout, importances = 0.0, 0.0, []

        refc = _latest_reforecast(db, m.id)
        if refc:
            demand_index = refc["demand_index"]
            sellout = refc["sellout_probability"]
            baseline_di = refc.get("baseline_demand_index") or baseline_di
            forecast_trigger = refc.get("trigger_description") or "baseline"
        else:
            demand_index = baseline_di
            forecast_trigger = "baseline"

        # Excitement: live momentum-based score when the match has signal,
        # otherwise the model's pre-match buzz (same formula the forecast
        # features use) as an expectation index.
        excitement = 0.0
        if m.id == DEMO_MATCH_ID and demo_kpis:
            excitement = demo_kpis.get("excitement_score", 0.0)
        if excitement <= 0:
            excitement = forecast_engine.baseline_buzz(match_features(m)) * 100.0

        total_w = sum(fi["importance"] for fi in importances) or 1.0
        drivers = [{"factor": DRIVER_LABELS.get(fi["feature"], fi["feature"]),
                    "weight": round(fi["importance"] / total_w, 2)}
                   for fi in importances[:5]]

        out.append({
            "id": m.id,
            "home": m.home_team, "home_short": home_ref.get("short", m.home_team[:3].upper()),
            "home_iso2": home_ref.get("iso2"),
            "away": m.away_team, "away_short": away_ref.get("short", m.away_team[:3].upper()),
            "away_iso2": away_ref.get("iso2"),
            "kickoff": m.kickoff_time,
            "tournament_stage": STAGE_LABELS.get(m.stage, f"Stage {m.stage}"),
            "venue": {"city": m.city or "TBD", "capacity": m.venue_capacity},
            "status": m.status,
            "demand_index": round(demand_index),
            "sellout_prob": round(sellout, 2),
            "score": {"home": m.home_score or 0, "away": m.away_score or 0,
                      "minute": match_state.current_minute(m)},
            "excitement": round(excitement),
            "baseline_forecast": round(baseline_di),
            "forecast_trigger": forecast_trigger,
            "drivers": drivers,
        })
    # Live first, then upcoming by kickoff, then finished — the UI selects MATCHES[0]
    order = {"live": 0, "upcoming": 1, "finished": 2}
    out.sort(key=lambda x: (order.get(x["status"], 3), x["kickoff"]))
    return out


# --------------------------------------------------------------- timeline
def _clock_ref(db: Session):
    m = db.query(DBMatch).filter(DBMatch.id == DEMO_MATCH_ID).first()
    if m and m.clock_started_at:
        return datetime.fromisoformat(m.clock_started_at.replace("Z", "+00:00"))
    return None


def _sentiment_timeline(db: Session) -> list[dict]:
    points = analytics.get_timeline(db, DEMO_MATCH_ID, bucket_s=30)
    if not points:
        return []
    ref = _clock_ref(db) or datetime.fromisoformat(points[0]["ts"].replace("Z", "+00:00"))

    by_minute: dict[int, dict] = {}
    for p in points:
        ts = datetime.fromisoformat(p["ts"].replace("Z", "+00:00"))
        minute = int(max(0.0, (ts - ref).total_seconds()) * match_state.REPLAY_TIME_SCALE / 60.0)
        b = by_minute.setdefault(minute, {"minute": minute, "pos": 0.0, "neg": 0.0,
                                          "neu": 0.0, "volume": 0})
        w = p["mentions"]
        b["pos"] += p["positive_pct"] * w
        b["neg"] += p["negative_pct"] * w
        b["neu"] += p["neutral_pct"] * w
        b["volume"] += w

    out = []
    for minute in sorted(by_minute):
        b = by_minute[minute]
        v = b["volume"] or 1
        out.append({
            "minute": minute,
            "positive": round(b["pos"] / v, 1),
            "negative": round(b["neg"] / v, 1),
            "neutral": round(b["neu"] / v, 1),
            "volume": b["volume"],
        })
    return out


# --------------------------------------------------------------- moments
def _moments(db: Session) -> list[dict]:
    from sqlalchemy import text
    rows = db.execute(text(
        "SELECT * FROM moments WHERE match_id = :m ORDER BY detected_at ASC LIMIT 40"
    ), {"m": DEMO_MATCH_ID}).fetchall()
    if not rows:
        return []
    ref = _clock_ref(db) or datetime.fromisoformat(rows[0].detected_at.replace("Z", "+00:00"))

    out = []
    for r in rows:
        momentum = json.loads(r.momentum_json)
        ts = datetime.fromisoformat(r.detected_at.replace("Z", "+00:00"))
        minute = int(max(0.0, (ts - ref).total_seconds()) * match_state.REPLAY_TIME_SCALE / 60.0)
        out.append({
            "id": r.id,
            "minute": min(minute, 90),
            "type": EVENT_TAG_UI.get(r.event_tag, "other surge"),
            "desc": r.description or "",
            "volume": momentum.get("volume_1m", 0),
            "emotion": momentum.get("dominant_emotion", "neutral"),
        })
    return out


# --------------------------------------------------------------- trending
def _trending(db: Session) -> list[dict]:
    return [{"topic": t["label"], "mentions": t["mentions"], "dir": t["trend"]}
            for t in analytics.get_topics(db, DEMO_MATCH_ID)[:6]]


# --------------------------------------------------------------- kpi ticker
def _kpi_ticker(db: Session, kpis: dict | None, live_count: int) -> list[dict]:
    latest = db.query(DBCampaign).order_by(DBCampaign.created_at.desc()).first()
    uplift = 1.0
    if latest:
        roi = json.loads(latest.roi_json)
        base = (roi.get("baseline_comparison") or {}).get("roas") or 0.0
        if base > 0:
            uplift = roi.get("roas", base) / base

    if kpis:
        region = COUNTRY_REF.get(kpis["most_active_region"], {}).get(
            "name", kpis["most_active_region"])
        items = [
            {"k": "MENTIONS", "v": f"{kpis['total_mentions']:,}"},
            {"k": "SENTIMENT+", "v": f"{kpis['positive_pct']:.1f}%"},
            {"k": "EXCITEMENT", "v": f"{round(kpis['excitement_score'])} / 100"},
            {"k": "TOP EMOTION", "v": str(kpis["top_emotion"]).upper()},
            {"k": "REGION", "v": region.upper()},
            {"k": "MSG/MIN", "v": f"{kpis['mentions_per_min']:,}"},
        ]
    else:  # no messages ingested yet — honest zero state
        items = [
            {"k": "MENTIONS", "v": "0"},
            {"k": "SENTIMENT+", "v": "0.0%"},
            {"k": "EXCITEMENT", "v": "0 / 100"},
            {"k": "TOP EMOTION", "v": "—"},
            {"k": "REGION", "v": "—"},
            {"k": "MSG/MIN", "v": "0"},
        ]
    items.append({"k": "MATCHES LIVE", "v": str(live_count)})
    items.append({"k": "ROI UPLIFT", "v": f"×{uplift:.1f}"})
    return items


# --------------------------------------------------------------- endpoint
@router.get("/ui/bootstrap")
def ui_bootstrap(db: Session = Depends(get_db)):
    kpis = analytics.get_kpis(db, DEMO_MATCH_ID)
    live_count = db.query(DBMatch).filter(DBMatch.status == "live").count()

    strategies = _strategies(db)
    countries = _countries(db)
    locations = sorted({c["name"] for c in countries} |
                       {s["location"] for s in strategies if s["location"] != "Global"})

    return {
        "brand": BRAND,
        "nav_links": NAV_LINKS,
        "features": FEATURES,
        "kpi_ticker": _kpi_ticker(db, kpis, live_count),
        "fan_segments": _fan_segments(),
        "countries": countries,
        "industries": _industries(),
        "locations": ["Global"] + locations,
        "strategies": strategies,
        "matches": _matches(db, kpis),
        "sentiment_timeline": _sentiment_timeline(db),
        "moments": _moments(db),
        "trending": _trending(db),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "demo_match_id": DEMO_MATCH_ID,
    }
