"""ROI engine (Feature 6) — spec §6 implemented exactly.

Every number is (a) standard funnel arithmetic, (b) a benchmark row from
data/benchmarks/benchmarks.csv (cited per row), or (c) a live signal passed
through the documented multiplier formula. Nothing is random or hardcoded.

Funnel (spec §6.1):
    Impressions = (Budget / CPM) * 1000
    Reach       = Impressions / Frequency
    Clicks      = Impressions * CTR_eff
    Conversions = Clicks * CVR_eff
    Revenue     = Conversions * AOV
    ROAS        = Revenue / Budget ;  ROI% = (ROAS - 1) * 100

Multiplier (spec §6.3, constants from contracts.py):
    M       = clamp(1 + K * Arousal * EmotionBrandFit * MomentStrength * SegmentMatch, 0.7, 2.5)
    CTR_eff = CTR * M
    CVR_eff = CVR * (1 + (M - 1) * CVR_LIFT_DAMPING)

SegmentMatch: overlap of the target segment's top countries with the live
top countries: 0.5 + 0.5 * |intersection| / min(len(seg), len(live)); 0.5 is
the neutral prior when either side is unknown. Documented modelling choice.

Confidence (contract §F.3):
    clip(0.4*volume_support + 0.3*moment_recency + 0.3*segment_support, 0, 1)
    volume_support  = clip(volume_5m / 500, 0, 1)
    moment_recency  = clip(1 - age_min / 30, 0, 1)   (1.0 when no moment involved)
    segment_support = clip(segment_size / 500, 0, 1)
    Baseline mode: fixed 0.75 (benchmark-only figure).
"""
import os
import csv
from datetime import datetime, timezone
from typing import Optional, List, Dict

from ..contracts import (
    AROUSAL, MULTIPLIER_K, MULTIPLIER_MIN, MULTIPLIER_MAX,
    CVR_LIFT_DAMPING, BenchmarkNotFound,
)

_BENCHMARKS: Dict[tuple, dict] = {}
_FIT: Dict[tuple, float] = {}


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _data_dir() -> str:
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(repo_root, "data", "benchmarks")


def _load():
    global _BENCHMARKS, _FIT
    if _BENCHMARKS:
        return
    with open(os.path.join(_data_dir(), "benchmarks.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            _BENCHMARKS[(row["industry"], row["channel"])] = {
                "cpm_usd": float(row["cpm_usd"]),
                "ctr": float(row["ctr"]),
                "cvr": float(row["cvr"]),
                "aov_usd": float(row["aov_usd"]),
                "frequency": float(row["frequency"]),
                "source": row["source"],
            }
    with open(os.path.join(_data_dir(), "emotion_brand_fit.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            _FIT[(row["industry"], row["emotion"])] = float(row["fit"])


def get_benchmark(industry: str, channel: str) -> dict:
    _load()
    bench = _BENCHMARKS.get((industry, channel))
    if bench is None:
        raise BenchmarkNotFound(f"No benchmark row for ({industry}, {channel})")
    return bench


def compute_multiplier(
    momentum: Optional[dict],
    industry: str,
    target_segment: Optional[str] = None,
    segment_top_countries: Optional[List[str]] = None,
) -> dict:
    """momentum = analytics.get_momentum() dict, or None => baseline (M = 1.0)."""
    _load()
    if momentum is None:
        return {"M": 1.0, "arousal": 0.0, "emotion_brand_fit": 0.0,
                "moment_strength": 0.0, "segment_match": 0.0, "k": MULTIPLIER_K}

    emotion = momentum.get("dominant_emotion", "neutral")
    arousal = AROUSAL.get(emotion, 0.1)
    fit = _FIT.get((industry, emotion), 0.35)
    strength = _clip(momentum.get("volume_ratio", 1.0) / 3.0, 0.0, 1.0)

    live_countries = momentum.get("top_countries") or []
    if target_segment and segment_top_countries and live_countries:
        overlap = len(set(segment_top_countries) & set(live_countries))
        denom = min(len(segment_top_countries), len(live_countries))
        segment_match = 0.5 + 0.5 * (overlap / denom) if denom else 0.5
    else:
        segment_match = 0.5  # neutral prior when either side is unknown

    m = _clip(1.0 + MULTIPLIER_K * arousal * fit * strength * segment_match,
              MULTIPLIER_MIN, MULTIPLIER_MAX)
    return {"M": round(m, 3), "arousal": arousal, "emotion_brand_fit": fit,
            "moment_strength": round(strength, 3),
            "segment_match": round(segment_match, 3), "k": MULTIPLIER_K}


def _funnel(budget_usd: float, bench: dict, m: float) -> dict:
    ctr_eff = min(bench["ctr"] * m, 1.0)
    cvr_eff = min(bench["cvr"] * (1.0 + (m - 1.0) * CVR_LIFT_DAMPING), 1.0)
    impressions = int((budget_usd / bench["cpm_usd"]) * 1000)
    reach = int(impressions / bench["frequency"])
    clicks = int(impressions * ctr_eff)
    conversions = int(clicks * cvr_eff)
    revenue = round(conversions * bench["aov_usd"], 2)
    return {
        "cpm_usd": bench["cpm_usd"], "frequency": bench["frequency"],
        "impressions": impressions, "reach": reach,
        "ctr_baseline": bench["ctr"], "ctr_effective": round(ctr_eff, 5),
        "clicks": clicks,
        "cvr_baseline": bench["cvr"], "cvr_effective": round(cvr_eff, 5),
        "conversions": conversions,
        "aov_usd": bench["aov_usd"], "revenue_usd": revenue,
    }


def _confidence(momentum: Optional[dict], segment_size: Optional[int],
                moment_age_min: float) -> float:
    if momentum is None:
        return 0.75
    volume_support = _clip(momentum.get("volume_5m", 0) / 500.0, 0.0, 1.0)
    moment_recency = _clip(1.0 - moment_age_min / 30.0, 0.0, 1.0)
    segment_support = _clip((segment_size or 0) / 500.0, 0.0, 1.0)
    return round(_clip(0.4 * volume_support + 0.3 * moment_recency
                       + 0.3 * segment_support, 0.0, 1.0), 2)


def simulate_roi(
    industry: str,
    channel: str,
    budget_usd: float,
    momentum: Optional[dict] = None,
    target_segment: Optional[str] = None,
    segment_top_countries: Optional[List[str]] = None,
    segment_size: Optional[int] = None,
    moment_age_min: float = 0.0,
) -> dict:
    """Full ROIResult dict (contract §B.8). momentum=None => baseline mode (M=1)."""
    bench = get_benchmark(industry, channel)
    mult = compute_multiplier(momentum, industry, target_segment, segment_top_countries)

    funnel = _funnel(budget_usd, bench, mult["M"])
    roas = round(funnel["revenue_usd"] / budget_usd, 3) if budget_usd > 0 else 0.0

    base_funnel = _funnel(budget_usd, bench, 1.0)
    base_roas = round(base_funnel["revenue_usd"] / budget_usd, 3) if budget_usd > 0 else 0.0

    return {
        "industry": industry, "channel": channel, "budget_usd": budget_usd,
        "multiplier": mult, "funnel": funnel,
        "roas": roas, "roi_pct": round((roas - 1.0) * 100.0, 1),
        "baseline_comparison": {
            "roas": base_roas,
            "roi_pct": round((base_roas - 1.0) * 100.0, 1),
            "revenue_usd": base_funnel["revenue_usd"],
        },
        "benchmark_source": f"{bench['source']} — {industry}/{channel}",
        "confidence": _confidence(momentum, segment_size, moment_age_min),
        "computed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def best_channel(industry: str, preferred_channel: Optional[str] = None) -> str:
    """Channel with the best benchmark ROAS proxy (ctr*cvr*aov/cpm) for the
    industry. A segment's preferred channel wins if it reaches >= 80% of the
    top proxy (preference beats a marginal ROI edge)."""
    _load()
    proxies = {
        ch: b["ctr"] * b["cvr"] * b["aov_usd"] / b["cpm_usd"]
        for (ind, ch), b in _BENCHMARKS.items() if ind == industry
    }
    if not proxies:
        raise BenchmarkNotFound(f"No benchmark rows for industry {industry}")
    top_channel = max(proxies, key=proxies.get)
    if preferred_channel in proxies and proxies[preferred_channel] >= 0.8 * proxies[top_channel]:
        return preferred_channel
    return top_channel


def plan_media(
    budget_usd: float,
    industry: str,
    forecasts: List[Dict],
    momenta: Optional[Dict[str, Optional[dict]]] = None,
    channel: Optional[str] = None,
) -> dict:
    """Allocate budget across matches proportional to demand_index * expected_M,
    greedy with a 60% single-match cap (spec Feature 6b)."""
    momenta = momenta or {}
    channel = channel or best_channel(industry)

    if not forecasts:
        return {"total_budget_usd": budget_usd, "industry": industry,
                "allocations": [], "expected_total_roas": 0.0}

    weights = {}
    expected_m = {}
    for f in forecasts:
        mid = f["match_id"]
        mult = compute_multiplier(momenta.get(mid), industry)
        expected_m[mid] = mult["M"]
        weights[mid] = max(f.get("demand_index") or 0.0, 1.0) * mult["M"]

    total_w = sum(weights.values())
    shares = {mid: w / total_w for mid, w in weights.items()}

    # 60% cap with redistribution (only meaningful when n >= 2)
    if len(shares) >= 2:
        capped = {mid: min(s, 0.6) for mid, s in shares.items()}
        excess = 1.0 - sum(capped.values())
        uncapped = [mid for mid in capped if shares[mid] < 0.6]
        if excess > 1e-9 and uncapped:
            sub = sum(shares[mid] for mid in uncapped)
            for mid in uncapped:
                capped[mid] += excess * (shares[mid] / sub)
        shares = capped

    allocations = []
    total_revenue = 0.0
    for f in forecasts:
        mid = f["match_id"]
        alloc = shares[mid] * budget_usd
        sim = simulate_roi(industry, channel, alloc, momentum=momenta.get(mid))
        total_revenue += sim["funnel"]["revenue_usd"]
        capped_note = " (capped at 60%)" if shares[mid] == 0.6 and len(shares) >= 2 else ""
        allocations.append({
            "match_id": mid,
            "budget_usd": round(alloc, 2),
            "share_pct": round(shares[mid] * 100.0, 1),
            "demand_index": round(f.get("demand_index") or 0.0, 1),
            "expected_roas": sim["roas"],
            "expected_revenue_usd": sim["funnel"]["revenue_usd"],
            "rationale": (f"demand index {f.get('demand_index') or 0.0:.0f} x "
                          f"expected multiplier {expected_m[mid]:.2f}{capped_note}"),
        })

    allocations.sort(key=lambda a: a["budget_usd"], reverse=True)
    return {
        "total_budget_usd": budget_usd, "industry": industry,
        "allocations": allocations,
        "expected_total_roas": round(total_revenue / budget_usd, 2) if budget_usd > 0 else 0.0,
    }
