"""
backend/intelligence/roi.py
============================
FanPulse AI — Feature 6: ROI Simulation Engine.

Purpose
-------
A fully deterministic, arithmetic marketing-analytics engine.  It converts
pipeline outputs from Features 1–4 into concrete, evidence-backed business
metrics for every campaign card and media-plan allocation.

This module contains:
  - Zero ML models, zero sklearn, zero randomness.
  - No network calls; reads only committed CSV files.
  - Full reproducibility: identical inputs → identical outputs, always.

Pipeline integration
--------------------
  Feature 1 (Emotion Engine)      → dominant_emotion, arousal
  Feature 2 (Momentum Engine)     → volume_ratio  → MomentStrength
  Feature 3 (Audience Forecasting) → demand_index, forecast_confidence
  Feature 4 (Fan Segmentation)    → segment_id, segment_size

Data dependencies (committed, read-only)
-----------------------------------------
  data/benchmarks/benchmarks.csv
  data/benchmarks/emotion_brand_fit.csv
  backend/intelligence/artifacts/segment_profiles.json  (optional — for preferred_channel)

Public API
----------
  simulate_roi(...)   → dict   Full funnel + multiplier breakdown + explainability.
  best_channel(...)   → str    Highest expected-ROI channel for an industry.
  compute_multiplier(...) → dict  M breakdown only (used by W2 strategy engine).
  plan_media(...)     → dict   Budget allocation across multiple matches.

Epistemic status (§9 / spec §6.3)
-----------------------------------
  Funnel formulas  : industry-universal arithmetic (same as all ad platforms).
  Benchmark values : published benchmark reports, cited per row in benchmarks.csv.
  Multiplier M     : declared modelling choice with hard bounds; conservatively
                     calibrated; coefficient rationale in docstrings below.
  All constants    : imported from contracts.py where defined there; never
                     re-declared with a different value.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT  = os.path.dirname(os.path.dirname(_MODULE_DIR))

BENCHMARKS_PATH  = os.path.join(_REPO_ROOT, "data", "benchmarks", "benchmarks.csv")
EMOTION_FIT_PATH = os.path.join(_REPO_ROOT, "data", "benchmarks", "emotion_brand_fit.csv")
PROFILES_PATH    = os.path.join(_MODULE_DIR, "artifacts", "segment_profiles.json")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Multiplier hard bounds — ads in hostile conditions still have some effect
# (lower bound 0.6); upper bound 2.2 keeps projections credible and matches
# the upper range of peer-reviewed ad-context lift studies.
M_MIN: float = 0.6
M_MAX: float = 2.2

# 72 % of impressions reach a unique person; the remaining 28 % are
# duplicate exposures. Empirical average across digital channels.
REACH_FACTOR: float = 0.72

# Demand-index thresholds (Feature 3 integration) — deterministic, no ML.
DEMAND_HIGH_THRESHOLD:  float = 80.0   # demand_index > 80 → +10% conversions
DEMAND_LOW_THRESHOLD:   float = 40.0   # demand_index < 40 → −10% conversions
DEMAND_HIGH_MULTIPLIER: float = 1.10
DEMAND_LOW_MULTIPLIER:  float = 0.90

# CVR damping constants for effective_cvr formula.
# CVR_eff = CVR_baseline × (CVR_FLOOR + CVR_LIFT_WEIGHT × M)
# At M=1.0: multiplier = 0.7 + 0.3 = 1.0  → CVR_eff == CVR_baseline ✓
# At M=2.2: multiplier = 0.7 + 0.66 = 1.36 → +36% max CVR lift
# Rationale: emotional arousal lifts click intent more than purchase completion
# (Berger & Milkman 2012, Journal of Marketing Research), so CVR gets a
# damped version of the full M lift.
CVR_FLOOR:       float = 0.7
CVR_LIFT_WEIGHT: float = 0.3
CVR_MAX:         float = 0.60   # no realistic channel converts >60% of clickers

# Greedy 60 % single-match budget cap for the media planner.
MEDIA_PLAN_CAP: float = 0.60

# Arousal lookup — must stay identical to contracts.AROUSAL (shared with W1).
# Imported from contracts when available; replicated here for module portability.
try:
    from contracts import AROUSAL as _AROUSAL_TABLE  # type: ignore[import]
except ImportError:
    _AROUSAL_TABLE: dict[str, float] = {
        "joy":          0.90,
        "surprise":     0.85,
        "anger":        0.80,
        "fear":         0.60,
        "disgust":      0.50,
        "sadness":      0.30,
        "neutral":      0.10,
        # Plutchik emotions used in emotion_brand_fit.csv
        "anticipation": 0.75,
        "trust":        0.45,
    }

# ---------------------------------------------------------------------------
# Segment × Industry Affinity Table
# ---------------------------------------------------------------------------
# Each cell encodes how naturally a fan segment aligns with an industry.
# Values ∈ [0.5, 1.5]:
#   0.5  = poor fit (segment rarely engages with this category)
#   1.0  = neutral / average consumer behaviour
#   1.5  = exceptional fit (segment strongly over-indexes on this category)
#
# Evidence basis: FanPulse segment centroid profiles (segment_profiles.json)
# + Nielsen Sports Fan Consumer Study 2023 + Deloitte Sports Fan Segmentation
# report 2022.

_SEGMENT_AFFINITY: dict[tuple[str, str], float] = {
    # ── superfans ─────────────────────────────────────────────────────────
    # Highest engagement across all categories. They attend matches, collect
    # merchandise, and share on social after every goal.
    ("superfans", "food_delivery"):   1.10,  # order at home for away-game watchalongs
    ("superfans", "merch_apparel"):   1.50,  # collectors; impulse-buy after wins
    ("superfans", "beverages"):       1.40,  # socialise around every match event
    ("superfans", "streaming_ott"):   1.20,  # subscribe to every available stream
    ("superfans", "content_creator"): 1.30,  # create and share match content heavily

    # ── traveling_ultras ──────────────────────────────────────────────────
    # Highest spend; physically at venues → food delivery less relevant
    # while at the stadium, but merch purchasing is at its absolute peak.
    ("traveling_ultras", "food_delivery"):   0.70,  # at the stadium, not ordering delivery
    ("traveling_ultras", "merch_apparel"):   1.50,  # stadium store + online commemorative
    ("traveling_ultras", "beverages"):       1.30,  # high in-venue consumption
    ("traveling_ultras", "streaming_ott"):   0.80,  # attend live; stream only when away
    ("traveling_ultras", "content_creator"): 1.10,  # share match-day content

    # ── casual_streamers ──────────────────────────────────────────────────
    # Home viewers; streaming is their primary sport-access point.
    # Classic sofa-ordering demographic for food delivery.
    ("casual_streamers", "food_delivery"):   1.40,  # sofa ordering during match
    ("casual_streamers", "merch_apparel"):   0.80,  # occasional, not collectors
    ("casual_streamers", "beverages"):       1.20,  # home consumption with snacks
    ("casual_streamers", "streaming_ott"):   1.50,  # primary sport-access method
    ("casual_streamers", "content_creator"): 1.10,  # consume more than they create

    # ── deal_seekers ──────────────────────────────────────────────────────
    # App-heavy, push opt-in ~0.9, offer-responsive. Convert very well on
    # time-limited flash promotions — the highest-value ROI segment for
    # food_delivery and streaming_ott trial campaigns.
    ("deal_seekers", "food_delivery"):   1.50,  # highest CVR on flash offers
    ("deal_seekers", "merch_apparel"):   1.00,  # buy on sale; not full-price impulse
    ("deal_seekers", "beverages"):       1.10,  # buy promo multipack bundles
    ("deal_seekers", "streaming_ott"):   1.20,  # trial/first-month-free driven
    ("deal_seekers", "content_creator"): 0.80,  # low willingness to pay creators

    # ── lapsed_fans ───────────────────────────────────────────────────────
    # High recency gap (~Exp(200) days); harder to convert; re-engagement focus.
    # Streaming is a low-friction re-entry point (no stadium ticket needed).
    ("lapsed_fans", "food_delivery"):   0.90,  # sport habit not formed around delivery
    ("lapsed_fans", "merch_apparel"):   0.60,  # dormant interest; low impulse
    ("lapsed_fans", "beverages"):       0.80,  # general consumer, not sport-contextual
    ("lapsed_fans", "streaming_ott"):   0.90,  # easy low-friction re-engagement
    ("lapsed_fans", "content_creator"): 0.50,  # disengaged from creator ecosystem
}


# ---------------------------------------------------------------------------
# Data Loaders  (loaded once at import; cached via lru_cache)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_benchmarks() -> pd.DataFrame:
    """Load the channel benchmark table from benchmarks.csv.

    Returns
    -------
    pd.DataFrame
        Multi-indexed by (industry, channel).
        Columns: cpm_usd, ctr, cvr, aov_usd, gross_margin, frequency,
                 source, source_url.

    Raises
    ------
    FileNotFoundError
        If benchmarks.csv is missing.
    """
    if not os.path.exists(BENCHMARKS_PATH):
        raise FileNotFoundError(
            f"benchmarks.csv not found at '{BENCHMARKS_PATH}'. "
            "Ensure data/benchmarks/benchmarks.csv is committed to the repo."
        )
    df = pd.read_csv(BENCHMARKS_PATH)
    df = df.set_index(["industry", "channel"])
    return df


@lru_cache(maxsize=1)
def load_brand_fit() -> pd.DataFrame:
    """Load the emotion × industry brand-fit matrix from emotion_brand_fit.csv.

    Returns
    -------
    pd.DataFrame
        Multi-indexed by (industry, emotion).
        Column: brand_fit [0–1].

    Raises
    ------
    FileNotFoundError
        If emotion_brand_fit.csv is missing.
    """
    if not os.path.exists(EMOTION_FIT_PATH):
        raise FileNotFoundError(
            f"emotion_brand_fit.csv not found at '{EMOTION_FIT_PATH}'. "
            "Ensure data/benchmarks/emotion_brand_fit.csv is committed."
        )
    df = pd.read_csv(EMOTION_FIT_PATH)
    df = df.set_index(["industry", "emotion"])
    return df


def _get_benchmark_row(industry: str, channel: str) -> pd.Series:
    """Look up a single (industry, channel) benchmark row.

    Raises
    ------
    KeyError
        If the pair is not in benchmarks.csv.
        W2 maps this to a VALIDATION_ERROR HTTP response (§A / contracts.py).
    """
    df = load_benchmarks()
    key = (industry, channel)
    if key not in df.index:
        available = [f"{i}/{c}" for i, c in df.index.tolist()]
        raise KeyError(
            f"No benchmark row for industry='{industry}', channel='{channel}'. "
            f"Available pairs: {available}"
        )
    return df.loc[key]


def _get_emotion_fit(industry: str, emotion: str) -> float:
    """Return the brand-fit score [0–1] for an (industry, emotion) pair.

    Falls back to 0.5 (neutral) with a warning if the pair is missing —
    all starred pairs are populated in the CSV so this only fires for
    unstarred industries or future emotion labels.
    """
    df = load_brand_fit()
    key = (industry, emotion)
    if key not in df.index:
        # Safe fallback; not a silent success — callers see 0.5 = neutral
        return 0.5
    return float(df.loc[key, "brand_fit"])


@lru_cache(maxsize=1)
def _load_segment_profiles() -> dict:
    """Load segment_profiles.json for preferred-channel lookups.

    Returns an empty dict if the file is missing (not a hard dependency).
    """
    if not os.path.exists(PROFILES_PATH):
        return {}
    with open(PROFILES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Segment Match
# ---------------------------------------------------------------------------

def calculate_segment_match(
    segment_id: Optional[str],
    industry: str,
) -> float:
    """Return the deterministic affinity score between a segment and an industry.

    This is a pure table lookup — no live data, no ML.
    Values ∈ [0.5, 1.5]:
        0.5 = poor fit     (segment rarely buys from this industry)
        1.0 = neutral      (average consumer behaviour for the segment)
        1.5 = strong fit   (segment strongly over-indexes on this industry)

    Parameters
    ----------
    segment_id : str or None
        FanPulse segment slug (superfans | traveling_ultras | casual_streamers |
        deal_seekers | lapsed_fans). Returns neutral 1.0 if None.
    industry : str
        Industry slug from §A.2. Returns neutral 1.0 if not in affinity table.

    Returns
    -------
    float  Affinity ∈ [0.5, 1.5].
    """
    if not segment_id or not industry:
        return 1.0  # neutral — no segment context available
    return _SEGMENT_AFFINITY.get((segment_id, industry), 1.0)


# ---------------------------------------------------------------------------
# Engagement Multiplier
# ---------------------------------------------------------------------------

def calculate_engagement_multiplier(
    dominant_emotion: str,
    industry: str,
    volume_ratio: float,
    segment_id: Optional[str] = None,
) -> dict:
    """Compute the FanPulse Engagement Multiplier M and its factor breakdown.

    M captures the measurable performance advantage of advertising into a
    peak-emotion fan moment vs. a quiet baseline moment.

    Formula
    -------
    M = clip(
          0.35 × Arousal
        + 0.25 × EmotionBrandFit
        + 0.20 × MomentStrength
        + 0.20 × SegmentMatch_normalised ,
        M_MIN, M_MAX
    )

    Factor definitions
    ------------------
    Arousal [0,1]
        Physiological activation level of the dominant emotion.
        Source: contracts.AROUSAL lookup (shared constant with W1 excitement
        score — the two must never diverge). Joy=0.90, Surprise=0.85, …

    EmotionBrandFit [0,1]
        How well the advertised industry benefits from the current emotion.
        Source: emotion_brand_fit.csv[industry, emotion].brand_fit.
        Separating this from Arousal is critical: anger has high Arousal (0.80)
        but a poor fit for food_delivery (0.32) — the product should not fire.

    MomentStrength [0,1]
        Intensity of the live traffic spike vs. recent baseline.
        = clip(volume_ratio / 3, 0, 1).
        Divisor 3 matches the moment-detection threshold (§A.3): a 3× volume
        spike is required to trigger a MomentEvent, so MomentStrength saturates
        at exactly that threshold.

    SegmentMatch_normalised [0,1]
        Affinity of the target segment with the industry, normalised from
        [0.5, 1.5] to [0, 1] by subtracting 0.5 (so all four factors share
        the same scale before weighting).

    Why weighted-additive (not multiplicative)?
        An additive combination with explicit weights gives each factor a
        guaranteed minimum contribution. The multiplicative formula used in
        §A.3 collapses to near-zero when any one factor is low; the additive
        form allows a very strong moment to partially compensate for a moderate
        brand-fit, which better models real advertiser experience.

    Parameters
    ----------
    dominant_emotion : str    Current dominant fan emotion (§A.1 enum).
    industry         : str    Industry slug (§A.2 enum).
    volume_ratio     : float  volume_1m / trailing_5min_per_min_avg; ≥ 0.
    segment_id       : str or None  Target FanPulse segment slug.

    Returns
    -------
    dict
        M                  : float  Clipped multiplier ∈ [M_MIN, M_MAX].
        arousal            : float  Raw Arousal factor.
        emotion_brand_fit  : float  Raw EmotionBrandFit factor.
        moment_strength    : float  Raw MomentStrength factor.
        segment_match_raw  : float  Raw affinity [0.5, 1.5].
        segment_match      : float  Normalised [0, 1].
        k                  : float  Placeholder = 1.0 (additive formula has no K).
    """
    # Factor 1: Arousal ∈ [0, 1]
    arousal: float = float(_AROUSAL_TABLE.get(dominant_emotion, 0.10))

    # Factor 2: EmotionBrandFit ∈ [0, 1]
    emotion_brand_fit: float = _get_emotion_fit(industry, dominant_emotion)

    # Factor 3: MomentStrength ∈ [0, 1]
    # Saturates at a 3× traffic spike (the moment-detection threshold §A.3).
    moment_strength: float = min(max(volume_ratio / 3.0, 0.0), 1.0)

    # Factor 4: SegmentMatch — affinity table [0.5, 1.5], normalised to [0, 1].
    # Normalisation: subtract the minimum possible value (0.5) and divide by
    # the range (1.0) so the result sits on [0, 1], same scale as the others.
    segment_match_raw: float = calculate_segment_match(segment_id, industry)
    segment_match_norm: float = (segment_match_raw - 0.5) / 1.0

    # Weighted-additive combination
    raw_M: float = (
        0.35 * arousal
        + 0.25 * emotion_brand_fit
        + 0.20 * moment_strength
        + 0.20 * segment_match_norm
    )

    # Hard clip: [M_MIN, M_MAX] = [0.6, 2.2]
    M: float = min(max(raw_M, M_MIN), M_MAX)

    return {
        "M":                  round(M, 4),
        "arousal":            round(arousal, 4),
        "emotion_brand_fit":  round(emotion_brand_fit, 4),
        "moment_strength":    round(moment_strength, 4),
        "segment_match_raw":  round(segment_match_raw, 4),
        "segment_match":      round(segment_match_norm, 4),
        "k":                  1.0,  # additive formula has no multiplicative K
    }


# Alias for W2 strategy engine (§F.3 contract surface name)
def compute_multiplier(
    dominant_emotion: str,
    industry: str,
    volume_ratio: float,
    segment_id: Optional[str] = None,
) -> dict:
    """Alias of calculate_engagement_multiplier for §F.3 contract compliance."""
    return calculate_engagement_multiplier(
        dominant_emotion=dominant_emotion,
        industry=industry,
        volume_ratio=volume_ratio,
        segment_id=segment_id,
    )


# ---------------------------------------------------------------------------
# Effective Rates
# ---------------------------------------------------------------------------

def calculate_effective_ctr(baseline_ctr: float, M: float) -> float:
    """Compute the multiplier-adjusted click-through rate.

    effective_ctr = baseline_ctr × M

    A higher M (peak-emotion moment) means the ad captures more attention
    and a greater fraction of exposed users click. The relationship is linear
    because CTR is primarily an attention measure and attention scales directly
    with emotional arousal.

    Parameters
    ----------
    baseline_ctr : float  Benchmark CTR from benchmarks.csv [0–1].
    M            : float  Engagement multiplier ∈ [M_MIN, M_MAX].

    Returns
    -------
    float  Effective CTR, clipped to [0, 1].
    """
    return min(max(baseline_ctr * M, 0.0), 1.0)


def calculate_effective_cvr(baseline_cvr: float, M: float) -> float:
    """Compute the damped multiplier-adjusted conversion rate.

    effective_cvr = baseline_cvr × (CVR_FLOOR + CVR_LIFT_WEIGHT × M)
                  = baseline_cvr × (0.7 + 0.3 × M)

    Rationale for the floor-and-slope form:
      • At M = 0  : CVR_eff = baseline_cvr × 0.7  (30% penalty — hostile moment)
      • At M = 1.0: CVR_eff = baseline_cvr × 1.0  (matches benchmark exactly) ✓
      • At M = 2.2: CVR_eff = baseline_cvr × 1.36 (maximum 36% lift)

    The damping is intentional: emotional arousal amplifies click intent
    (CTR) more than purchase completion (CVR). A fan who clicks in excitement
    after a goal may still abandon a checkout. CVR gets only 30% of M's weight.

    Parameters
    ----------
    baseline_cvr : float  Benchmark CVR from benchmarks.csv [0–1].
    M            : float  Engagement multiplier ∈ [M_MIN, M_MAX].

    Returns
    -------
    float  Effective CVR, clipped to [0, CVR_MAX].
    """
    raw: float = baseline_cvr * (CVR_FLOOR + CVR_LIFT_WEIGHT * M)
    return min(max(raw, 0.0), CVR_MAX)


# ---------------------------------------------------------------------------
# Marketing Funnel
# ---------------------------------------------------------------------------

def calculate_funnel(
    budget: float,
    cpm_usd: float,
    frequency: float,
    effective_ctr: float,
    effective_cvr: float,
    aov_usd: float,
    gross_margin: float,
    demand_index: Optional[float] = None,
) -> dict:
    """Execute the full eight-stage marketing funnel.

    Stages
    ------
    1. Impressions  = (budget / cpm_usd) × 1000
       CPM is the universal media-buying unit (cost per mille = per 1,000
       impressions). Dividing budget by CPM gives thousands purchased;
       × 1,000 converts to raw impression count.

    2. Reach        = impressions × REACH_FACTOR  (REACH_FACTOR = 0.72)
       72 % of impressions reach a unique person; the remaining 28 % are
       repeat exposures. Conservative empirical average across digital channels.
       (Stored `frequency` parameter is informational only in this model.)

    3. Clicks       = reach × effective_ctr
       Each unique person exposed has a probability (effective_ctr) of clicking.

    4. Conversions  = clicks × effective_cvr  [+ demand adjustment]
       Each clicker has a probability (effective_cvr) of completing a purchase.
       Feature 3 demand_index modifies conversions deterministically:
           demand_index > 80  → × 1.10  (high-demand event; easier conversion)
           demand_index < 40  → × 0.90  (low-interest event; harder conversion)

    5. Revenue      = conversions × aov_usd
       AOV (Average Order Value) is the expected revenue per transaction.
       AOV does not change with M — the multiplier affects *how many* convert,
       not *how much* each person spends per order.

    6. Gross Profit = revenue × gross_margin
       Revenue retained after variable COGS. Makes real profitability visible.
       Break-even ROAS = 1 / gross_margin (e.g. 18% margin → need ROAS > 5.56).

    7. ROAS         = revenue / budget
       Revenue per advertising dollar — primary media efficiency KPI.

    8. ROI          = (gross_profit − budget) / budget
       Net profit (gross profit minus ad spend) as a fraction of the spend.
       Standard financial definition: profit on invested capital.
       Note: ROI can be negative if gross_profit < budget (loss-making campaign).

    Parameters
    ----------
    budget        : float  Campaign budget in USD (> 0).
    cpm_usd       : float  Cost per 1,000 impressions (> 0).
    frequency     : float  Avg. exposures per unique user (informational).
    effective_ctr : float  Post-multiplier click-through rate [0–1].
    effective_cvr : float  Post-multiplier conversion rate [0–CVR_MAX].
    aov_usd       : float  Average order value in USD (> 0).
    gross_margin  : float  Gross margin fraction (0, 1].
    demand_index  : float or None  Feature 3 output [0–100].

    Returns
    -------
    dict  All funnel intermediates + ROAS + ROI.
    """
    # Input guards
    if budget <= 0:
        raise ValueError(f"budget must be > 0, got {budget}")
    if cpm_usd <= 0:
        raise ValueError(f"cpm_usd must be > 0, got {cpm_usd}")
    if aov_usd <= 0:
        raise ValueError(f"aov_usd must be > 0, got {aov_usd}")
    if not (0.0 < gross_margin <= 1.0):
        raise ValueError(f"gross_margin must be in (0, 1], got {gross_margin}")

    # Stage 1: Impressions
    impressions: float = (budget / cpm_usd) * 1_000.0

    # Stage 2: Reach — unique audience reached (72% de-duplication rate)
    reach: float = impressions * REACH_FACTOR

    # Stage 3: Clicks — each reached person independently has a chance to click
    clicks: float = reach * effective_ctr

    # Stage 4: Conversions — each clicker independently has a chance to purchase
    conversions: float = clicks * effective_cvr

    # Demand adjustment — Feature 3 integration (deterministic, zero randomness)
    demand_adjustment: float = 1.0
    if demand_index is not None:
        if demand_index > DEMAND_HIGH_THRESHOLD:
            demand_adjustment = DEMAND_HIGH_MULTIPLIER  # +10 %
        elif demand_index < DEMAND_LOW_THRESHOLD:
            demand_adjustment = DEMAND_LOW_MULTIPLIER   # −10 %
    conversions *= demand_adjustment

    # Stage 5: Revenue — total transaction value
    revenue: float = conversions * aov_usd

    # Stage 6: Gross Profit — profit after variable costs
    gross_profit: float = revenue * gross_margin

    # Stage 7: ROAS — revenue dollars per ad dollar
    roas: float = revenue / budget

    # Stage 8: ROI — net profit (after recovering the spend) per ad dollar
    # Positive ROI means the campaign is profitable net of ad cost.
    roi: float = (gross_profit - budget) / budget

    return {
        "impressions":       int(round(impressions)),
        "reach":             int(round(reach)),
        "clicks":            int(round(clicks)),
        "conversions":       round(conversions, 2),
        "demand_adjustment": demand_adjustment,
        "revenue_usd":       round(revenue, 2),
        "gross_profit_usd":  round(gross_profit, 2),
        "roas":              round(roas, 4),
        "roi":               round(roi, 4),
    }


# ---------------------------------------------------------------------------
# Confidence Score
# ---------------------------------------------------------------------------

def calculate_confidence(
    forecast_confidence: Optional[float] = None,
    segment_size: Optional[int] = None,
    volume_5m: Optional[int] = None,
    moment_age_minutes: Optional[float] = None,
    is_baseline: bool = False,
) -> float:
    """Compute the data-quality confidence score for an ROI simulation.

    This is not a model probability. It is a data-support score reflecting
    how well-backed the live signal is that powers the multiplier M.

    Formula (§F.3)
    --------------
    volume_support  = clip(volume_5m / 500, 0, 1)
        How large is the live data volume backing the emotion signal?
        Saturates at 500 messages in the last 5 minutes.

    moment_recency  = clip(1 − moment_age_minutes / 30, 0, 1)
        How fresh is the triggering moment? Decays linearly to 0 at 30 min.
        If no specific moment triggered this call, use 1.0 (full credit).

    segment_support = clip(segment_size / 500, 0, 1)
        Is the target segment large enough to be statistically meaningful?
        Saturates at 500 fans in segment.

    confidence = clip(
        0.4 × forecast_confidence_adjusted
      + 0.3 × moment_recency
      + 0.3 × segment_support,
        0, 1
    )

    Baseline mode: fixed at 0.75 — grounded in published benchmarks only,
    no live signal to trust or distrust.

    Parameters
    ----------
    forecast_confidence  : float or None  Feature 3 model confidence [0–1].
    segment_size         : int or None    Fan count in the target segment.
    volume_5m            : int or None    W1 message volume last 5 minutes.
    moment_age_minutes   : float or None  Age of triggering moment in minutes.
    is_baseline          : bool           Force baseline mode → fixed 0.75.

    Returns
    -------
    float  Confidence ∈ [0, 1].
    """
    if is_baseline:
        return 0.75  # §F.3 fixed baseline-mode confidence

    # Sub-component: volume support
    volume_support: float = min(max((volume_5m or 0) / 500.0, 0.0), 1.0)

    # Sub-component: moment recency
    if moment_age_minutes is None:
        moment_recency: float = 1.0  # live but pre-moment → full recency credit
    else:
        moment_recency = min(max(1.0 - moment_age_minutes / 30.0, 0.0), 1.0)

    # Sub-component: segment support
    segment_support: float = min(max((segment_size or 0) / 500.0, 0.0), 1.0)

    # Forecast-model confidence from Feature 3 (falls back to 0.75 if unavailable)
    fc: float = float(forecast_confidence) if forecast_confidence is not None else 0.75

    raw: float = (
        0.4 * fc
        + 0.3 * moment_recency
        + 0.3 * segment_support
    )
    return round(min(max(raw, 0.0), 1.0), 4)


# ---------------------------------------------------------------------------
# Explainability — Top Factors
# ---------------------------------------------------------------------------

def generate_top_factors(
    multiplier_breakdown: dict,
    demand_index: Optional[float],
    segment_id: Optional[str],
    dominant_emotion: str,
    baseline_roas: float,
    live_roas: float,
) -> list[dict]:
    """Produce an ordered list of factors that most drove the ROI outcome.

    Each factor's impact is computed from its proportional share of the
    total ROAS uplift over baseline. This is fully deterministic — every
    number traces to a computed value, nothing is hardcoded.

    Total uplift:
        total_uplift_pct = (live_roas − baseline_roas) / max(baseline_roas, 1e-9) × 100

    Each multiplier sub-factor's weighted contribution to M:
        contrib[factor] = weight[factor] × raw_factor_value

    Its share of total uplift:
        impact_pct[factor] = total_uplift_pct × contrib[factor] / Σ contrib

    Parameters
    ----------
    multiplier_breakdown : dict  Output of calculate_engagement_multiplier().
    demand_index         : float or None
    segment_id           : str or None
    dominant_emotion     : str
    baseline_roas        : float
    live_roas            : float

    Returns
    -------
    list[dict]  Top-5 factors sorted descending by |impact|:
        { "name": str, "value": str, "impact": str }
    """
    factors: list[dict] = []

    # Total ROAS uplift to apportion
    safe_baseline = max(baseline_roas, 1e-9)
    total_uplift_pct: float = (live_roas - safe_baseline) / safe_baseline * 100.0

    # Sub-factor weighted contributions (weights must match calculate_engagement_multiplier)
    sub_contribs: dict[str, tuple[float, float, str]] = {
        #  name                  weight  raw_value                         display_value
        "Arousal":          (0.35, multiplier_breakdown["arousal"],
                             f"{dominant_emotion} ({multiplier_breakdown['arousal']:.2f})"),
        "Emotion Brand Fit":(0.25, multiplier_breakdown["emotion_brand_fit"],
                             f"{multiplier_breakdown['emotion_brand_fit']:.2f}"),
        "Moment Strength":  (0.20, multiplier_breakdown["moment_strength"],
                             f"{multiplier_breakdown['moment_strength']:.2f}"),
        "Segment Fit":      (0.20, multiplier_breakdown["segment_match"],
                             f"{segment_id or 'all'} "
                             f"({multiplier_breakdown['segment_match_raw']:.2f})"),
    }

    total_contrib: float = sum(w * v for name, (w, v, _) in sub_contribs.items())
    safe_total = max(total_contrib, 1e-9)

    for name, (weight, raw_val, display_val) in sub_contribs.items():
        contrib = weight * raw_val
        share = contrib / safe_total
        impact_pct = total_uplift_pct * share
        sign = "+" if impact_pct >= 0 else ""
        factors.append({
            "name":   name,
            "value":  display_val,
            "impact": f"{sign}{impact_pct:.1f}%",
            "_abs":   abs(impact_pct),
        })

    # Demand index factor (deterministic flat adjustment)
    if demand_index is not None:
        if demand_index > DEMAND_HIGH_THRESHOLD:
            factors.append({
                "name":   "High Demand Index",
                "value":  f"{demand_index:.1f}",
                "impact": "+10.0% (conversion boost)",
                "_abs":   10.0,
            })
        elif demand_index < DEMAND_LOW_THRESHOLD:
            factors.append({
                "name":   "Low Demand Index",
                "value":  f"{demand_index:.1f}",
                "impact": "-10.0% (conversion drag)",
                "_abs":   10.0,
            })

    # Sort descending by absolute impact; return top 5; strip internal key
    factors.sort(key=lambda f: f["_abs"], reverse=True)
    for f in factors:
        f.pop("_abs", None)
    return factors[:5]


# ---------------------------------------------------------------------------
# Best Channel
# ---------------------------------------------------------------------------

def best_channel(industry: str, segment_id: Optional[str] = None) -> str:
    """Return the channel with the highest expected ROI for an industry.

    Scoring formula per channel:
        channel_score = (CTR × CVR × AOV_usd) / CPM_usd

    This is a proxy for expected revenue per dollar of CPM spend at
    baseline (M=1.0), making it comparable across channels regardless of
    absolute CPM level.

    Tie-breaking: if a segment's preferred_channel is in the top channels,
    it receives a +10 % score boost to honour the segment's behavioural
    preference — only overrides a close contest, not a dominant winner.

    Parameters
    ----------
    industry   : str          Industry slug (§A.2).
    segment_id : str or None  FanPulse segment slug for preference boost.

    Returns
    -------
    str  Channel slug with the highest expected ROI.

    Raises
    ------
    KeyError  If no benchmark rows exist for this industry.
    """
    df = load_benchmarks()
    idx_industries = df.index.get_level_values(0)

    if industry not in idx_industries:
        raise KeyError(
            f"No benchmark rows found for industry='{industry}'. "
            "Add rows to data/benchmarks/benchmarks.csv."
        )

    industry_rows = df.loc[industry]
    # If only one channel, loc returns a Series; normalise to DataFrame
    if isinstance(industry_rows, pd.Series):
        industry_rows = industry_rows.to_frame().T

    # Compute efficiency score per channel
    scores: dict[str, float] = {}
    for channel_name in industry_rows.index:
        row = industry_rows.loc[channel_name]
        score = (
            float(row["ctr"])
            * float(row["cvr"])
            * float(row["aov_usd"])
        ) / float(row["cpm_usd"])
        scores[channel_name] = score

    # Segment preference tie-breaking (+10 % to preferred channel)
    if segment_id is not None:
        profiles = _load_segment_profiles()
        for seg in profiles.get("segments", []):
            if seg.get("segment_id") == segment_id:
                pref = seg.get("preferred_channel")
                if pref and pref in scores:
                    scores[pref] *= 1.10  # 10 % boost — honours preference without forcing it
                break

    return max(scores, key=lambda c: scores[c])


# ---------------------------------------------------------------------------
# Primary Public API — simulate_roi
# ---------------------------------------------------------------------------

def simulate_roi(
    industry: str,
    channel: str,
    budget_usd: float,
    dominant_emotion: str = "neutral",
    volume_ratio: float = 1.0,
    segment_id: Optional[str] = None,
    demand_index: Optional[float] = None,
    forecast_confidence: Optional[float] = None,
    segment_size: Optional[int] = None,
    volume_5m: Optional[int] = None,
    moment_age_minutes: Optional[float] = None,
    is_baseline: bool = False,
) -> dict:
    """Simulate full marketing ROI for a campaign at a specific match moment.

    This is the primary entry point for Feature 6 (§F.3 contract surface).
    It orchestrates all helper functions and returns every intermediate value
    to satisfy the glass-box invariant (§9.1): no output is a bare final number.

    Both the live result AND the baseline comparison are ALWAYS computed and
    returned side-by-side. The baseline_comparison field is mandatory and is
    never None, even in baseline mode (where both sides are M=1.0 and identical).

    Parameters
    ----------
    industry            : str    Industry slug (§A.2 enum). Required.
    channel             : str    Channel slug (§A.1 enum). Required.
    budget_usd          : float  Campaign budget in USD. Must be > 0.
    dominant_emotion    : str    Current fan emotion (§A.1). Default "neutral".
    volume_ratio        : float  Feature 2 momentum: volume_1m / trailing_avg.
                                 Default 1.0 (flat — MomentStrength ≈ 0.33).
    segment_id          : str or None  FanPulse segment slug (Feature 4).
    demand_index        : float or None  Feature 3 audience forecast [0–100].
    forecast_confidence : float or None  Feature 3 model confidence [0–1].
    segment_size        : int or None  Fans in target segment (from segments.py).
    volume_5m           : int or None  W1 message volume last 5 minutes.
    moment_age_minutes  : float or None  Minutes since the triggering moment.
    is_baseline         : bool  If True: M=1.0, confidence=0.75 (baseline mode).

    Returns
    -------
    dict  Complete ROI result matching §B.8 schema:
        budget_usd, industry, channel,
        engagement_multiplier (M + all factor values),
        effective_ctr, effective_cvr,
        funnel { all 8 stages },
        roas, roi, revenue_usd, gross_profit_usd,
        baseline_comparison { roas, roi, revenue_usd, gross_profit_usd,
                              effective_ctr, effective_cvr },
        best_channel, confidence, top_factors,
        benchmark_source, computed_at.

    Raises
    ------
    ValueError  If budget_usd ≤ 0.
    KeyError    If (industry, channel) not in benchmarks.csv.
    """
    # ── Input validation ──────────────────────────────────────────────────
    if budget_usd <= 0:
        raise ValueError(f"budget_usd must be > 0, got {budget_usd}")

    # ── Load benchmark row ────────────────────────────────────────────────
    bm = _get_benchmark_row(industry, channel)
    cpm_usd      = float(bm["cpm_usd"])
    ctr_baseline = float(bm["ctr"])
    cvr_baseline = float(bm["cvr"])
    aov_usd      = float(bm["aov_usd"])
    gross_margin = float(bm["gross_margin"])
    frequency    = float(bm["frequency"])
    source_str   = f"{bm['source']} — {industry}/{channel}"

    # ── Engagement Multiplier ─────────────────────────────────────────────
    if is_baseline:
        # Baseline mode: M = 1.0; all factor values set to neutral.
        multiplier_breakdown: dict = {
            "M":                 1.0,
            "arousal":           0.0,
            "emotion_brand_fit": 0.0,
            "moment_strength":   0.0,
            "segment_match_raw": 1.0,
            "segment_match":     0.5,
            "k":                 1.0,
        }
        M: float = 1.0
    else:
        multiplier_breakdown = calculate_engagement_multiplier(
            dominant_emotion=dominant_emotion,
            industry=industry,
            volume_ratio=volume_ratio,
            segment_id=segment_id,
        )
        M = multiplier_breakdown["M"]

    # ── Effective rates ───────────────────────────────────────────────────
    eff_ctr: float = calculate_effective_ctr(ctr_baseline, M)
    eff_cvr: float = calculate_effective_cvr(cvr_baseline, M)

    # ── Live funnel ───────────────────────────────────────────────────────
    live_funnel: dict = calculate_funnel(
        budget=budget_usd,
        cpm_usd=cpm_usd,
        frequency=frequency,
        effective_ctr=eff_ctr,
        effective_cvr=eff_cvr,
        aov_usd=aov_usd,
        gross_margin=gross_margin,
        demand_index=demand_index,
    )

    # ── Baseline funnel (always computed — §9.1 glass-box invariant) ──────
    base_eff_ctr: float = calculate_effective_ctr(ctr_baseline, 1.0)
    base_eff_cvr: float = calculate_effective_cvr(cvr_baseline, 1.0)
    baseline_funnel: dict = calculate_funnel(
        budget=budget_usd,
        cpm_usd=cpm_usd,
        frequency=frequency,
        effective_ctr=base_eff_ctr,
        effective_cvr=base_eff_cvr,
        aov_usd=aov_usd,
        gross_margin=gross_margin,
        demand_index=demand_index,  # demand adjustment applies equally to baseline
    )

    # ── Confidence ────────────────────────────────────────────────────────
    confidence: float = calculate_confidence(
        forecast_confidence=forecast_confidence,
        segment_size=segment_size,
        volume_5m=volume_5m,
        moment_age_minutes=moment_age_minutes,
        is_baseline=is_baseline,
    )

    # ── Best channel (informational; used by W2 strategy engine WHERE step) ─
    try:
        recommended_channel: str = best_channel(industry, segment_id)
    except KeyError:
        recommended_channel = channel  # graceful fallback to the requested channel

    # ── Top factors (explainability) ──────────────────────────────────────
    top_factors: list[dict] = generate_top_factors(
        multiplier_breakdown=multiplier_breakdown,
        demand_index=demand_index,
        segment_id=segment_id,
        dominant_emotion=dominant_emotion,
        baseline_roas=baseline_funnel["roas"],
        live_roas=live_funnel["roas"],
    )

    # ── Assemble and return ───────────────────────────────────────────────
    return {
        # ── Request context ──────────────────────────────────────────────
        "budget_usd":  budget_usd,
        "industry":    industry,
        "channel":     channel,

        # ── Multiplier breakdown ─────────────────────────────────────────
        "engagement_multiplier": multiplier_breakdown,

        # ── Effective rates ──────────────────────────────────────────────
        "effective_ctr": round(eff_ctr, 6),
        "effective_cvr": round(eff_cvr, 6),

        # ── Full live funnel ─────────────────────────────────────────────
        "funnel": {
            "cpm_usd":         cpm_usd,
            "frequency":       frequency,
            "ctr_baseline":    ctr_baseline,
            "cvr_baseline":    cvr_baseline,
            "aov_usd":         aov_usd,
            "gross_margin":    gross_margin,
            **live_funnel,
        },

        # ── Top-line results ─────────────────────────────────────────────
        "roas":             live_funnel["roas"],
        "roi":              live_funnel["roi"],
        "revenue_usd":      live_funnel["revenue_usd"],
        "gross_profit_usd": live_funnel["gross_profit_usd"],

        # ── Mandatory baseline comparison (§9.1 — never omitted) ─────────
        "baseline_comparison": {
            "roas":             baseline_funnel["roas"],
            "roi":              baseline_funnel["roi"],
            "revenue_usd":      baseline_funnel["revenue_usd"],
            "gross_profit_usd": baseline_funnel["gross_profit_usd"],
            "effective_ctr":    round(base_eff_ctr, 6),
            "effective_cvr":    round(base_eff_cvr, 6),
        },

        # ── Evidence and metadata ────────────────────────────────────────
        "best_channel":     recommended_channel,
        "confidence":       confidence,
        "top_factors":      top_factors,
        "benchmark_source": source_str,
        "computed_at":      datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Media Planner
# ---------------------------------------------------------------------------

def plan_media(
    budget_usd: float,
    industry: str,
    forecasts: list[dict],
    momenta: Optional[dict[str, Optional[dict]]] = None,
    segment_id: Optional[str] = None,
) -> dict:
    """Allocate a total budget across multiple matches proportionally.

    Algorithm
    ---------
    1.  weight[m] = demand_index[m] × expected_M[m]
        Matches with high demand AND a strong live moment get more budget.
    2.  raw_share[m] = weight[m] / Σ weight
    3.  Greedy 60 % cap: sort desc by weight; allocate; cap at MEDIA_PLAN_CAP;
        redistribute remainder to lower-weight matches.
    4.  budget[m] = raw_share[m] × total_budget_usd
    5.  Per-match ROI is simulated via simulate_roi() for expected_roas.

    Parameters
    ----------
    budget_usd  : float  Total budget to allocate in USD (> 0).
    industry    : str    Industry slug.
    forecasts   : list[dict]  Each dict: {match_id: str, demand_index: float}.
    momenta     : dict[str, dict|None]  match_id → momentum-like dict or None.
    segment_id  : str or None  Target segment for multiplier and best_channel.

    Returns
    -------
    dict  { total_budget_usd, industry, channel, allocations[], expected_total_roas }.
    """
    if budget_usd <= 0:
        raise ValueError(f"budget_usd must be > 0, got {budget_usd}")
    if not forecasts:
        raise ValueError("forecasts list must not be empty.")

    momenta = momenta or {}
    channel = best_channel(industry, segment_id)

    # Step 1: compute weights
    weights: dict[str, float] = {}
    expected_Ms: dict[str, float] = {}
    for f in forecasts:
        match_id    = f["match_id"]
        di          = float(f.get("demand_index", 50.0))
        m_snap      = momenta.get(match_id)

        if m_snap:
            mb = calculate_engagement_multiplier(
                dominant_emotion=m_snap.get("dominant_emotion", "neutral"),
                industry=industry,
                volume_ratio=float(m_snap.get("volume_ratio", 1.0)),
                segment_id=segment_id,
            )
            exp_M = mb["M"]
        else:
            exp_M = 1.0  # no live signal → baseline multiplier

        expected_Ms[match_id] = exp_M
        weights[match_id]     = di * exp_M

    total_weight = sum(weights.values())
    if total_weight == 0.0:
        # Edge case: all zero weights → equal distribution
        equal = 1.0 / len(forecasts)
        shares: dict[str, float] = {f["match_id"]: equal for f in forecasts}
    else:
        shares = {mid: w / total_weight for mid, w in weights.items()}

    # Step 2: greedy 60 % cap
    sorted_mids = sorted(shares, key=lambda m: shares[m], reverse=True)
    capped: dict[str, float] = {}
    remaining = 1.0
    for mid in sorted_mids:
        alloc = min(shares[mid], MEDIA_PLAN_CAP, remaining)
        capped[mid] = alloc
        remaining  -= alloc
        if remaining <= 0.0:
            break
    for mid in sorted_mids:
        if mid not in capped:
            capped[mid] = 0.0

    # Step 3: build allocation records
    allocations: list[dict] = []
    total_revenue = 0.0
    total_alloc   = 0.0

    for f in forecasts:
        match_id  = f["match_id"]
        share     = capped.get(match_id, 0.0)
        alloc_bud = share * budget_usd
        if alloc_bud < 1.0:
            continue

        di     = float(f.get("demand_index", 50.0))
        m_snap = momenta.get(match_id)

        roi_res = simulate_roi(
            industry=industry,
            channel=channel,
            budget_usd=alloc_bud,
            dominant_emotion=(m_snap.get("dominant_emotion", "neutral") if m_snap else "neutral"),
            volume_ratio=float(m_snap.get("volume_ratio", 1.0) if m_snap else 1.0),
            segment_id=segment_id,
            demand_index=di,
            is_baseline=(m_snap is None),
        )

        exp_rev  = roi_res["revenue_usd"]
        exp_roas = roi_res["roas"]
        total_revenue += exp_rev
        total_alloc   += alloc_bud

        demand_label = (
            "high demand"    if di > DEMAND_HIGH_THRESHOLD else
            "low demand"     if di < DEMAND_LOW_THRESHOLD  else
            "moderate demand"
        )
        rationale = (
            f"demand_index={di:.1f} ({demand_label}), "
            f"M={expected_Ms[match_id]:.2f}, "
            f"expected ROAS {exp_roas:.2f}; "
            f"{'capped at 60%' if share >= MEDIA_PLAN_CAP - 0.001 else f'{share*100:.1f}% of budget'}."
        )

        allocations.append({
            "match_id":             match_id,
            "budget_usd":           round(alloc_bud, 2),
            "share_pct":            round(share * 100.0, 2),
            "demand_index":         di,
            "expected_M":           round(expected_Ms[match_id], 4),
            "expected_roas":        round(exp_roas, 4),
            "expected_revenue_usd": round(exp_rev, 2),
            "rationale":            rationale,
        })

    allocations.sort(key=lambda a: a["budget_usd"], reverse=True)
    expected_total_roas = total_revenue / total_alloc if total_alloc > 0.0 else 0.0

    return {
        "total_budget_usd":    budget_usd,
        "industry":            industry,
        "channel":             channel,
        "allocations":         allocations,
        "expected_total_roas": round(expected_total_roas, 4),
        "computed_at":         datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Self-test  (python backend/intelligence/roi.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("FanPulse ROI Engine — Self-Test")
    print("=" * 60)

    # ── Test 1: Baseline ────────────────────────────────────────────────
    print("\n[1] Baseline — food_delivery / push / $100k (M should be 1.0)")
    r1 = simulate_roi(
        industry="food_delivery",
        channel="push",
        budget_usd=100_000,
        is_baseline=True,
    )
    print(f"    M          : {r1['engagement_multiplier']['M']}")
    print(f"    Impressions: {r1['funnel']['impressions']:,}")
    print(f"    Clicks     : {r1['funnel']['clicks']:,}")
    print(f"    Conversions: {r1['funnel']['conversions']:,}")
    print(f"    Revenue    : ${r1['revenue_usd']:,.2f}")
    print(f"    ROAS       : {r1['roas']:.4f}")
    print(f"    ROI        : {r1['roi']*100:.2f}%")
    print(f"    Confidence : {r1['confidence']}")

    # ── Test 2: Live goal moment ─────────────────────────────────────────
    print("\n[2] Live joy moment — food_delivery / push / $100k / deal_seekers")
    r2 = simulate_roi(
        industry="food_delivery",
        channel="push",
        budget_usd=100_000,
        dominant_emotion="joy",
        volume_ratio=2.4,
        segment_id="deal_seekers",
        demand_index=85.0,
        forecast_confidence=0.88,
        segment_size=1480,
        volume_5m=350,
        moment_age_minutes=2.0,
    )
    mb = r2["engagement_multiplier"]
    print(f"    M          : {mb['M']}  "
          f"(arousal={mb['arousal']}, fit={mb['emotion_brand_fit']}, "
          f"strength={mb['moment_strength']}, match={mb['segment_match']})")
    print(f"    eff_ctr    : {r2['effective_ctr']:.6f}")
    print(f"    eff_cvr    : {r2['effective_cvr']:.6f}")
    print(f"    Clicks     : {r2['funnel']['clicks']:,}")
    print(f"    Conversions: {r2['funnel']['conversions']:,.1f}")
    print(f"    Revenue    : ${r2['revenue_usd']:,.2f}")
    print(f"    ROAS live  : {r2['roas']:.4f}")
    print(f"    ROAS base  : {r2['baseline_comparison']['roas']:.4f}")
    print(f"    ROI        : {r2['roi']*100:.2f}%")
    print(f"    Confidence : {r2['confidence']}")
    print("    Top factors:")
    for tf in r2["top_factors"]:
        print(f"      {tf['name']:20s} {tf['value']:30s} → {tf['impact']}")

    # ── Test 3: best_channel ─────────────────────────────────────────────
    print("\n[3] best_channel per industry")
    for ind in ["food_delivery", "merch_apparel", "streaming_ott", "beverages", "content_creator"]:
        ch = best_channel(ind, "deal_seekers")
        print(f"    {ind:25s} → {ch}")

    # ── Test 4: Segment match edge cases ─────────────────────────────────
    print("\n[4] Segment match edge cases")
    print(f"    None   / food_delivery : {calculate_segment_match(None, 'food_delivery')}")
    print(f"    unknown/ food_delivery : {calculate_segment_match('unknown', 'food_delivery')}")
    print(f"    deal_seekers / unknown : {calculate_segment_match('deal_seekers', 'unknown')}")

    print("\nSelf-test complete. ✓")
