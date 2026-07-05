from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

# A.1 Enums
class Sentiment(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"

class Emotion(str, Enum):
    joy = "joy"
    anger = "anger"
    surprise = "surprise"
    fear = "fear"
    disgust = "disgust"
    sadness = "sadness"
    neutral = "neutral"

class Source(str, Enum):
    reddit = "reddit"
    youtube = "youtube"
    news = "news"
    replay = "replay"

class Channel(str, Enum):
    push = "push"
    instagram = "instagram"
    youtube = "youtube"
    email = "email"

class SegmentId(str, Enum):
    superfans = "superfans"
    traveling_ultras = "traveling_ultras"
    casual_streamers = "casual_streamers"
    deal_seekers = "deal_seekers"
    lapsed_fans = "lapsed_fans"

class EventTag(str, Enum):
    goal = "goal"
    red_card = "red_card"
    var_controversy = "var_controversy"
    full_time = "full_time"
    kickoff = "kickoff"
    surge_other = "surge_other"

class Archetype(str, Enum):
    celebration_flash_offer = "celebration_flash_offer"
    consolation_offer = "consolation_offer"
    commemorative_drop = "commemorative_drop"
    tune_in_push = "tune_in_push"
    fan_trip_promo = "fan_trip_promo"
    watch_it_here = "watch_it_here"
    install_play = "install_play"
    flash_sale = "flash_sale"
    brand_awareness = "brand_awareness"
    content_idea = "content_idea"

class Industry(str, Enum):
    food_delivery = "food_delivery"
    merch_apparel = "merch_apparel"
    beverages = "beverages"
    streaming_ott = "streaming_ott"
    content_creator = "content_creator"
    sportswear_fashion = "sportswear_fashion"
    betting_igaming = "betting_igaming"
    gaming_esports = "gaming_esports"
    retail_ecommerce = "retail_ecommerce"
    telecom = "telecom"
    consumer_electronics = "consumer_electronics"
    fintech = "fintech"
    travel_hospitality = "travel_hospitality"
    pubs_venues = "pubs_venues"
    automotive = "automotive"

# A.3 Constants
RANDOM_SEED = 42

AROUSAL = {
    "joy": 0.90, "surprise": 0.85, "anger": 0.80, "fear": 0.60,
    "disgust": 0.50, "sadness": 0.30, "neutral": 0.10
}

MULTIPLIER_K = 2.0
MULTIPLIER_MIN, MULTIPLIER_MAX = 0.7, 2.5
CVR_LIFT_DAMPING = 0.5

MOMENT_VOLUME_RATIO = 3.0
MOMENT_SENTIMENT_DELTA_PP = 10.0
MOMENT_COOLDOWN_SECONDS = 120

MOMENTUM_MIN_MESSAGES_5M = 10
GEMINI_DEBOUNCE_SECONDS = 12

# A.4 Core pydantic models
class RawMessageIn(BaseModel):
    external_id: str
    match_id: str
    source: Source
    author: Optional[str] = None
    text: str
    country: Optional[str] = None
    created_at: datetime

class ClassifiedMessage(BaseModel):
    message_id: int
    match_id: str
    source: Source
    text: str
    author: Optional[str] = None
    country: Optional[str] = None
    sentiment: Sentiment
    sentiment_score: float
    emotion: Emotion
    emotion_score: float
    topics: List[str]
    created_at: datetime

class MomentumSnapshot(BaseModel):
    match_id: str
    volume_1m: int
    volume_5m: int
    volume_ratio: float
    dominant_emotion: Emotion
    arousal: float
    positive_pct: float
    sentiment_delta_pp: float
    top_topics: List[str]
    top_countries: List[str]
    computed_at: datetime

class MomentEvent(BaseModel):
    moment_id: str
    match_id: str
    event_tag: EventTag
    detected_at: datetime
    momentum: MomentumSnapshot
    description: str

class MatchFeatures(BaseModel):
    match_id: str
    stage: int
    home_team: str
    away_team: str
    home_rank: int
    away_rank: int
    rank_gap: int
    rivalry_flag: bool
    host_involved: bool
    city_population_m: float
    venue_capacity: int
    day_of_week: int
    kickoff_hour_local: int
    buzz_index: float

# B. Response Models
class Match(BaseModel):
    match_id: str
    home_team: str
    away_team: str
    kickoff_time: str
    stage: int
    venue_capacity: int
    city: str
    status: str
    demand_index: Optional[float] = None
    sellout_probability: Optional[float] = None

class MatchListResponse(BaseModel):
    matches: List[Match]

class KpiSnapshot(BaseModel):
    match_id: str
    total_mentions: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    top_emotion: Emotion
    excitement_score: float
    most_active_region: str
    mentions_per_min: int
    computed_at: str

class TimelinePoint(BaseModel):
    ts: str
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    mentions: int
    top_emotion: Emotion
    event_tag: Optional[EventTag] = None

class TimelineResponse(BaseModel):
    match_id: str
    points: List[TimelinePoint]

class CountryHeatmap(BaseModel):
    country_code: str
    avg_sentiment: float
    dominant_emotion: Emotion
    mentions: int

class HeatmapPayload(BaseModel):
    match_id: str
    computed_at: str
    countries: List[CountryHeatmap]

class TopicItem(BaseModel):
    label: str
    mentions: int
    trend: str

class TopicsResponse(BaseModel):
    topics: List[TopicItem]

class FeedResponse(BaseModel):
    messages: List[ClassifiedMessage]

class MomentsResponse(BaseModel):
    moments: List[MomentEvent]

class FeatureImportance(BaseModel):
    feature: str
    importance: float

class AudienceForecast(BaseModel):
    match_id: str
    demand_index: float
    predicted_attendance_pct: float
    sellout_probability: float
    feature_importance: List[FeatureImportance]
    is_reforecast: bool
    baseline_demand_index: Optional[float] = None
    delta_vs_baseline_pct: Optional[float] = None
    trigger_description: Optional[str] = None
    model_mae: float
    computed_at: str

class CopyVariant(BaseModel):
    headline: str
    body: str
    cta: str

class Copy(BaseModel):
    headline: str
    body: str
    cta: str
    hashtags: List[str]
    variant_b: CopyVariant

class ROIResultFunnel(BaseModel):
    cpm_usd: float
    frequency: float
    impressions: int
    reach: int
    ctr_baseline: float
    ctr_effective: float
    clicks: int
    cvr_baseline: float
    cvr_effective: float
    conversions: int
    aov_usd: float
    revenue_usd: float

class MultiplierBreakdown(BaseModel):
    M: float
    arousal: float
    emotion_brand_fit: float
    moment_strength: float
    segment_match: float
    k: float

class BaselineComparison(BaseModel):
    roas: float
    roi_pct: float
    revenue_usd: float

class ROIResult(BaseModel):
    industry: Industry
    channel: Channel
    budget_usd: float
    multiplier: MultiplierBreakdown
    funnel: ROIResultFunnel
    roas: float
    roi_pct: float
    baseline_comparison: BaselineComparison
    benchmark_source: str
    confidence: float
    computed_at: str

class Segment(BaseModel):
    segment_id: SegmentId
    display_name: str
    size: int
    share_pct: float
    avg_engagement_score: float
    avg_annual_value_usd: float
    top_countries: List[str]
    preferred_channel: Channel
    churn_risk_pct: float
    defining_traits: List[str]
    activity_share_pct: float

class CampaignBrief(BaseModel):
    match_id: str
    industry: Industry
    archetype: Archetype
    target_segment: SegmentId
    channel: Channel
    window_minutes: int
    moment: Optional[MomentEvent] = None
    emotion: Emotion
    top_topics: List[str]
    top_countries: List[str]
    roi: ROIResult
    segment: Segment
    tone_notes: str

class CampaignCard(BaseModel):
    campaign_id: str
    match_id: str
    industry: Industry
    archetype: Archetype
    target_segment: SegmentId
    channel: Channel
    window_minutes: int
    window_ends_at: str
    status: str
    trigger: str
    moment_id: Optional[str] = None
    copy_content: Copy = Field(alias="copy")
    roi: ROIResult
    evidence: Dict[str, Any]
    confidence: float
    llm_fallback: bool
    created_at: str

class CampaignsResponse(BaseModel):
    campaigns: List[CampaignCard]

class ContentIdeaDetail(BaseModel):
    format: str
    hook: str
    concept: str
    hashtags: List[str]
    post_within_minutes: int

class ContentIdeaCard(BaseModel):
    content_id: str
    match_id: str
    platform: str
    archetype: str
    idea: ContentIdeaDetail
    evidence: Dict[str, str]
    confidence: float
    llm_fallback: bool
    created_at: str

class Segment(BaseModel):
    segment_id: SegmentId
    display_name: str
    size: int
    share_pct: float
    avg_engagement_score: float
    avg_annual_value_usd: float
    top_countries: List[str]
    preferred_channel: Channel
    churn_risk_pct: float
    defining_traits: List[str]
    activity_share_pct: float

class SegmentReport(BaseModel):
    segments: List[Segment]
    silhouette_score: float
    n_fans: int

class NextBestAction(BaseModel):
    segment_id: SegmentId
    industry: Industry
    channel: Channel
    archetype: Archetype
    timing_rule: str
    expected_ctr: float
    rationale: str

class MediaAllocation(BaseModel):
    match_id: str
    budget_usd: float
    share_pct: float
    demand_index: float
    expected_roas: float
    expected_revenue_usd: float
    rationale: str

class MediaPlan(BaseModel):
    total_budget_usd: float
    industry: Industry
    allocations: List[MediaAllocation]
    expected_total_roas: float

class BenchmarkNotFound(Exception):
    pass
