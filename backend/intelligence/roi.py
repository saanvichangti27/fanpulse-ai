from datetime import datetime, timezone
from typing import Optional, List, Dict

# Simple baseline metrics for simulation
INDUSTRY_METRICS = {
    "food_delivery": {"cpm": 12.0, "ctr": 0.02, "cvr": 0.05, "aov": 25.0},
    "merch_apparel": {"cpm": 15.0, "ctr": 0.015, "cvr": 0.04, "aov": 60.0},
    "streaming_ott": {"cpm": 20.0, "ctr": 0.03, "cvr": 0.08, "aov": 15.0},
    "beverages": {"cpm": 8.0, "ctr": 0.01, "cvr": 0.02, "aov": 10.0},
    "content_creator": {"cpm": 10.0, "ctr": 0.025, "cvr": 0.06, "aov": 5.0}
}

def simulate_roi(
    industry: str,
    channel: str,
    budget_usd: float,
    dominant_emotion: str = "neutral",
    volume_ratio: float = 1.0,
    segment_id: Optional[str] = None,
    demand_index: Optional[float] = None,
    is_baseline: bool = False
) -> dict:
    
    metrics = INDUSTRY_METRICS.get(industry, INDUSTRY_METRICS["food_delivery"])
    
    cpm = metrics["cpm"]
    base_ctr = metrics["ctr"]
    base_cvr = metrics["cvr"]
    aov = metrics["aov"]
    
    # Calculate Multiplier M
    if is_baseline:
        M = 1.0
        arousal = 0.0
        fit = 0.0
        strength = 0.0
        match = 0.5
    else:
        # Simplistic logic
        arousal = 0.8 if dominant_emotion in ["joy", "surprise", "anger"] else 0.2
        fit = 0.8 if industry in ["food_delivery", "merch_apparel"] else 0.5
        strength = min(volume_ratio / 3.0, 1.0)
        match = 0.9 if segment_id else 0.5
        
        M = 0.35 * arousal + 0.25 * fit + 0.20 * strength + 0.20 * match
        M = max(1.0, min(M + 0.5, 2.5)) # Ensure some lift for live moments
        
    eff_ctr = min(base_ctr * M, 1.0)
    eff_cvr = min(base_cvr * M, 1.0)
    
    impressions = int((budget_usd / cpm) * 1000)
    reach = int(impressions * 0.7)
    clicks = int(reach * eff_ctr)
    conversions = int(clicks * eff_cvr)
    revenue = float(conversions * aov)
    roas = float(revenue / budget_usd) if budget_usd > 0 else 0.0
    roi = float((revenue - budget_usd) / budget_usd) if budget_usd > 0 else 0.0

    # Baseline Funnel
    b_clicks = int(reach * base_ctr)
    b_conversions = int(b_clicks * base_cvr)
    b_revenue = float(b_conversions * aov)
    b_roas = float(b_revenue / budget_usd) if budget_usd > 0 else 0.0
    b_roi = float((b_revenue - budget_usd) / budget_usd) if budget_usd > 0 else 0.0

    return {
        "industry": industry,
        "channel": channel,
        "budget_usd": budget_usd,
        "multiplier": {
            "M": M,
            "arousal": arousal,
            "emotion_brand_fit": fit,
            "moment_strength": strength,
            "segment_match": match,
            "k": 1.0
        },
        "funnel": {
            "cpm_usd": cpm,
            "frequency": 1.4,
            "impressions": impressions,
            "reach": reach,
            "ctr_baseline": base_ctr,
            "ctr_effective": eff_ctr,
            "clicks": clicks,
            "cvr_baseline": base_cvr,
            "cvr_effective": eff_cvr,
            "conversions": conversions,
            "aov_usd": aov,
            "revenue_usd": revenue
        },
        "roas": roas,
        "roi_pct": roi,
        "baseline_comparison": {
            "roas": b_roas,
            "roi_pct": b_roi,
            "revenue_usd": b_revenue
        },
        "benchmark_source": "Antigravity Custom Engine v1",
        "confidence": 0.85,
        "computed_at": datetime.now(timezone.utc).isoformat()
    }


def plan_media(
    budget_usd: float,
    industry: str,
    forecasts: List[Dict]
) -> dict:
    
    if not forecasts:
        return {
            "total_budget_usd": budget_usd,
            "industry": industry,
            "allocations": [],
            "expected_total_roas": 0.0
        }
        
    # Apportion based on demand index, or split equally
    total_demand = sum(f.get("demand_index", 50.0) for f in forecasts)
    
    allocations = []
    total_revenue = 0.0
    for f in forecasts:
        demand = f.get("demand_index", 50.0)
        share = demand / total_demand if total_demand > 0 else (1.0 / len(forecasts))
        alloc_bud = share * budget_usd
        
        sim = simulate_roi(industry, "push", alloc_bud, is_baseline=True)
        total_revenue += sim["funnel"]["revenue_usd"]
        
        allocations.append({
            "match_id": f["match_id"],
            "budget_usd": alloc_bud,
            "share_pct": share * 100.0,
            "demand_index": demand,
            "expected_roas": sim["roas"],
            "expected_revenue_usd": sim["funnel"]["revenue_usd"],
            "rationale": f"Allocated {share*100:.1f}% based on demand index of {demand:.1f}"
        })
        
    roas = total_revenue / budget_usd if budget_usd > 0 else 0.0
    
    return {
        "total_budget_usd": budget_usd,
        "industry": industry,
        "allocations": allocations,
        "expected_total_roas": roas
    }
