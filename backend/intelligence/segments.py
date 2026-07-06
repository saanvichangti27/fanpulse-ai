import os
import json
import pickle
import pandas as pd
from typing import Dict, List, Optional

# Global cache to load models once
_PROFILES = None
_KMEANS = None
_SCALER = None

def _load_artifacts():
    global _PROFILES, _KMEANS, _SCALER
    if _PROFILES is None:
        artifacts_dir = os.path.join(os.path.dirname(__file__), "artifacts")
        
        with open(os.path.join(artifacts_dir, "segment_profiles.json"), "r") as f:
            _PROFILES = json.load(f)
            
        with open(os.path.join(artifacts_dir, "kmeans_model.pkl"), "rb") as f:
            _KMEANS = pickle.load(f)
            
        with open(os.path.join(artifacts_dir, "scaler.pkl"), "rb") as f:
            _SCALER = pickle.load(f)

_TRAIT_LABELS = {
    "matches_attended": "match attendance", "tickets_bought_24m": "ticket buying",
    "avg_ticket_spend_usd": "ticket spend", "merch_purchases_12m": "merch buying",
    "merch_spend_usd_12m": "merch spend", "app_sessions_30d": "app usage",
    "email_open_rate": "email opens", "days_since_last_engagement": "time since last engagement",
    "streaming_minutes_30d": "streaming time", "social_shares_30d": "social sharing",
}


def _derive_traits(seg: dict, all_segments: list) -> list:
    """Data-derived defining traits: the features where this segment's KMeans
    centroid deviates most from the cross-segment mean (relative deviation)."""
    traits = []
    centroid = seg.get("centroid", {})
    scored = []
    for feat, label in _TRAIT_LABELS.items():
        vals = [s["centroid"].get(feat, 0.0) for s in all_segments if "centroid" in s]
        if not vals or feat not in centroid:
            continue
        mean = sum(vals) / len(vals)
        spread = (max(vals) - min(vals)) or 1e-9
        rel = (centroid[feat] - mean) / spread
        scored.append((abs(rel), rel, label))
    for _, rel, label in sorted(scored, reverse=True)[:3]:
        traits.append(f"{'high' if rel > 0 else 'low'} {label}")
    opt_in = centroid.get("push_opt_in")
    if opt_in is not None and opt_in >= 0.7:
        traits.append(f"push opt-in {opt_in * 100:.0f}%")
    return traits


def get_segments() -> dict:
    """Segment profiles + silhouette + n_fans (SegmentReport contract shape)."""
    _load_artifacts()
    segs = _PROFILES.get("segments", [])
    for seg in segs:
        if "display_name" not in seg:
            seg["display_name"] = seg["segment_id"].replace("_", " ").title()
        if not seg.get("defining_traits"):
            seg["defining_traits"] = _derive_traits(seg, segs)
        if "activity_share_pct" not in seg:
            # Static prior; overwritten with the live overlay when a match_id is given
            seg["activity_share_pct"] = seg.get("share_pct", 0.0)
    return _PROFILES

def get_active_overlay(country_volumes: Dict[str, int]) -> Dict[str, float]:
    """
    Calculates the active overlay (share of activity) per segment based on live country volumes.
    Uses the segment's top countries to distribute the volume.
    Returns: segment_id -> activity_share_pct (0-100)
    """
    _load_artifacts()
    
    # We assign volume points to segments if they contain the country in top_countries
    segment_points = {seg["segment_id"]: 0.0 for seg in _PROFILES["segments"]}
    
    for country, volume in country_volumes.items():
        # Find which segments have this country in their top_countries
        matching_segs = [s["segment_id"] for s in _PROFILES["segments"] if country in s["top_countries"]]
        
        if matching_segs:
            # Distribute volume equally among matching segments
            share = volume / len(matching_segs)
            for seg_id in matching_segs:
                segment_points[seg_id] += share
                
    total_points = sum(segment_points.values())
    if total_points == 0:
        return {s: 0.0 for s in segment_points}
        
    return {seg_id: (points / total_points) * 100.0 for seg_id, points in segment_points.items()}

# NBA rulebook: (archetype, timing_rule, affinity, rationale) per segment x industry.
# expected_ctr = benchmark CTR for (industry, segment's preferred channel) x affinity.
# Affinity is a documented, curated response factor (offer-responsive segments
# beat the category benchmark; poor-fit segments fall below it) — the benchmark
# itself always comes from data/benchmarks/benchmarks.csv.
_NBA_RULES = {
    "food_delivery": {
        "deal_seekers":     ("celebration_flash_offer", "immediately post-moment", 1.8,
                             "High offer-responsiveness and push opt-in; flash offers convert well above benchmark."),
        "casual_streamers": ("celebration_flash_offer", "during match", 1.3,
                             "Watching at home; in-match ordering context."),
        "traveling_ultras": ("brand_awareness", "pre-match", 0.7,
                             "At the venue, unlikely to order delivery."),
        "*":                ("consolation_offer", "post-match", 0.9,
                             "Standard food-delivery targeting."),
    },
    "merch_apparel": {
        "superfans":        ("commemorative_drop", "immediately post-win", 2.0,
                             "High merch spend history, strong emotional tie."),
        "traveling_ultras": ("commemorative_drop", "post-match", 1.6,
                             "High disposable income, match attendance."),
        "*":                ("flash_sale", "post-match", 0.8,
                             "Merch engagement for average fans."),
    },
    "beverages": {
        "casual_streamers": ("watch_it_here", "pre-match", 1.4,
                             "High streaming time, home consumption."),
        "*":                ("brand_awareness", "during match", 0.9,
                             "Broad-reach beverage targeting."),
    },
    "streaming_ott": {
        "casual_streamers": ("tune_in_push", "pre-match", 1.6,
                             "Primary consumption method is streaming."),
        "lapsed_fans":      ("tune_in_push", "pre-match", 0.6,
                             "Re-engagement attempt; expect below-benchmark response."),
        "*":                ("tune_in_push", "pre-match", 1.0,
                             "Standard tune-in prompt."),
    },
    "content_creator": {
        "*":                ("content_idea", "during peak moment", 1.5,
                             "High-arousal moments drive above-benchmark content engagement."),
    },
}

STARRED_INDUSTRIES = ["food_delivery", "merch_apparel", "beverages", "streaming_ott", "content_creator"]


def get_next_best_actions(industry: Optional[str] = None) -> List[dict]:
    """NBA matrix per (segment x industry): archetype + timing from the curated
    rulebook; expected_ctr = benchmark CTR (benchmarks.csv) x affinity factor."""
    _load_artifacts()
    from . import roi as roi_engine  # benchmark lookups (lazy: avoids import cycles)

    target_industries = [industry] if industry else STARRED_INDUSTRIES
    actions = []
    for seg in _PROFILES["segments"]:
        seg_id = seg["segment_id"]
        pref_channel = seg["preferred_channel"]
        for ind in target_industries:
            rules = _NBA_RULES.get(ind, {})
            archetype, timing, affinity, rationale = rules.get(seg_id, rules.get("*",
                ("brand_awareness", "baseline", 1.0, "General brand engagement.")))
            bench = roi_engine.get_benchmark(ind, pref_channel)
            actions.append({
                "segment_id": seg_id,
                "industry": ind,
                "channel": pref_channel,
                "archetype": archetype,
                "timing_rule": timing,
                "expected_ctr": round(bench["ctr"] * affinity, 5),
                "rationale": f"{rationale} (benchmark {pref_channel} CTR {bench['ctr']:.3%} x {affinity} affinity)",
            })
    return actions

if __name__ == "__main__":
    import pprint
    print("Segments:")
    pprint.pprint(get_segments())
    
    print("\nActive Overlay:")
    pprint.pprint(get_active_overlay({"BR": 5000, "UK": 1000}))
    
    print("\nNext Best Actions (food_delivery):")
    pprint.pprint(get_next_best_actions("food_delivery"))
