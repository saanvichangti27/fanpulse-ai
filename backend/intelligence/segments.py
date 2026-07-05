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

def get_segments() -> dict:
    """
    Returns the segment profiles, silhouette score, and total fans.
    Shape matches SegmentReport contract.
    """
    _load_artifacts()
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

def get_next_best_actions(industry: Optional[str] = None) -> List[dict]:
    """
    Returns Next Best Action matrix rules per (segment x industry).
    If industry is provided, filters for that industry.
    """
    _load_artifacts()
    
    # The 5 starred industries (demo focus)
    starred_industries = ["food_delivery", "merch_apparel", "beverages", "streaming_ott", "content_creator"]
    
    target_industries = [industry] if industry else starred_industries
    
    actions = []
    
    # Simple rule engine
    for seg in _PROFILES["segments"]:
        seg_id = seg["segment_id"]
        pref_channel = seg["preferred_channel"]
        
        for ind in target_industries:
            archetype = "brand_awareness"
            timing = "baseline"
            expected_ctr = 0.01 # Base benchmark
            rationale = "General brand engagement."
            
            # 1. Food Delivery
            if ind == "food_delivery":
                if seg_id == "deal_seekers":
                    archetype = "celebration_flash_offer"
                    timing = "immediately post-moment"
                    expected_ctr = 0.04
                    rationale = "High offer-responsiveness, high push opt-in."
                elif seg_id == "casual_streamers":
                    archetype = "celebration_flash_offer"
                    timing = "during match"
                    expected_ctr = 0.02
                    rationale = "Watching at home, likely to order food."
                elif seg_id == "traveling_ultras":
                    archetype = "brand_awareness"
                    timing = "pre-match"
                    expected_ctr = 0.015
                    rationale = "At the venue, unlikely to order delivery."
                else:
                    archetype = "consolation_offer"
                    timing = "post-match"
                    expected_ctr = 0.015
                    rationale = "Standard food delivery targeting."
                    
            # 2. Merch Apparel
            elif ind == "merch_apparel":
                if seg_id == "superfans":
                    archetype = "commemorative_drop"
                    timing = "immediately post-win"
                    expected_ctr = 0.05
                    rationale = "High merch spend history, strong emotional tie."
                elif seg_id == "traveling_ultras":
                    archetype = "commemorative_drop"
                    timing = "post-match"
                    expected_ctr = 0.04
                    rationale = "High disposable income, match attendance."
                else:
                    archetype = "flash_sale"
                    timing = "post-match"
                    expected_ctr = 0.012
                    rationale = "Merch engagement for average fans."
                    
            # 3. Beverages
            elif ind == "beverages":
                if seg_id == "casual_streamers":
                    archetype = "watch_it_here"
                    timing = "pre-match"
                    expected_ctr = 0.025
                    rationale = "High streaming time, home consumption."
                else:
                    archetype = "brand_awareness"
                    timing = "during match"
                    expected_ctr = 0.01
                    rationale = "Broad reach beverage targeting."
                    
            # 4. Streaming OTT
            elif ind == "streaming_ott":
                if seg_id == "casual_streamers":
                    archetype = "tune_in_push"
                    timing = "pre-match"
                    expected_ctr = 0.035
                    rationale = "Primary consumption method is streaming."
                elif seg_id == "lapsed_fans":
                    archetype = "tune_in_push"
                    timing = "pre-match"
                    expected_ctr = 0.01
                    rationale = "Attempting to re-engage via streaming access."
                else:
                    archetype = "tune_in_push"
                    timing = "pre-match"
                    expected_ctr = 0.015
                    rationale = "Standard tune-in prompt."
                    
            # 5. Content Creator
            elif ind == "content_creator":
                archetype = "content_idea"
                timing = "during peak moment"
                expected_ctr = 0.06
                rationale = "Capitalize on high arousal moments for content."
                
            actions.append({
                "segment_id": seg_id,
                "industry": ind,
                "channel": pref_channel,
                "archetype": archetype,
                "timing_rule": timing,
                "expected_ctr": expected_ctr,
                "rationale": rationale
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
